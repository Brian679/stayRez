import os
from typing import Any, Dict, List, Optional

from django.db.models import Q

from properties.models import University, Property
from .models import WhatsappConversation


def _system_prompt() -> str:
    return (
        "You are offRez, a WhatsApp assistant for finding accommodation and rentals. "
        "You can understand and respond in English or Shona. Always reply in the user's language. "
        "Keep replies concise and WhatsApp-friendly. "
        "You can help users: browse universities, list available properties, filter by gender/sharing/price, "
        "and explain the admin-fee payment and landlord contact flow. "
        "If the user asks for landlord contact details, explain that contacts are unlocked only after admin fee approval. "
        "If you don't know, ask one short clarifying question."
    )


def _recent_messages(conversation: WhatsappConversation, limit: int = 12) -> List[Dict[str, str]]:
    qs = conversation.messages.order_by("-created_at")[:limit]
    msgs = list(reversed(qs))
    out = []
    for m in msgs:
        if m.role in ("user", "assistant"):
            out.append({"role": m.role, "content": m.content})
    return out


def _tool_list_universities(query: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    qs = University.objects.all().order_by("name")
    if query:
        qs = qs.filter(name__icontains=query.strip())
    qs = qs[: max(1, min(int(limit), 25))]
    return [{"id": u.id, "name": u.name, "admin_fee_per_head": str(u.admin_fee_per_head)} for u in qs]


def _tool_list_properties(
    university_id: Optional[int] = None,
    query: Optional[str] = None,
    gender: Optional[str] = None,
    sharing: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    qs = Property.objects.filter(is_approved=True, is_available=True)
    if university_id:
        qs = qs.filter(university_id=university_id)
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query))
    if gender in {"all", "boys", "girls", "mixed"}:
        qs = qs.filter(gender=gender)
    if sharing in {"single", "two", "other"}:
        qs = qs.filter(sharing=sharing)
    if max_price is not None:
        try:
            max_price_val = float(max_price)
            qs = qs.filter(Q(price_per_month__lte=max_price_val) | Q(nightly_price__lte=max_price_val))
        except Exception:
            pass

    qs = qs.order_by("-created_at")[: max(1, min(int(limit), 15))]

    out = []
    for p in qs:
        price = p.price_per_month if p.price_per_month is not None else p.nightly_price
        out.append(
            {
                "id": p.id,
                "title": p.title,
                "gender": p.get_gender_display() if hasattr(p, "get_gender_display") else p.gender,
                "sharing": p.get_sharing_display() if hasattr(p, "get_sharing_display") else p.sharing,
                "price": str(price) if price is not None else None,
            }
        )
    return out


def _tool_property_details(property_id: int) -> Dict[str, Any]:
    p = Property.objects.get(pk=property_id)
    price = p.price_per_month if p.price_per_month is not None else p.nightly_price
    return {
        "id": p.id,
        "title": p.title,
        "description": (p.description or "")[:500],
        "gender": p.get_gender_display() if hasattr(p, "get_gender_display") else p.gender,
        "sharing": p.get_sharing_display() if hasattr(p, "get_sharing_display") else p.sharing,
        "price": str(price) if price is not None else None,
        "university": p.university.name if p.university else None,
        "location": p.location or None,
        "notes": "Landlord contact details are shown only after admin fee approval.",
    }


def _fallback_reply(user_text: str) -> str:
    # Very small non-AI fallback for dev environments.
    return (
        "I can help you find accommodation. Tell me which university (or city) you want, "
        "and your budget (optional).\n\n"
        "Example: ‘Ndeipi nzvimbo dziripo kuUZ pasi pe$150?’"
    )


def generate_reply(conversation: WhatsappConversation, user_text: str, request=None) -> str:
    """Generate an AI reply.

    Uses OpenAI if OPENAI_API_KEY is set; otherwise returns a safe fallback.
    """

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _fallback_reply(user_text)

    # Lazy import so the app can run without the package in dev.
    try:
        from openai import OpenAI
    except Exception:
        return _fallback_reply(user_text)

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"

    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_universities",
                "description": "List universities (optionally filtered by name query).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_properties",
                "description": "List available properties with optional filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "university_id": {"type": "integer"},
                        "query": {"type": "string"},
                        "gender": {"type": "string", "enum": ["all", "boys", "girls", "mixed"]},
                        "sharing": {"type": "string", "enum": ["single", "two", "other"]},
                        "max_price": {"type": "number"},
                        "limit": {"type": "integer"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "property_details",
                "description": "Get details for a specific property id.",
                "parameters": {
                    "type": "object",
                    "properties": {"property_id": {"type": "integer"}},
                    "required": ["property_id"],
                },
            },
        },
    ]

    messages: List[Dict[str, str]] = [{"role": "system", "content": _system_prompt()}]
    messages += _recent_messages(conversation)
    messages.append({"role": "user", "content": user_text})

    # 1st call: let model decide tool usage
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.3,
    )

    choice = resp.choices[0]
    msg = choice.message

    # Tool loop: handle 0..N tool calls
    tool_calls = getattr(msg, "tool_calls", None) or []
    if tool_calls:
        messages.append({"role": "assistant", "content": msg.content or ""})
        for tc in tool_calls:
            fn = tc.function
            name = fn.name
            args = {}
            try:
                import json as _json

                args = _json.loads(fn.arguments or "{}")
            except Exception:
                args = {}

            if name == "list_universities":
                result = _tool_list_universities(query=args.get("query"), limit=args.get("limit", 10))
            elif name == "list_properties":
                result = _tool_list_properties(
                    university_id=args.get("university_id"),
                    query=args.get("query"),
                    gender=args.get("gender"),
                    sharing=args.get("sharing"),
                    max_price=args.get("max_price"),
                    limit=args.get("limit", 8),
                )
            elif name == "property_details":
                result = _tool_property_details(property_id=int(args.get("property_id")))
            else:
                result = {"error": "unknown tool"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                }
            )

        # 2nd call: final answer using tool results
        resp2 = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
        )
        return (resp2.choices[0].message.content or "").strip() or _fallback_reply(user_text)

    return (msg.content or "").strip() or _fallback_reply(user_text)
