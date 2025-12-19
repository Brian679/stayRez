from django.urls import path
from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="api-register"),
    path("auth/token/", views.TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", views.TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", views.TokenVerifyView.as_view(), name="token_verify"),
    path("auth/login/", views.LoginView.as_view(), name="api-login"),
    path("auth/logout/", views.LogoutView.as_view(), name="api-logout"),
    path("auth/profile/", views.ProfileView.as_view(), name="api-profile"),
    path("auth/password/change/", views.ChangePasswordView.as_view(), name="api-password-change"),

    # Legacy aliases (mobile/backward-compat)
    path("register/", views.RegisterView.as_view(), name="api-register-legacy"),
    path("login/", views.LoginView.as_view(), name="api-login-legacy"),
    path("logout/", views.LogoutView.as_view(), name="api-logout-legacy"),
    path("profile/", views.ProfileView.as_view(), name="api-profile-legacy"),
    path("services/", views.ServiceListView.as_view(), name="services-list"),
    path("cities/", views.CityListView.as_view(), name="cities-list"),
    path("universities/", views.UniversityListView.as_view(), name="universities-list"),
    path("universities/<int:pk>/", views.UniversityDetailView.as_view(), name="university-detail"),
    path("universities/<int:pk>/properties/", views.UniversityPropertiesView.as_view(), name="university-properties"),
    path("properties/", views.PropertyListView.as_view(), name="properties-list"),
    path("properties/nearby/", views.NearbyPropertiesView.as_view(), name="properties-nearby"),
    path("properties/<int:pk>/", views.PropertyDetailView.as_view(), name="property-detail"),
    path("properties/<int:pk>/contact/", views.ContactLandlordView.as_view(), name="api-property-contact"),
    path("properties/<int:pk>/reviews/", views.ReviewCreateView.as_view(), name="property-reviews"),
    path("landlord/properties/", views.LandlordPropertyListView.as_view(), name="landlord-properties"),
    path("landlord/properties/add/", views.LandlordPropertyCreateView.as_view(), name="landlord-property-add"),
    path("landlord/properties/<int:pk>/", views.LandlordPropertyDetailView.as_view(), name="landlord-property-detail"),
    path("landlord/activity/", views.LandlordActivityListView.as_view(), name="landlord-activity"),
    path("payments/confirm/", views.PaymentConfirmationCreateView.as_view(), name="payment-confirmation"),
    path("payments/notify-admin/<int:pk>/", views.NotifyAdminPaymentView.as_view(), name="notify-admin-payment"),

    # admin actions
    path("admin/payment-confirmations/<int:pk>/approve/", views.ApprovePaymentConfirmationView.as_view(), name="approve-payment-confirmation"),
    path("admin/payment-confirmations/<int:pk>/decline/", views.DeclinePaymentConfirmationView.as_view(), name="decline-payment-confirmation"),
    path("admin/properties/<int:pk>/approve/", views.ApprovePropertyView.as_view(), name="approve-property"),

    # notifications
    path("notifications/", views.NotificationListView.as_view(), name="notifications-list"),
    path("notifications/<int:pk>/mark-read/", views.MarkNotificationReadView.as_view(), name="mark-notification-read"),
]
