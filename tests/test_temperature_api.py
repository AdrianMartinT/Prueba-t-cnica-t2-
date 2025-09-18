from rest_framework.test import APIClient


def test_temperature_stats_ok(sample_hours_madrid):
    client = APIClient()
    url = "/api/temperature/?city=Madrid&start=2024-07-01&end=2024-07-03&threshold=30"
    response = client.get(url)
    assert response.status_code == 200
    payload = response.json()["temperature"]
    assert "average" in payload
    assert "average_by_day" in payload
    assert "max" in payload
    assert "min" in payload
    assert "hours_above_threshold" in payload
    assert "hours_below_threshold" in payload
