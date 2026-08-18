FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web_gateway ./web_gateway
COPY routes ./routes
COPY brave ./brave

ENV PYTHONPATH=/app
ENV PORT=8000
ENV HERMES_MOCK=1

EXPOSE 8000

CMD ["python", "-m", "web_gateway.entry"]
