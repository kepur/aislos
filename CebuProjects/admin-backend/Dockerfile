FROM python:3.12-slim

WORKDIR /srv/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /srv/backend/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /srv/backend
COPY admin-backend /srv/admin-backend

ENV PYTHONPATH=/srv/backend
WORKDIR /srv/admin-backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
