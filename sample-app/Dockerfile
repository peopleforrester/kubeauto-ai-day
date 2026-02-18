# ABOUTME: Multi-stage Dockerfile for the sample Flask app.
# ABOUTME: Installs OTel auto-instrumentation and runs via opentelemetry-instrument.
FROM python:3.13-slim AS base

WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    opentelemetry-bootstrap -a install

COPY src/app.py .

EXPOSE 8080

USER 1000:1000

CMD ["opentelemetry-instrument", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
