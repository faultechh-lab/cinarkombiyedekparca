import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *


required_env = {"SECRET_KEY": "DJANGO_SECRET_KEY", "SITE_DOMAIN": "SITE_DOMAIN"}
if DB_ENGINE in ("postgres", "postgresql"):
    required_env.update({name: name for name in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")})

missing_env = [label for name, label in required_env.items() if not os.environ.get(name, "").strip()]
if missing_env:
    raise ImproperlyConfigured(f"Set the production runtime variables: {', '.join(missing_env)}")

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
SITE_DOMAIN = os.environ["SITE_DOMAIN"]

ALLOWED_HOSTS = [SITE_DOMAIN, "backend", "localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = [
    f"https://{SITE_DOMAIN}",
    *config("CSRF_EXTRA_ORIGINS", default="", cast=Csv()),
]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = []

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 3600
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

STATIC_URL = "/static/"
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
