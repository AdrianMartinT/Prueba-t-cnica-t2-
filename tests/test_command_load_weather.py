import datetime as dt
from zoneinfo import ZoneInfo
from django.core.management import call_command
from django.conf import settings
from meteo.models import City, HourlyWeather


class DummyGeo:
    def __init__(self, name, country, lat, lon):
        self.name = name
        self.country = country
        self.latitude = lat
        self.longitude = lon


def test_load_weather_uses_user_city_name(monkeypatch, db):
    def fake_geocode(city_name):
        return DummyGeo(name="Seville", country="Spain", lat=37.39, lon=-5.99)

    tz = ZoneInfo(settings.TIME_ZONE)

    def fake_fetch_hourly(lat, lon, start, end):
        return [
            {"date_time": dt.datetime(2024, 7, 1, 0, tzinfo=tz), "temperature_2m": 20.0, "precipitation": 0.0}
        ]

    from meteo.services import open_meteo as svc
    monkeypatch.setattr(svc, "geocode_city", fake_geocode)
    monkeypatch.setattr(svc, "fetch_hourly", fake_fetch_hourly)

    call_command("load_weather", city="Sevilla", start="2024-07-01", end="2024-07-01")

    city = City.objects.get(country="Spain")
    assert city.name == "Sevilla"
    assert HourlyWeather.objects.filter(city=city).count() == 1
