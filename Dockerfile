FROM node:20-slim AS frontend-builder
WORKDIR /dashboard
COPY dashboard/package*.json ./
RUN npm ci || npm install
COPY dashboard/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY backend/ ./backend/
COPY --from=frontend-builder /dashboard/dist ./dashboard/dist

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
