from django.urls import path
from meteo.views import (
    TemperatureStatsView,
    PrecipitationStatsView,
    SummaryStatsView
)

urlpatterns = [
    path(
        "api/temperature/",
        TemperatureStatsView.as_view(),
        name="temperature-stats"
    ),
    path(
        "api/precipitation/",
        PrecipitationStatsView.as_view(),
        name="precipitation-stats"
    ),
    path(
        "api/summary/",
        SummaryStatsView.as_view(),
        name="summary-stats"
    ),
]
