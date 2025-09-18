from datetime import datetime, time, timezone as py_timezone
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
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
        temperature_query_serializer = TemperatureQuerySerializer(data=request.query_params)
        temperature_query_serializer.is_valid(raise_exception=True)
        city_name = temperature_query_serializer.validated_data["city"]
        start = temperature_query_serializer.validated_data["start"]
        end = temperature_query_serializer.validated_data["end"]
        threshold = temperature_query_serializer.validated_data["threshold"]
        threshold_low = temperature_query_serializer.validated_data["threshold_low"]
        tzname = temperature_query_serializer.validated_data["timezone"]
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
        arr = temps.to_numpy(dtype=float)

        avg = float(np.nanmean(arr))
        idx_max = int(np.nanargmax(arr))
        idx_min = int(np.nanargmin(arr))

        avg_by_day = {
            d.isoformat(): float(np.nanmean(g["temperature_2m"].to_numpy(dtype=float)))
            for d, g in df.groupby("date")
        }
        max_row = df.loc[idx_max]
        min_row = df.loc[idx_min]

        def iso_minutes(dt: pd.Timestamp) -> str:
            return dt.to_pydatetime().replace(second=0, microsecond=0).isoformat()

        hours_above = int(np.sum(arr > float(threshold)))
        hours_below = int(np.sum(arr < float(threshold_low)))

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
        precipitation_query_serializer = PrecipitationQuerySerializer(data=request.query_params)
        precipitation_query_serializer.is_valid(raise_exception=True)
        city_name = precipitation_query_serializer.validated_data["city"]
        start = precipitation_query_serializer.validated_data["start"]
        end = precipitation_query_serializer.validated_data["end"]
        tzname = precipitation_query_serializer.validated_data["timezone"]
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
        total = float(np.nansum(daily.to_numpy(dtype=float)))
        total_by_day = {d.isoformat(): round(float(v), 1) for d, v in daily.items()}
        days_with_precip = int(np.sum(daily.to_numpy(dtype=float) > 0))

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
        summary_query_serializer = SummaryQuerySerializer(data=request.query_params)
        summary_query_serializer.is_valid(raise_exception=True)
        start = summary_query_serializer.validated_data["start"]
        end = summary_query_serializer.validated_data["end"]
        tz = ZoneInfo(summary_query_serializer.validated_data["timezone"])

        names = []
        if summary_query_serializer.validated_data.get("city"):
            names = [summary_query_serializer.validated_data["city"]]
        if summary_query_serializer.validated_data.get("cities"):
            names += [c.strip() for c in summary_query_serializer.validated_data["cities"].split(",") if c.strip()]

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

            t_arr = df["temperature_2m"].to_numpy(dtype=float)
            t_avg = round(float(np.nanmean(t_arr)), 1)
            t_max_row = df.iloc[int(np.nanargmax(t_arr))]
            t_min_row = df.iloc[int(np.nanargmin(t_arr))]

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
            dp_arr = daily_prec.to_numpy(dtype=float)
            precipitation_total = round(float(np.nansum(dp_arr)), 1)
            days_with_prec = int(np.sum(dp_arr > 0))
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
                "precipitation_total": precipitation_total,
                "days_with_precipitation": days_with_prec,
                "precipitation_max": precipitation_max,
                "temperature_max": temperature_max,
                "temperature_min": temperature_min,
            }

        return Response(result)
