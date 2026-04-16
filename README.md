# FastApiSHA256

Асинхронное REST API для работы с пользователями, администраторами, счетами и транзакциями. Проект реализован по тестовому заданию Backend Python: авторизация по JWT, CRUD пользователей для администратора, просмотр счетов и транзакций, webhook для обработки внешних транзакций с SHA256-подписью.

В проекте используется FastAPI вместо Sanic. По ТЗ это допустимо, так как запрещен только Django.

## Стек

- Python 3.12
- FastAPI
- Uvicorn
- PostgreSQL 18
- SQLAlchemy async
- Alembic
- Pydantic Settings
- PyJWT
- Argon2 password hashing через `pwdlib`
- Docker Compose
- Ruff
- pytest / pytest-asyncio / httpx

## Что Реализовано

- Авторизация пользователя и администратора через `POST /api/v1/auth/login`.
- JWT Bearer authentication.
- Пользовательские endpoints:
  - получение данных о себе;
  - получение своих счетов;
  - получение своих транзакций.
- Админские endpoints:
  - создание пользователя;
  - обновление пользователя;
  - удаление пользователя;
  - получение списка пользователей со счетами.
- Администратор хранится как обычный пользователь с `is_admin=true`.
- Счет пользователя хранит `id`, `user_id`, `balance`.
- Транзакция хранит внешний `transaction_id`, `user_id`, `account_id`, `amount`.
- Webhook транзакций:
  - проверяет SHA256-подпись;
  - создает счет, если его нет;
  - сохраняет транзакцию;
  - обновляет баланс;
  - не применяет один `transaction_id` повторно;
  - запрещает `amount = 0`;
  - для отрицательных транзакций запрещает уход баланса в `<= 0`.
- Alembic-миграция создает таблицы и seed-данные.
- Dockerfile и Docker Compose.
- GitHub Actions CI для Ruff и тестов.
- Синтетические async-тесты на SQLite.

## Переменные Окружения

Пример лежит в `.env.example`.

Обязательные параметры:

```env
DB_USER=postgres
DB_PASSWORD=change-me-db-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fastapi_sha256_db
JWT_SECRET_KEY=change-me-jwt-secret-key-with-at-least-32-bytes
EXTERNAL_SECRET_KEY=change-me-external-transaction-secret
```

Необязательные параметры:

```env
ENVIRONMENT=production
DEBUG=false
APP_HOST_PORT=80
POSTGRES_HOST_PORT=2432
```

Секреты должны храниться в `.env` или переменных окружения. Файл `.env` добавлен в `.gitignore`.

## Запуск Через Docker Compose

1. Создать `.env`:

```bash
cp .env.example .env
```

2. При необходимости поменять значения `DB_PASSWORD`, `JWT_SECRET_KEY`, `EXTERNAL_SECRET_KEY`.

3. Запустить проект:

```bash
docker compose up --build
```

Docker Compose поднимает:

- `postgres` на PostgreSQL 18;
- `app` на FastAPI/Uvicorn;
- приложение доступно на `http://127.0.0.1`;
- OpenAPI docs доступны на `http://127.0.0.1/docs`.

Миграции запускаются автоматически при старте контейнера приложения.

Остановить контейнеры:

```bash
docker compose down
```

Остановить контейнеры и удалить volume с базой:

```bash
docker compose down -v
```

## Локальный Запуск Без Docker

Нужен запущенный PostgreSQL и заполненный `.env`.

Если PostgreSQL запущен на хосте:

```env
DB_HOST=localhost
DB_PORT=5432
```

Если используется PostgreSQL из Docker Compose, опубликованный наружу:

```env
DB_HOST=localhost
DB_PORT=2432
```

Установить зависимости:

```bash
poetry install
```

Применить миграции:

```bash
poetry run alembic upgrade head
```

Запустить приложение:

```bash
poetry run uvicorn app.main:app --reload
```

Локально Uvicorn по умолчанию будет доступен на `http://127.0.0.1:8000/docs`.

## Seed-Данные

Миграция создает пользователя, администратора и счет пользователя.

| Роль | Email / username | Password |
| --- | --- | --- |
| Пользователь | `user@example.com` | `user12345` |
| Администратор | `admin@example.com` | `admin12345` |

Стартовый счет:

| id | user_id | balance |
| --- | --- | --- |
| `1` | `1` | `0.0` |

## Основные Endpoints

Base:

```http
GET /
GET /healthcheck
```

Auth:

```http
POST /api/v1/auth/login
GET /api/v1/auth/is-admin
```

User:

```http
GET /api/v1/users/me
GET /api/v1/users/me/accounts
GET /api/v1/users/me/transactions
```

Admin:

```http
GET /api/v1/admin/users
POST /api/v1/admin/users
PATCH /api/v1/admin/users/{user_id}
DELETE /api/v1/admin/users/{user_id}
```

Transactions:

```http
POST /api/v1/transactions/signature
POST /api/v1/transactions/webhook
```

`/api/v1/transactions/signature` нужен для ручного тестирования webhook-запросов.

## Авторизация

Пример login:

```bash
curl -X POST http://127.0.0.1/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"admin12345"}'
```

Ответ:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

Дальше токен передается в заголовке:

```http
Authorization: Bearer <access_token>
```

## Webhook Транзакций

Webhook принимает JSON:

```json
{
  "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
  "user_id": 1,
  "account_id": 1,
  "amount": 100,
  "signature": "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"
}
```

Подпись строится как SHA256 от строки:

```text
{account_id}{amount}{transaction_id}{user_id}{EXTERNAL_SECRET_KEY}
```

Для удобства тестирования можно сначала получить подпись:

```bash
curl -X POST http://127.0.0.1/api/v1/transactions/signature \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"5eae174f-7cd0-472c-bd36-35660f00132b","user_id":1,"account_id":1,"amount":100}'
```

Потом отправить webhook:

```bash
curl -X POST http://127.0.0.1/api/v1/transactions/webhook \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"5eae174f-7cd0-472c-bd36-35660f00132b","user_id":1,"account_id":1,"amount":100,"signature":"<signature>"}'
```

## Тесты И Линтер

Запуск тестов:

```bash
poetry run pytest -q
```

Ruff:

```bash
poetry run ruff check .
poetry run ruff format --check .
```

Форматирование:

```bash
poetry run ruff format .
```

GitHub Actions запускает Ruff и pytest на `push` и `pull_request`.

## Миграции

Создать новую миграцию:

```bash
poetry run alembic revision --autogenerate -m "migration message"
```

Применить миграции:

```bash
poetry run alembic upgrade head
```

Откатить последнюю миграцию:

```bash
poetry run alembic downgrade -1
```
