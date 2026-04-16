# FastApiSHA256

Асинхронное REST API для работы с пользователями, администраторами, счетами и транзакциями.

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

## Тесты И Линтер

Запуск тестов:

```bash
poetry run pytest -vv
```

Ruff:

```bash
poetry run ruff check .
poetry run ruff format --check .
```

Форматирование:

```bash
poetry run ruff format
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
