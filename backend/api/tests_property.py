from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from properties.models import University, Property


class PropertyAPITests(TestCase):
    def setUp(self):
        self.landlord = User.objects.create_user(email="landlord@example.com", password="pass", role="landlord")
        self.user = User.objects.create_user(email="user@example.com", password="pass", role="general")
        self.uni = University.objects.create(name="MapUni", admin_fee_per_head=10, latitude=12.3, longitude=34.5)
        self.client = APIClient()

    def test_landlord_can_create_property(self):
        self.client.force_authenticate(user=self.landlord)
        url = "/api/landlord/properties/add/"
        payload = {"title": "LL House", "description": "Nice", "property_type": "students", "university": self.uni.id, "latitude": 12.31, "longitude": 34.51}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Property.objects.filter(owner=self.landlord).count(), 1)

    def test_nearby_search_returns_properties_within_radius(self):
        # create an approved property
        p = Property.objects.create(title="Nearby", owner=self.landlord, university=self.uni, property_type="students", latitude=12.31, longitude=34.51, is_approved=True)
        url = "/api/properties/nearby/?lat=12.31&lng=34.51&radius_km=2"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.data["results"]) >= 1)

    def test_landlord_add_property_with_images(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        # Use API endpoint which returns JSON and status 201
        self.client.force_authenticate(user=self.landlord)
        url = "/api/landlord/properties/add/"
        jpeg_bytes = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00" + (b"\x08" * 64) +
            b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\"\x00\x02\x11\x01\x03\x11\x01"
            b"\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00" + b"\xd2\xcf \xff\xd9"
        )
        img = SimpleUploadedFile("test.jpg", jpeg_bytes, content_type="image/jpeg")
        payload = {
            "title": "WithImg",
            "description": "Has image",
            "property_type": "students",
            "university": self.uni.id,
            "latitude": 12.31,
            "longitude": 34.51,
        }
        data = {
            'title': 'WithImg',
            'description': 'Has image',
            'property_type': 'students',
            'university': self.uni.id,
            'latitude': 12.31,
            'longitude': 34.51,
            'images': [img],
        }
        resp = self.client.post(url, data, format='multipart')
        self.assertEqual(resp.status_code, 201, f"resp.data: {resp.data}")
        p = Property.objects.filter(owner=self.landlord, title="WithImg").first()
        self.assertIsNotNone(p)
        self.assertEqual(p.images.count(), 1)

    def test_university_properties_filters_and_ordering(self):
        # create several properties with varying attributes
        p1 = Property.objects.create(title="A Boys Single", owner=self.landlord, university=self.uni, property_type="students", gender="boys", sharing="single", nightly_price=10, latitude=12.30, longitude=34.50, is_approved=True)
        p2 = Property.objects.create(title="B Girls Two", owner=self.landlord, university=self.uni, property_type="students", gender="girls", sharing="two", nightly_price=20, latitude=12.32, longitude=34.52, is_approved=True)
        p3 = Property.objects.create(title="C Mixed", owner=self.landlord, university=self.uni, property_type="students", gender="mixed", sharing="other", nightly_price=5, latitude=12.35, longitude=34.55, is_approved=True)
        # filter by gender
        url = f"/api/universities/{self.uni.id}/properties/?gender=boys"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(r["title"].startswith("A Boys") for r in resp.data.get("results", resp.data)))
        # order by price desc: ensure highest price is first
        url = f"/api/universities/{self.uni.id}/properties/?order=price_desc"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        results = resp.data.get("results", resp.data)
        prices = [r.get("nightly_price") for r in results]
        # ensure highest price is first if prices exist
        non_null_prices = [p for p in prices if p is not None]
        if non_null_prices:
            # compare numeric values (avoid formatting differences)
            self.assertEqual(float(non_null_prices[0]), max([float(x) for x in non_null_prices]))

    def test_property_list_distance_ordering(self):
        # properties at different distances
        p1 = Property.objects.create(title="Near", owner=self.landlord, property_type="students", university=self.uni, latitude=12.300, longitude=34.500, nightly_price=10, is_approved=True)
        p2 = Property.objects.create(title="Far", owner=self.landlord, property_type="students", university=self.uni, latitude=12.400, longitude=34.600, nightly_price=20, is_approved=True)
        url = "/api/properties/?lat=12.300&lng=34.500&order=distance_asc"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        results = resp.data.get("results", resp.data)
        # ensure that 'Near' appears before 'Far'
        titles = [r.get("title") for r in results]
        self.assertTrue(titles.index("Near") < titles.index("Far"))
