import csv

from django.core.management.base import BaseCommand

from leads.models import Lead

FIELD_MAP = {
    "name": "name",
    "address": "address",
    "phone": "phone",
    "email": "email",
    "url": "url",
    "country": "country",
    "state": "state",
    "city": "city",
    "zip": "zip",
    "facebook_link": "facebook_link",
    "instagram_link": "instagram_link",
    "twitter_link": "twitter_link",
    "whatsapp_link": "whatsapp_link",
    "tiktok_link": "tiktok_link",
    "linkedin_link": "linkedin_link",
    "youtube_link": "youtube_link",
    "primary_category_name": "primary_category_name",
    "category_name": "category_name",
}


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


class Command(BaseCommand):
    help = "Import sales leads from a Google-Maps-style places CSV export."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing leads before importing.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        if options["clear"]:
            deleted, _ = Lead.objects.all().delete()
            self.stdout.write(f"Deleted {deleted} existing leads.")

        batch = []
        batch_size = 1000
        created = 0

        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kwargs = {model_field: row.get(csv_field, "") or ""
                          for csv_field, model_field in FIELD_MAP.items()}
                kwargs["lat"] = to_float(row.get("lat"))
                kwargs["lng"] = to_float(row.get("lng"))
                kwargs["rating_count"] = to_int(row.get("rating_count"))
                kwargs["star_count"] = to_float(row.get("star_count"))

                batch.append(Lead(**kwargs))
                if len(batch) >= batch_size:
                    Lead.objects.bulk_create(batch)
                    created += len(batch)
                    batch = []

            if batch:
                Lead.objects.bulk_create(batch)
                created += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Imported {created} leads."))
