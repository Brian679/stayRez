from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils.text import slugify

from properties.models import Property, Service, University


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return [
            "web-home",
            "web-about",
            "web-contact",
            "students-accommodation-universities",
            "longterm-cities",
            "longterm-properties",
            "shortterm-cities",
            "shortterm-properties",
            "realestate-cities",
            "realestate-properties",
            "resort-cities",
            "resort-properties",
            "shop-cities",
            "shop-properties",
        ]

    def location(self, item):
        return reverse(item)


class PropertySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Property.objects.filter(is_approved=True, is_available=True).order_by("-created_at")

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        if getattr(obj, 'property_type', None) == 'students' and getattr(obj, 'university_id', None):
            return reverse(
                "students-accommodation-detail",
                kwargs={
                    "university_slug": slugify(obj.university.name),
                    "property_slug": slugify(obj.title),
                },
            )
        return reverse("web-property-detail", args=[obj.pk])


class ServiceSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Service.objects.filter(is_active=True).order_by("order", "name")

    def location(self, obj):
        return reverse("service-entry", args=[obj.slug])


class UniversitySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return University.objects.all().order_by("name")

    def location(self, obj):
        return reverse(
            "students-accommodation-university",
            kwargs={"university_slug": slugify(obj.name)},
        )


sitemaps = {
    "static": StaticViewSitemap,
    "services": ServiceSitemap,
    "universities": UniversitySitemap,
    "properties": PropertySitemap,
}
