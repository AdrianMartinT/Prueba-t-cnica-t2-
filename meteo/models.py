from django.db import models


class City(models.Model):
    name = models.CharField(max_length=120)
    country = models.CharField(max_length=120, blank=True, default="")
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "country"], name="uq_city_country")
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.country})" if self.country else self.name


class HourlyWeather(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="hourly")
    date_time = models.DateTimeField(db_index=True)
    temperature_2m = models.FloatField(null=True)
    precipitation = models.FloatField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["city", "date_time"],
                                    name="uq_city_datetime")
        ]
        indexes = [
            models.Index(fields=["city", "date_time"]),
        ]

    def __str__(self) -> str:
        return f"{self.city} @ {self.date_time.isoformat()}"
