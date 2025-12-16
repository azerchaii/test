FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY services/api-gateway/src/ ./src/

# Copy proto files for gRPC client generation
COPY proto/ ./proto/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
