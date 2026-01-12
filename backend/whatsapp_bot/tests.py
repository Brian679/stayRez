from django.test import TestCase


class WhatsappWebhookTests(TestCase):
    def test_webhook_verification_challenge(self):
        resp = self.client.get(
            "/whatsapp/webhook/",
            {
                "hub.mode": "subscribe",
                "hub.verify_token": "test-token",
                "hub.challenge": "12345",
            },
        )
        # No token configured => forbidden
        self.assertEqual(resp.status_code, 403)
