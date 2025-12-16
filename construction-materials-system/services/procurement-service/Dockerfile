FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY services/procurement-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY services/procurement-service/src/ ./src/
COPY proto/ ./proto/

RUN mkdir -p /app/data

EXPOSE 50052

CMD ["python", "-m", "src.main"]
