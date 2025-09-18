from rest_framework.test import APIClient


def test_temperature_stats_ok(sample_hours_madrid):
    client = APIClient()
    url = "/api/temperature/?city=Madrid&start=2024-07-01&end=2024-07-03&threshold=30"
    r = client.get(url)
    assert r.status_code == 200
    payload = r.json()["temperature"]
    assert "average" in payload
    assert payload["max"]["value"] == 33.4
    assert payload["min"]["value"] == 14.5
    assert payload["hours_above_threshold"] >= 1
