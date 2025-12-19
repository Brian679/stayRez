from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models import User


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user(self):
        url = reverse('api-register')
        payload = {'email': 'new@example.com', 'password': 'pass', 'username': 'newuser', 'full_name': 'New User', 'role': 'general'}
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    def test_profile_get_and_update(self):
        user = User.objects.create_user(email='u@example.com', password='pass', full_name='Old', role='general')
        self.client.force_authenticate(user=user)
        url = reverse('api-profile')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['email'], 'u@example.com')

        resp2 = self.client.patch(url, {'full_name': 'New Name'}, format='json')
        self.assertEqual(resp2.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.full_name, 'New Name')

    def test_session_login_logout(self):
        user = User.objects.create_user(email='s@example.com', password='pass', full_name='S', role='general')
        login_url = reverse('api-login')
        resp = self.client.post(login_url, {'email': 's@example.com', 'password': 'pass'}, format='json')
        self.assertEqual(resp.status_code, 200)
        # after login, profile should be accessible via session
        profile_url = reverse('api-profile')
        resp2 = self.client.get(profile_url)
        self.assertEqual(resp2.status_code, 200)
        # logout
        logout_url = reverse('api-logout')
        resp3 = self.client.post(logout_url)
        self.assertEqual(resp3.status_code, 200)
        # profile now should be unauthorized
        resp4 = self.client.get(profile_url)
        # depending on auth configuration, unauthenticated response may be 401 or 403
        self.assertIn(resp4.status_code, (401, 403))

    def test_token_endpoints_fallback(self):
        # Token obtain endpoint exists (may be 501 when SimpleJWT absent)
        token_url = reverse('token_obtain_pair')
        resp = self.client.post(token_url, {'email': 'x', 'password': 'y'}, format='json')
        # Accept 501 (not implemented) or 400/401 for invalid credentials if JWT installed
        self.assertIn(resp.status_code, (501, 400, 401))
        # refresh endpoint should similarly be available and return 501 if not installed
        refresh_url = reverse('token_refresh')
        resp2 = self.client.post(refresh_url, {}, format='json')
        self.assertIn(resp2.status_code, (501, 400))
        verify_url = reverse('token_verify')
        resp3 = self.client.post(verify_url, {}, format='json')
        self.assertIn(resp3.status_code, (501, 400))

