FROM python:3.12-slim

WORKDIR /app

RUN adduser --disabled-password --no-create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# results/ is a mounted volume; it must exist and be writable before the
# volume inherits its ownership.
RUN mkdir -p /app/results && chown -R appuser:appuser /app

USER appuser

ENV HOME=/tmp \
    MPLCONFIGDIR=/tmp/matplotlib \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["gunicorn", "--workers", "3", "--timeout", "300", "--bind", "0.0.0.0:8000", "wsgi:app"]
