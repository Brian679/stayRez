from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from web.sitemaps import sitemaps
from web import views as web_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django-sitemap"),
    path("robots.txt", web_views.robots_txt, name="robots-txt"),
    path("api/", include("api.urls")),
    # Public web site at root
    path("", include("web.urls")),
    # Dashboard routes (kept for backward-compatibility)
    path("dashboard/", include("web.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
