# offRez Backend

Django backend scaffold for the offRez app (students accommodation, long-term, short-term, real estate, resorts, shops)

Run locally:

- python -m venv venv
- venv\Scripts\activate
- pip install -r requirements.txt
- cd backend
- python manage.py migrate
- python manage.py createsuperuser
- python manage.py runserver

This repo contains initial models: Custom User, University, City, Property, Review, AdminFeePayment, PaymentConfirmation and basic API endpoints.

Available API endpoints (early):
- POST /api/auth/register/ (email,password,full_name,role)
- POST /api/auth/token/ (obtain JWT access/refresh)
- GET  /api/universities/  (list universities and admin fee per head)
- GET  /api/properties/    (list approved properties)
- POST /api/payments/confirm/ (submit payment confirmation with university id, number of students and confirmation text)

Additional (new):
- GET  /api/universities/<id>/properties/  (list approved properties for a university)
- GET  /api/properties/<id>/  (property detail, reviews, avg rating)
- POST /api/properties/<id>/reviews/  (authenticated: submit review for property)

Website pages:
- GET / (home grid of services)
- GET /students/ (universities list)
- GET /students/university/<id>/ (list properties for university)
- GET /property/<id>/ (property detail, reviews, contact flow)

Mobile App:
- A Kivy skeleton at mobile/kivy_app/main.py that fetches the above API endpoints.


Notes:
- Admins will receive in-app notifications when a payment confirmation is submitted (check `Notifications` in the Django admin).
- Exact property location (latitude/longitude and landlord contact) will be shown only after admin approves the payment confirmation and marks the payment as valid.

