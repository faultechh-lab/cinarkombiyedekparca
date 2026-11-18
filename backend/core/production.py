import os

from .settings import *


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
