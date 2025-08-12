FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

# Initialize DB at first run (idempotent)
CMD ["/bin/sh", "-c", "flask --app app.py db_init && gunicorn -w 2 -b 0.0.0.0:8000 app:app"]
