from rest_framework.test import APIClient


def test_summary_ok(sample_hours_madrid):
    client = APIClient()
    url = "/api/summary/?city=Madrid&start=2024-07-01&end=2024-07-03"
    r = client.get(url)
    assert r.status_code == 200
    data = r.json()
    madrid = data["Madrid"]
    assert madrid["temperature_average"] is not None
    assert madrid["precipitation_total"] >= 0.0
    assert "temperature_max" in madrid and "temperature_min" in madrid
    assert "precipitation_max" in madrid
