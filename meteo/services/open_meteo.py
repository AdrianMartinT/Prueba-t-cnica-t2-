import requests
from dataclasses import dataclass
from django.conf import settings
from datetime import datetime
from zoneinfo import ZoneInfo

GEOCODE_URL = settings.OPEN_METEO_GEOCODE_URL
ARCHIVE_URL = settings.OPEN_METEO_ARCHIVE_URL


@dataclass
class GeocodeResult:
    name: str
    country: str
    latitude: float
    longitude: float


def geocode_city(city: str) -> GeocodeResult | None:
    result = requests.get(GEOCODE_URL, params={"name": city, "count": 1})
    result.raise_for_status()
    data = result.json()
    if not data.get("results"):
        return None
    x = data["results"][0]
    return GeocodeResult(
        name=x.get("name", city),
        country=x.get("country", "") or "",
        latitude=float(x["latitude"]),
        longitude=float(x["longitude"]),
    )


def fetch_hourly(
    lat: float,
    lon: float,
    start: str,
    end: str,
    tz: str = None
):
    tz = tz or settings.DEFAULT_TZ
    result = requests.get(ARCHIVE_URL, params={
        "latitude": lat, "longitude": lon,
        "start_date": start, "end_date": end,
        "hourly": "temperature_2m,precipitation",
        "timezone": tz,
    })
    result.raise_for_status()
    j = result.json()
    hourly = j.get("hourly", {})
    times = hourly.get("time", []) or []
    temps = hourly.get("temperature_2m", []) or []
    precs = hourly.get("precipitation", []) or []
    tzinfo = ZoneInfo(tz)
    out = []
    for i, t in enumerate(times):
        dt = datetime.fromisoformat(t).replace(tzinfo=tzinfo)
        out.append({
            "date_time": dt,
            "temperature_2m": temps[i] if i < len(temps) else None,
            "precipitation": precs[i] if i < len(precs) else None,
        })
    return out
