import datetime as dt
import pytest
from django.utils.timezone import make_aware
from django.conf import settings
from meteo.models import City, HourlyWeather

TZ = settings.TIME_ZONE


@pytest.fixture
def city_madrid(db):
    return City.objects.create(
        name="Madrid", country="Spain", latitude=40.4168, longitude=-3.7038
    )


def aware(year, month, day, hour):
    return make_aware(dt.datetime(year, month, day, hour, 0), TZ)


@pytest.fixture
def sample_hours_madrid(db, city_madrid):
    data = [
        (aware(2024, 7, 1, 0), 18.0, 0.2),
        (aware(2024, 7, 1, 15), 30.0, 1.3),
        (aware(2024, 7, 2, 7), 14.5, 0.0),
        (aware(2024, 7, 3, 17), 33.4, 3.7),
    ]
    for dt_, temperature, precipitation in data:
        HourlyWeather.objects.create(city=city_madrid, date_time=dt_, temperature_2m=temperature, precipitation=precipitation)
    return city_madrid
