from django.core.management.base import BaseCommand

from properties.models import City


DEFAULT_CITIES = [
    # South Africa (common/popular)
    "Johannesburg",
    "Cape Town",
    "Durban",
    "Pretoria",
    "Bloemfontein",
    "Gqeberha",
    "East London",
    "Polokwane",
    "Nelspruit",
    "Mbombela",
    "Kimberley",
    "Rustenburg",
    "Pietermaritzburg",
    "Stellenbosch",
    "George",
    "Mthatha",
    "Vereeniging",
    "Klerksdorp",
    "Welkom",
    "Soweto",
]


class Command(BaseCommand):
    help = "Seed the City table with a default list (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only-if-empty",
            action="store_true",
            help="Only seed when City table is empty.",
        )

    def handle(self, *args, **options):
        if options.get("only_if_empty") and City.objects.exists():
            self.stdout.write(self.style.WARNING("City table not empty; skipping."))
            return

        existing_lower = set(City.objects.values_list("name", flat=True))
        existing_lower = {name.strip().lower() for name in existing_lower if name}

        created = 0
        for name in DEFAULT_CITIES:
            normalized = name.strip()
            if not normalized:
                continue
            if normalized.lower() in existing_lower:
                continue
            City.objects.create(name=normalized)
            existing_lower.add(normalized.lower())
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded cities. Created: {created}. Total: {City.objects.count()}"))
