.PHONY: help build up down logs test proto clean init

help:
	@echo "Construction Materials System - Available commands:"
	@echo ""
	@echo "  make init     - Initialize project (copy .env, generate proto)"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - View logs from all services"
	@echo "  make test     - Run all tests"
	@echo "  make proto    - Generate gRPC code from proto files"
	@echo "  make clean    - Remove all containers and volumes"
	@echo ""

init:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file"; fi
	@make proto
	@echo "Project initialized!"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "Services are starting..."
	@echo ""
	@echo "  Web App:     http://localhost:3000"
	@echo "  API Gateway: http://localhost:8000"
	@echo "  API Docs:    http://localhost:8000/docs"
	@echo "  RabbitMQ:    http://localhost:15672"
	@echo ""

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	docker-compose run --rm api-gateway pytest tests/ -v --cov=src

proto:
	@echo "Generating gRPC code from proto files..."
	@for service in inventory procurement requests notification; do \
		mkdir -p services/$${service}-service/src/infrastructure/grpc/generated; \
		python -m grpc_tools.protoc \
			-I./proto \
			--python_out=./services/$${service}-service/src/infrastructure/grpc/generated \
			--pyi_out=./services/$${service}-service/src/infrastructure/grpc/generated \
			--grpc_python_out=./services/$${service}-service/src/infrastructure/grpc/generated \
			./proto/*.proto 2>/dev/null || true; \
	done
	@mkdir -p services/api-gateway/src/grpc_clients/generated
	@python -m grpc_tools.protoc \
		-I./proto \
		--python_out=./services/api-gateway/src/grpc_clients/generated \
		--pyi_out=./services/api-gateway/src/grpc_clients/generated \
		--grpc_python_out=./services/api-gateway/src/grpc_clients/generated \
		./proto/*.proto 2>/dev/null || true
	@echo "Done!"

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
