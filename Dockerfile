FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario sin privilegios; /app/instance guarda la base SQLite
RUN useradd --create-home appuser \
    && mkdir -p /app/instance \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# seed.py solo siembra si la base está vacía
CMD ["sh", "-c", "python seed.py && gunicorn --bind 0.0.0.0:${PORT:-8000} run:app"]
