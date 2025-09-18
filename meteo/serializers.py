from django.conf import settings
from rest_framework import serializers


class TemperatureQuerySerializer(serializers.Serializer):
    city = serializers.CharField(required=True)
    start = serializers.DateField(required=True)
    end = serializers.DateField(required=True)
    threshold = serializers.FloatField(required=False, default=settings.DEFAULT_TEMP_THRESHOLD_HIGH)
    threshold_low = serializers.FloatField(required=False, default=settings.DEFAULT_TEMP_THRESHOLD_LOW)
    timezone = serializers.CharField(required=False, default=settings.DEFAULT_TZ)


class PrecipitationQuerySerializer(serializers.Serializer):
    city = serializers.CharField(required=True)
    start = serializers.DateField(required=True)
    end = serializers.DateField(required=True)
    timezone = serializers.CharField(required=False, default=settings.DEFAULT_TZ)


class SummaryQuerySerializer(serializers.Serializer):
    city = serializers.CharField(required=False, allow_blank=True)
    cities = serializers.CharField(required=False, allow_blank=True)
    start = serializers.DateField(required=True)
    end = serializers.DateField(required=True)
    timezone = serializers.CharField(required=False, default=settings.DEFAULT_TZ)

    def validate(self, attrs):
        if not (attrs.get("city") or attrs.get("cities")):
            raise serializers.ValidationError("You must provide 'city' or 'cities'.")
        return attrs
