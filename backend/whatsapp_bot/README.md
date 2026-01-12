# WhatsApp Chatbot (offRez)

This adds a WhatsApp Cloud API webhook to your Django backend, plus an AI-powered router that can understand and reply in **Shona** or **English**.

## What it does (MVP)

- Receives WhatsApp messages via a webhook.
- Uses an LLM (OpenAI) to understand intent (including Shona) and respond.
- Can call into your DB to:
  - list universities
  - list properties (with simple filters)
  - show property details
- Sends the response back to the user via WhatsApp Cloud API.

## URLs

- Webhook: `/whatsapp/webhook/`

## Environment variables

Required for WhatsApp:
- `WHATSAPP_VERIFY_TOKEN` (any random string you set in Meta + in your env)
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`

Optional security:
- `WHATSAPP_APP_SECRET` (enables X-Hub-Signature-256 validation)

AI:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-4.1-mini`)

## Install deps

Add these to your environment:
- `requests`
- `openai`

## Notes

- If `OPENAI_API_KEY` is not set, the bot returns a short non-AI fallback message.
- For production, ensure `WHATSAPP_APP_SECRET` is set so webhook requests are signed.
