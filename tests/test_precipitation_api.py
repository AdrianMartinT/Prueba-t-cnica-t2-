from rest_framework.test import APIClient


def test_precipitation_stats_ok(sample_hours_madrid):
    client = APIClient()
    url = "/api/precipitation/?city=Madrid&start=2024-07-01&end=2024-07-03"
    r = client.get(url)
    assert r.status_code == 200
    p = r.json()["precipitation"]
    assert p["total"] > 0.0
    assert p["days_with_precipitation"] >= 1
    assert "max" in p and "value" in p["max"] and "date" in p["max"]
