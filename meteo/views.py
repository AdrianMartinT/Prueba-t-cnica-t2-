from datetime import datetime, time, timezone as py_timezone
from zoneinfo import ZoneInfo
import pandas as pd
from django.db.models import QuerySet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import City, HourlyWeather
from .serializers import (
    TemperatureQuerySerializer,
    PrecipitationQuerySerializer,
    SummaryQuerySerializer
)


class TemperatureStatsView(APIView):
    def get(self, request):
        s = TemperatureQuerySerializer(data=request.query_params)
        s.is_valid(raise_exception=True)
        city_name = s.validated_data["city"]
        start = s.validated_data["start"]
        end = s.validated_data["end"]
        threshold = s.validated_data["threshold"]
        threshold_low = s.validated_data["threshold_low"]
        tzname = s.validated_data["timezone"]
        tz = ZoneInfo(tzname)

        try:
            city = City.objects.get(name=city_name)
        except City.DoesNotExist:
            return Response({"detail": f"City not found: {city_name}"}, status=status.HTTP_404_NOT_FOUND)

        start_dt_local = datetime.combine(start, time.min).replace(tzinfo=tz)
        end_dt_local = datetime.combine(end, time.max).replace(tzinfo=tz)
        start_dt_utc = start_dt_local.astimezone(py_timezone.utc)
        end_dt_utc = end_dt_local.astimezone(py_timezone.utc)

        qs: QuerySet[HourlyWeather] = (
            HourlyWeather.objects
            .filter(city=city, date_time__range=(start_dt_utc, end_dt_utc))
            .values("date_time", "temperature_2m")
        )
        rows = list(qs)
        if not rows:
            return Response({"temperature": {}}, status=status.HTTP_200_OK)

        df = pd.DataFrame(rows)
        df["date_time"] = pd.to_datetime(df["date_time"], utc=True).dt.tz_convert(tz)
        df["date"] = df["date_time"].dt.date
        temps = df["temperature_2m"].astype("float")

        avg = float(temps.mean())
        avg_by_day = {d.isoformat(): float(g["temperature_2m"].mean())
                      for d, g in df.groupby("date")}

        idx_max = temps.idxmax()
        idx_min = temps.idxmin()
        max_row = df.loc[idx_max]
        min_row = df.loc[idx_min]

        def iso_minutes(dt: pd.Timestamp) -> str:
            return dt.to_pydatetime().replace(second=0, microsecond=0).isoformat()

        hours_above = int((temps > float(threshold)).sum())
        hours_below = int((temps < float(threshold_low)).sum())

        payload = {
            "temperature": {
                "average": round(avg, 1),
                "average_by_day": {k: round(v, 1) for k, v in avg_by_day.items()},
                "max": {
                    "value": round(float(max_row["temperature_2m"]), 1),
                    "date_time": iso_minutes(max_row["date_time"]),
                },
                "min": {
                    "value": round(float(min_row["temperature_2m"]), 1),
                    "date_time": iso_minutes(min_row["date_time"]),
                },
                "hours_above_threshold": hours_above,
                "hours_below_threshold": hours_below,
            }
        }
        return Response(payload)


class PrecipitationStatsView(APIView):
    def get(self, request):
        s = PrecipitationQuerySerializer(data=request.query_params)
        s.is_valid(raise_exception=True)
        city_name = s.validated_data["city"]
        start = s.validated_data["start"]
        end = s.validated_data["end"]
        tzname = s.validated_data["timezone"]
        tz = ZoneInfo(tzname)

        try:
            city = City.objects.get(name__iexact=city_name)
        except City.DoesNotExist:
            return Response({"detail": f"City not found: {city_name}"}, status=status.HTTP_404_NOT_FOUND)

        start_dt_utc = datetime.combine(start, time.min).replace(tzinfo=tz).astimezone(py_timezone.utc)
        end_dt_utc = datetime.combine(end, time.max).replace(tzinfo=tz).astimezone(py_timezone.utc)

        rows = list(
            HourlyWeather.objects
            .filter(city=city, date_time__range=(start_dt_utc, end_dt_utc))
            .values("date_time", "precipitation")
        )
        if not rows:
            return Response({"precipitation": {}}, status=status.HTTP_200_OK)

        df = pd.DataFrame(rows)
        df["date_time"] = pd.to_datetime(df["date_time"], utc=True).dt.tz_convert(tz)
        df["date"] = df["date_time"].dt.date
        df["precipitation"] = df["precipitation"].astype("float").fillna(0.0)

        daily = df.groupby("date")["precipitation"].sum()
        total = float(daily.sum())
        total_by_day = {d.isoformat(): round(float(v), 1) for d, v in daily.items()}
        days_with_precip = int((daily > 0).sum())

        max_date = daily.idxmax()
        max_value = float(daily.loc[max_date]) if len(daily) else 0.0

        num_days = (end - start).days + 1
        average = total / num_days if num_days > 0 else 0.0

        payload = {
            "precipitation": {
                "total": round(total, 1),
                "total_by_day": total_by_day,
                "days_with_precipitation": days_with_precip,
                "max": {
                    "value": round(max_value, 1),
                    "date": max_date.isoformat(),
                },
                "average": round(average, 2),
            }
        }
        return Response(payload)


class SummaryStatsView(APIView):
    def get(self, request):
        s = SummaryQuerySerializer(data=request.query_params)
        s.is_valid(raise_exception=True)
        start = s.validated_data["start"]
        end = s.validated_data["end"]
        tz = ZoneInfo(s.validated_data["timezone"])

        names = []
        if s.validated_data.get("city"):
            names = [s.validated_data["city"]]
        if s.validated_data.get("cities"):
            names += [c.strip() for c in s.validated_data["cities"].split(",") if c.strip()]

        start_utc = datetime.combine(start, time.min).replace(tzinfo=tz).astimezone(py_timezone.utc)
        end_utc = datetime.combine(end, time.max).replace(tzinfo=tz).astimezone(py_timezone.utc)

        result = {}
        for name in names:
            try:
                city = City.objects.get(name__iexact=name)
            except City.DoesNotExist:
                result[name] = {"info": f"City not found: {name}"}
                continue

            qs = (HourlyWeather.objects
                  .filter(city=city, date_time__range=(start_utc, end_utc))
                  .values("date_time", "temperature_2m", "precipitation"))
            rows = list(qs)
            if not rows:
                result[city.name] = {
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "temperature_average": None,
                    "precipitation_total": 0.0,
                    "days_with_precipitation": 0,
                    "precipitation_max": None,
                    "temperature_max": None,
                    "temperature_min": None,
                }
                continue

            df = pd.DataFrame(rows)
            df["date_time"] = pd.to_datetime(df["date_time"], utc=True).dt.tz_convert(tz)
            df["date"] = df["date_time"].dt.date
            df["temperature_2m"] = df["temperature_2m"].astype("float")
            df["precipitation"] = df["precipitation"].astype("float").fillna(0.0)

            t_avg = round(float(df["temperature_2m"].mean()), 1)
            t_max_row = df.loc[df["temperature_2m"].idxmax()]
            t_min_row = df.loc[df["temperature_2m"].idxmin()]

            def fmt_dt_no_seconds(ts: pd.Timestamp) -> str:
                return ts.to_pydatetime().replace(second=0,
                                                  microsecond=0
                                                  ).strftime("%Y-%m-%dT%H:%M")

            temperature_max = {
                "date": fmt_dt_no_seconds(t_max_row["date_time"]),
                "value": round(float(t_max_row["temperature_2m"]), 1),
            }
            temperature_min = {
                "date": fmt_dt_no_seconds(t_min_row["date_time"]),
                "value": round(float(t_min_row["temperature_2m"]), 1),
            }

            daily_prec = df.groupby("date")["precipitation"].sum()
            p_total = round(float(daily_prec.sum()), 1)
            days_with_prec = int((daily_prec > 0).sum())
            if len(daily_prec):
                p_max_date = daily_prec.idxmax()
                p_max_value = round(float(daily_prec.loc[p_max_date]), 1)
                precipitation_max = {"date": p_max_date.isoformat(),
                                     "value": p_max_value}
            else:
                precipitation_max = None

            result[city.name] = {
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "temperature_average": t_avg,
                "precipitation_total": p_total,
                "days_with_precipitation": days_with_prec,
                "precipitation_max": precipitation_max,
                "temperature_max": temperature_max,
                "temperature_min": temperature_min,
            }

        return Response(result)
