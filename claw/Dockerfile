FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py ./server.py
ENV PORT=9000
CMD ["python", "server.py"]
