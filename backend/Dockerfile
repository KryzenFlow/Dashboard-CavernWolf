FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/web_gateway ./web_gateway
COPY backend/routes ./routes
COPY wsl_backend ./wsl_backend
COPY plugins ./plugins
COPY frontend ./frontend

ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0
ENV FRONTEND_DIR=/app/frontend

CMD ["python", "-m", "web_gateway.entry"]
