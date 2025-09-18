import os
from dotenv import load_dotenv
load_dotenv()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "openmeteo_db",
        "USER": "openmeteo_user",
        "PASSWORD": "change_me",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Madrid")
USE_TZ = True
OPEN_METEO_GEOCODE_URL = os.getenv(
    "OPEN_METEO_GEOCODE_URL",
    "https://geocoding-api.open-meteo.com/v1/search",
)
OPEN_METEO_ARCHIVE_URL = os.getenv(
    "OPEN_METEO_ARCHIVE_URL",
    "https://archive-api.open-meteo.com/v1/archive",
)
REQUEST_TIMEOUT_SECS = float(os.getenv("REQUEST_TIMEOUT_SECS", "20"))
DEFAULT_TZ = os.getenv("DEFAULT_TZ", TIME_ZONE)
DEFAULT_TEMP_THRESHOLD_HIGH = float(os.getenv("DEFAULT_TEMP_THRESHOLD_HIGH", "30.0"))
DEFAULT_TEMP_THRESHOLD_LOW = float(os.getenv("DEFAULT_TEMP_THRESHOLD_LOW", "0.0"))

SECRET_KEY = "dev-only-change-me"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "meteo",
    "rest_framework"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
STATIC_URL = "/static/"
ROOT_URLCONF = "openmeteo_api.urls"
