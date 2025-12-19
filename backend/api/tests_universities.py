from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from properties.models import University, City


class UniversityAPITests(TestCase):
    def setUp(self):
        self.city = City.objects.create(name='Harare')
        self.uni = University.objects.create(name='University of Zimbabwe', city=self.city, admin_fee_per_head=50.00, latitude=-17.823, longitude=31.033)
        self.client = APIClient()

    def test_universities_list(self):
        url = reverse('universities-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], 'University of Zimbabwe')
        self.assertEqual(float(resp.data[0]['admin_fee_per_head']), 50.0)

    def test_university_detail(self):
        url = reverse('university-detail', kwargs={'pk': self.uni.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'University of Zimbabwe')
        self.assertEqual(resp.data['city_name'], 'Harare')

    def test_web_universities_page(self):
        # Test web page lists universities and shows admin fee
        resp = self.client.get('/dashboard/students/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'University of Zimbabwe', resp.content)
        self.assertIn(b'50', resp.content)


class UniversityAPITests(TestCase):
    def setUp(self):
        self.city = City.objects.create(name='Harare')
        self.uni = University.objects.create(name='University of Zimbabwe', city=self.city, admin_fee_per_head=50.00, latitude=-17.823, longitude=31.033)
        self.client = APIClient()

    def test_universities_list(self):
        url = reverse('universities-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], 'University of Zimbabwe')
        self.assertEqual(float(resp.data[0]['admin_fee_per_head']), 50.0)

    def test_university_detail(self):
        url = reverse('university-detail', kwargs={'pk': self.uni.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'University of Zimbabwe')
        self.assertEqual(resp.data['city_name'], 'Harare')

    def test_web_universities_page(self):
        # Test web page lists universities and shows admin fee
        resp = self.client.get('/dashboard/students/')
        self.assertIn(b'University of Zimbabwe', resp.content)
        self.assertIn(b'50', resp.content)
