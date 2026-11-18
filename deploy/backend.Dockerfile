FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=core.production
WORKDIR /app/backend

COPY backend/requirements.txt backend/requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt \
    && groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app app

COPY backend/ ./
COPY frontend/public/assets/ /app/frontend/public/assets/
RUN mkdir -p media staticfiles && chown app:app media staticfiles

USER app
EXPOSE 8000
CMD ["sh", "-ec", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 2 --access-logfile -"]
