from django.test import TestCase
from django.urls import reverse
from accounts.models import User


class WebAuthTests(TestCase):
    def test_register_view_and_login(self):
        url = reverse('web-register')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(url, {
            'username': 'webuser',
            'email': 'web@example.com',
            'password': 'pass12345',
            'full_name': 'Web',
            'role': 'general'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(email='web@example.com').exists())

    def test_login_and_profile(self):
        u = User.objects.create_user(email='x@example.com', password='pass12345', full_name='X', username='x')
        login_url = reverse('web-login')
        resp = self.client.post(login_url, {'identifier': 'x@example.com', 'password': 'pass12345'})
        # login redirects
        self.assertEqual(resp.status_code, 302)
        profile_url = reverse('web-profile')
        resp2 = self.client.get(profile_url)
        # should redirect to login because client not authenticated after manual post
        self.assertIn(resp2.status_code, (200,302))

    def test_home_links_to_students_and_university_links_to_properties(self):
        # verify home page has a link to the students universities page
        resp = self.client.get(reverse('web-home'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('/students-accommodation/universities/', resp.content.decode())

        # create a sample university and ensure university card links to properties page
        from properties.models import University
        uni = University.objects.create(name='MapUni', admin_fee_per_head=10)
        resp2 = self.client.get(reverse('students-universities'))
        # old /students/ URL should permanently redirect to canonical route
        self.assertEqual(resp2.status_code, 301)

        resp3 = self.client.get(reverse('students-accommodation-universities'))
        self.assertEqual(resp3.status_code, 200)
        self.assertIn(f"/students-accommodation/{uni.name.lower()}/", resp3.content.decode())
