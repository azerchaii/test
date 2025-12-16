FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY services/inventory-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY services/inventory-service/src/ ./src/

# Copy proto files and generate gRPC code
COPY proto/ ./proto/
RUN python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./src/infrastructure/grpc_server \
    --pyi_out=./src/infrastructure/grpc_server \
    --grpc_python_out=./src/infrastructure/grpc_server \
    ./proto/inventory.proto || true

# Create data directory
RUN mkdir -p /app/data

# Create non-root user
RUN useradd --create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 50051

CMD ["python", "-m", "src.main"]
