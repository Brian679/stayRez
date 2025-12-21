import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET", "dev-secret-key")

DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

_allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "").strip()
if _allowed_hosts:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(",") if h.strip()]
else:
    # Dev-friendly default; set DJANGO_ALLOWED_HOSTS in production.
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    # 3rd party
    "rest_framework",
    "corsheaders",

    # local apps
    "accounts",
    "properties",
    "payments",
    "core",
    "web",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "backend.context_processors.universities",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

# JWT optional: use SimpleJWT if installed, else fall back to session auth (useful for dev/tests)
try:
    import rest_framework_simplejwt  # noqa
    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ),
    }
    SIMPLE_JWT = {
        "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    }
except Exception:
    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "rest_framework.authentication.SessionAuthentication",
        ),
    }

CORS_ALLOW_ALL_ORIGINS = True

# Trust proxy headers (PythonAnywhere / reverse proxies) so request.build_absolute_uri
# and request.scheme reflect the external HTTPS URL.
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

_csrf_trusted = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf_trusted:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_trusted.split(",") if o.strip()]

# Authentication settings
LOGIN_URL = '/auth/login/'

# Payment details (used on contact/payment pages)
ECOCASH_NUMBER = os.getenv("ECOCASH_NUMBER", "0776487550")
ECOCASH_ACCOUNT_HOLDER = os.getenv("ECOCASH_ACCOUNT_HOLDER", "T. Tayero")

# Contact details (used on Contact Us page)
CONTACT_ADDRESS = os.getenv("CONTACT_ADDRESS", "4376 Coldstream Chinhoyi")
CONTACT_PHONE = os.getenv("CONTACT_PHONE", "+263776487550")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "+263785213532")
