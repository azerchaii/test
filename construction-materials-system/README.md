# Construction Materials Management System

Система управления строительными материалами - микросервисная архитектура для учета, закупки и уведомлений о строительных материалах.

## Архитектура

Система состоит из следующих компонентов:

- **Inventory Service** - Сервис учета материалов на складе
- **Request Service** - Сервис запросов от бригад
- **Procurement Service** - Сервис автоматических закупок
- **Notification Service** - Сервис email оповещений
- **API Gateway** - REST API для веб-приложения
- **Web Application** - Веб-интерфейс

## Технологии

- Python 3.11
- FastAPI
- gRPC (межсервисное взаимодействие)
- RabbitMQ (асинхронные события)
- SQLite (хранение данных)
- Docker & Docker Compose

## Быстрый старт

```bash
# Клонирование и запуск
git clone <repo-url>
cd construction-materials-system

# Копирование настроек
cp .env.example .env

# Запуск всех сервисов
make up

# Или без make
docker-compose up -d --build
```

## Доступные сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| Web App | http://localhost:3000 | Веб-интерфейс |
| API Gateway | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger документация |
| RabbitMQ | http://localhost:15672 | Management UI |

## Роли пользователей

- **Бригадир** - создает запросы на материалы
- **Администратор** - управляет материалами, поставщиками, видит все данные

## API Endpoints

### Аутентификация
- `POST /api/v1/auth/login` - Вход в систему
- `GET /api/v1/auth/me` - Текущий пользователь

### Материалы
- `GET /api/v1/inventory/materials` - Список материалов
- `POST /api/v1/inventory/materials` - Создать материал (admin)
- `GET /api/v1/inventory/materials/{id}/availability` - Проверить доступность

### Запросы
- `GET /api/v1/requests` - Список запросов
- `POST /api/v1/requests` - Создать запрос на материалы

### Закупки
- `GET /api/v1/procurement/orders` - Список заказов
- `GET /api/v1/procurement/suppliers` - Список поставщиков

### Оповещения
- `GET /api/v1/notifications` - История оповещений (admin)

## Разработка

```bash
# Генерация gRPC кода
make proto

# Запуск тестов
make test

# Просмотр логов
make logs

# Остановка
make down
```

## Заглушки (Stubs)

Для тестирования без реальных интеграций используются заглушки:

- **StubSupplierAdapter** - имитирует API поставщиков
- **StubEmailAdapter** - имитирует отправку email

Переключение между заглушками и реальными адаптерами:

```bash
# .env
USE_STUBS=true   # Использовать заглушки
USE_STUBS=false  # Использовать реальные адаптеры
```

## Лицензия

MIT
