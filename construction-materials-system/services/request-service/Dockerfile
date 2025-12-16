FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY services/request-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY services/request-service/src/ ./src/
COPY proto/ ./proto/

RUN mkdir -p /app/data

EXPOSE 50053

CMD ["python", "-m", "src.main"]
