FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_DEBUG=False PORT=3000
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt && useradd --create-home creo
COPY --chown=creo:creo . .
RUN mkdir -p /app/media /app/private_media /app/staticfiles && chown -R creo:creo /app
USER creo
EXPOSE 3000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python scripts/serve.py"]
