import json
import os
import hmac
import hashlib

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import WhatsappConversation, WhatsappMessage
from .whatsapp_client import send_whatsapp_text
from .ai_router import generate_reply


def _validate_signature(request) -> bool:
    """Validate X-Hub-Signature-256 when WHATSAPP_APP_SECRET is set.

    Meta sends: X-Hub-Signature-256: sha256=<hex>
    """

    app_secret = os.getenv("WHATSAPP_APP_SECRET", "").strip()
    if not app_secret:
        return True

    header = request.headers.get("X-Hub-Signature-256") or request.META.get("HTTP_X_HUB_SIGNATURE_256")
    if not header or not header.startswith("sha256="):
        return False

    expected = header.split("=", 1)[1]
    raw = request.body or b""
    digest = hmac.new(app_secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """WhatsApp Cloud API webhook.

    GET: verification challenge
    POST: message notifications
    """

    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        expected = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()

        if mode == "subscribe" and expected and token == expected and challenge:
            return HttpResponse(challenge)
        return HttpResponse("Forbidden", status=403)

    # POST
    if not _validate_signature(request):
        return HttpResponse("Invalid signature", status=403)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return HttpResponse("Bad Request", status=400)

    # WhatsApp Cloud payload shape:
    # entry[].changes[].value.messages[]
    entries = payload.get("entry") or []
    for entry in entries:
        for change in (entry.get("changes") or []):
            value = change.get("value") or {}
            contacts = value.get("contacts") or []
            messages = value.get("messages") or []

            display_name = ""
            wa_id = ""
            if contacts:
                display_name = (contacts[0].get("profile") or {}).get("name") or ""
                wa_id = contacts[0].get("wa_id") or ""

            for msg in messages:
                from_id = msg.get("from") or wa_id
                if not from_id:
                    continue

                msg_type = msg.get("type")
                text = ""
                if msg_type == "text":
                    text = ((msg.get("text") or {}).get("body") or "").strip()
                elif msg_type == "button":
                    text = ((msg.get("button") or {}).get("text") or "").strip()
                else:
                    # ignore non-text for MVP
                    continue

                if not text:
                    continue

                conv, _ = WhatsappConversation.objects.get_or_create(
                    wa_id=from_id,
                    defaults={"display_name": display_name},
                )
                if display_name and conv.display_name != display_name:
                    conv.display_name = display_name
                    conv.save(update_fields=["display_name"])

                WhatsappMessage.objects.create(conversation=conv, role="user", content=text)

                reply = generate_reply(conversation=conv, user_text=text, request=request)
                if reply:
                    WhatsappMessage.objects.create(conversation=conv, role="assistant", content=reply)
                    send_whatsapp_text(to_wa_id=from_id, body=reply)

    return JsonResponse({"ok": True})
