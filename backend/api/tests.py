from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models import User
from properties.models import University, Property
from payments.models import AdminFeePayment, PaymentConfirmation
from core.models import Notification


class PaymentAndContactTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", password="pass", role="admin")
        self.user = User.objects.create_user(email="user@example.com", password="pass", role="general")
        self.uni = University.objects.create(name="Test Uni", admin_fee_per_head=10)
        self.prop = Property.objects.create(
            title="Test Property",
            owner=self.admin,
            university=self.uni,
            property_type="students",
            house_number="12A",
            contact_phone="+123456789",
            caretaker_number="+987654321",
            latitude=12.345678,
            longitude=98.765432,
            is_approved=True,
        )
        self.client = APIClient()

    def test_submit_payment_confirmation_creates_payment_and_notifies_admin(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("payment-confirmation")
        payload = {"university": self.uni.id, "for_number_of_students": 2, "confirmation_text": "Paid to Ecocash"}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, 201)

        payment = AdminFeePayment.objects.get(user=self.user, university=self.uni)
        self.assertEqual(float(payment.amount), 20.0)
        self.assertEqual(payment.for_number_of_students, 2)

        conf = PaymentConfirmation.objects.get(payment=payment)
        self.assertEqual(conf.status, "pending")

        # admin should have a notification
        self.assertTrue(Notification.objects.filter(recipient=self.admin, title__icontains="payment confirmation").exists() or Notification.objects.filter(recipient=self.admin, title__icontains="payment").exists())

    def test_admin_approve_activates_payment(self):
        payment = AdminFeePayment.objects.create(user=self.user, university=self.uni, amount=30, for_number_of_students=3)
        conf = PaymentConfirmation.objects.create(payment=payment, confirmation_text="confirm")

        url = reverse("approve-payment-confirmation", kwargs={"pk": conf.id})
        self.client.force_authenticate(user=self.admin)
        # UpdateAPIView expects PUT or PATCH
        resp = self.client.put(url, {}, format="json")
        self.assertEqual(resp.status_code, 200)

        conf.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(conf.status, "approved")
        self.assertGreater(payment.uses_remaining, 0)
        self.assertIsNotNone(payment.valid_until)

        # user notified
        self.assertTrue(Notification.objects.filter(recipient=self.user, title__icontains="Payment confirmed").exists())

    def test_contact_landlord_no_payment_returns_instructions(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("api-property-contact", kwargs={"pk": self.prop.id})
        resp = self.client.post(url, {"students": 3}, format="json")
        self.assertEqual(resp.status_code, 402)
        self.assertIn("payment_instructions", resp.data)
        self.assertEqual(float(resp.data["payment_instructions"]["amount"]), 30.0)

    def test_contact_landlord_with_active_payment_returns_contact_and_decrements(self):
        payment = AdminFeePayment.objects.create(user=self.user, university=self.uni, amount=50, for_number_of_students=5)
        payment.activate(days_valid=30)
        initial_uses = payment.uses_remaining

        self.client.force_authenticate(user=self.user)
        url = reverse("api-property-contact", kwargs={"pk": self.prop.id})
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["house_number"], "12A")

        payment.refresh_from_db()
        self.assertEqual(payment.uses_remaining, initial_uses - 1)

    def test_admin_decline_payment_confirmation(self):
        payment = AdminFeePayment.objects.create(user=self.user, university=self.uni, amount=20, for_number_of_students=2)
        conf = PaymentConfirmation.objects.create(payment=payment, confirmation_text="confirm")

        url = reverse("decline-payment-confirmation", kwargs={"pk": conf.id})
        self.client.force_authenticate(user=self.admin)
        resp = self.client.put(url, {}, format="json")
        self.assertEqual(resp.status_code, 200)

        conf.refresh_from_db()
        self.assertEqual(conf.status, "declined")
        self.assertTrue(Notification.objects.filter(recipient=self.user, title__icontains="Payment declined").exists())

    def test_admin_ajax_approve_decline_via_dashboard(self):
        payment = AdminFeePayment.objects.create(user=self.user, university=self.uni, amount=40, for_number_of_students=4)
        conf = PaymentConfirmation.objects.create(payment=payment, confirmation_text="confirm")

        url = reverse("dashboard-payment-confirmations")
        # approve via AJAX
        self.client.force_login(self.admin)
        resp = self.client.post(url, {"action": "approve", "pk": conf.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        conf.refresh_from_db()
        self.assertEqual(conf.status, "approved")

        # create another and decline
        payment2 = AdminFeePayment.objects.create(user=self.user, university=self.uni, amount=40, for_number_of_students=4)
        conf2 = PaymentConfirmation.objects.create(payment=payment2, confirmation_text="confirm2")
        resp2 = self.client.post(url, {"action": "decline", "pk": conf2.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code, 200)
        conf2.refresh_from_db()
        self.assertEqual(conf2.status, "declined")
