from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from meteo.models import City, HourlyWeather
from meteo.services.open_meteo import geocode_city, fetch_hourly


class Command(BaseCommand):
    help = "Load hourly data (temp and precip) for a city and date range."

    def add_arguments(self, p):
        p.add_argument("--city", required=True)
        p.add_argument("--start", required=True, help="YYYY-MM-DD (pasado)")
        p.add_argument("--end", required=True, help="YYYY-MM-DD (pasado)")

    def handle(self, *args, **o):
        city_name, start, end = o["city"], o["start"], o["end"]

        geo = geocode_city(city_name)
        if not geo:
            raise CommandError(f"City not found: {city_name}")

        city, _ = City.objects.get_or_create(
            name=city_name, country=geo.country,
            defaults={"latitude": geo.latitude, "longitude": geo.longitude},
        )
        City.objects.filter(pk=city.pk).update(
            latitude=geo.latitude,
            longitude=geo.longitude
        )

        rows = fetch_hourly(geo.latitude, geo.longitude, start, end)
        objs = [
            HourlyWeather(
                city=city,
                date_time=r["date_time"],
                temperature_2m=r["temperature_2m"],
                precipitation=r["precipitation"],
            )
            for r in rows
        ]

        with transaction.atomic():
            created = HourlyWeather.objects.bulk_create(objs,
                                                        ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"{city} | {start}..{end} | hours received={len(rows)} saved={len(created)}"
        ))
