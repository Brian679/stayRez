from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.home, name="web-home"),
    path("about/", views.about_view, name="web-about"),
    path("contact/", views.contact_view, name="web-contact"),
    # Canonical students accommodation URLs
    path("students-accommodation/universities/", views.universities, name="students-accommodation-universities"),
    path("students-accommodation/<slug:university_slug>/", views.university_properties_by_slug, name="students-accommodation-university"),
    path("students-accommodation/<slug:university_slug>/<slug:property_slug>/", views.student_property_detail, name="students-accommodation-detail"),

    # Back-compat redirects (old URLs)
    path("students/", views.redirect_students_universities, name="students-universities"),
    path("students/university/<int:pk>/", views.redirect_students_university_properties, name="students-university-properties"),
    path("longterm/", views.longterm_cities, name="longterm-cities"),
    path("longterm/properties/", views.longterm_properties, name="longterm-properties"),
    path("shortterm/", views.shortterm_cities, name="shortterm-cities"),
    path("shortterm/properties/", views.shortterm_properties, name="shortterm-properties"),
    path("realestate/", views.realestate_cities, name="realestate-cities"),
    path("realestate/properties/", views.realestate_properties, name="realestate-properties"),
    path("resorts/", views.resort_cities, name="resort-cities"),
    path("resorts/properties/", views.resort_properties, name="resort-properties"),
    path("shops/", views.shop_cities, name="shop-cities"),
    path("shops/properties/", views.shop_properties, name="shop-properties"),
    path("property/<int:pk>/", views.property_detail, name="web-property-detail"),
    path("property/<int:pk>/reviews/", views.property_review_create, name="web-property-reviews"),
    path("property/<int:pk>/reviews/delete/", views.property_review_delete, name="web-property-review-delete"),
    path("property/<int:pk>/contact/", views.property_contact, name="property-contact"),
    path("dashboard/payment-confirmations/", views.payment_confirmations, name="dashboard-payment-confirmations"),
    path("dashboard/my-properties/", views.my_properties, name="dashboard-my-properties"),
    path("dashboard/properties/add/", views.add_property, name="dashboard-add-property"),
    path("dashboard/properties/<int:pk>/edit/", views.edit_property, name="dashboard-edit-property"),
    path("dashboard/properties/<int:pk>/toggle-availability/", views.toggle_property_availability, name="dashboard-toggle-availability"),
    path("dashboard/properties/<int:pk>/delete/", views.delete_property, name="dashboard-delete-property"),
    path("auth/register/", views.register_view, name="web-register"),
    path("auth/login/", views.login_view, name="web-login"),
    path("auth/logout/", views.logout_view, name="web-logout"),
    path("auth/profile/", views.profile_view, name="web-profile"),

    # Password management (web)
    path("auth/password/change/", views.change_password, name="web-password-change"),
    path(
        "auth/password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(template_name="web/password_change_done.html"),
        name="web-password-change-done",
    ),
    path("auth/password/reset/", views.password_reset_request, name="web-password-reset"),
    path(
        "auth/password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="web/password_reset_done.html"),
        name="web-password-reset-done",
    ),
    path(
        "auth/password/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="web/password_reset_confirm.html"),
        name="web-password-reset-confirm",
    ),
    path("auth/password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="web/password_reset_complete.html"),
        name="web-password-reset-complete",
    ),
    path("api/properties/<int:property_id>/toggle-like/", views.toggle_property_like, name="toggle-property-like"),

    # --- Slug-driven service routes (preferred)
    # These must be last to avoid capturing fixed prefixes like /property/, /auth/, /dashboard/.
    path("<slug:service_slug>/", views.service_entry, name="service-entry"),
    path("<slug:service_slug>/properties/", views.service_properties, name="service-properties"),
    path("<slug:service_slug>/university/<int:pk>/", views.university_properties, name="service-university-properties"),
]
