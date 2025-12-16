FROM python:3.11-slim

WORKDIR /app

COPY services/notification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/notification-service/src/ ./src/
COPY proto/ ./proto/

EXPOSE 50054

CMD ["python", "-m", "src.main"]
