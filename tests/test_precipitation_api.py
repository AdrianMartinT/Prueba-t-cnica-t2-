from rest_framework.test import APIClient


def test_precipitation_stats_ok(sample_hours_madrid):
    client = APIClient()
    url = "/api/precipitation/?city=Madrid&start=2024-07-01&end=2024-07-03"
    response = client.get(url)
    assert response.status_code == 200
    payload = response.json()["precipitation"]
    assert payload["total"] >= 0.0
    assert payload["days_with_precipitation"] >= 0
    assert "max" in payload and "value" in payload["max"] and "date" in payload["max"]
