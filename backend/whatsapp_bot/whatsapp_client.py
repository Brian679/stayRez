import os
import requests


def send_whatsapp_text(to_wa_id: str, body: str) -> None:
    """Send a plain text message via WhatsApp Cloud API.

    Requires:
    - WHATSAPP_PHONE_NUMBER_ID
    - WHATSAPP_ACCESS_TOKEN
    """

    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()

    if not phone_number_id or not access_token:
        # Not configured; fail silently in dev to avoid crashing webhooks.
        return

    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "text",
        "text": {"body": body},
    }

    try:
        requests.post(url, headers=headers, json=payload, timeout=15)
    except Exception:
        # Avoid raising from webhook handler
        return
