# FastApiSHA256

Асинхронное REST API для пользователей, администраторов, счетов и платежных вебхуков.

Проект выполняется по тестовому заданию Backend Python. В ТЗ рекомендован Sanic, но допускается любой веб-фреймворк кроме Django. В проекте выбран **FastAPI**, потому что он хорошо подходит для асинхронного REST API, дает OpenAPI-документацию из коробки и удобно работает с Pydantic-схемами.

## Текущий статус

Проект находится на стадии базового каркаса и доменных моделей.

Уже сделано:

- подключен FastAPI entrypoint: `app/main.py`;
- добавлены основные зависимости через Poetry;
- настроен Ruff в `pyproject.toml`;
- добавлен конфиг приложения через `pydantic-settings`;
- обязательные секреты и настройки БД читаются из `.env` или переменных окружения;
- добавлен `EXTERNAL_SECRET_KEY` для проверки подписи платежных вебхуков;
- настроена асинхронная SQLAlchemy-сессия;
- реализована базовая ORM-модель `Users`;
- администратор выбран как пользователь с `is_admin=True`, без отдельной таблицы `admins`;
- реализована ORM-модель `Accounts`;
- реализована ORM-модель `Transactions` для платежей/пополнений;
- добавлена Alembic-конфигурация под async SQLAlchemy;
- создана первая миграция `5710458efe00`;
- в миграции созданы тестовый пользователь, тестовый администратор и счет пользователя;
- добавлен security-layer для хеширования паролей и JWT;
- реализован `POST /api/v1/auth/login`;
- реализован `GET /api/v1/auth/is-admin` для проверки флага администратора;
- добавлены auth dependencies `get_current_user` и `get_current_admin`;
- добавлен пример webhook payload в `example.json`;
- текущие модели проходят Ruff и компилируются.

Пока не сделано:

- нет Pydantic-схем для профилей, счетов, транзакций и webhook;
- нет пользовательских, админских и платежных REST-роутов, кроме login и проверки is-admin;
- нет сервиса обработки webhook;
- нет проверки SHA256-подписи;
- нет атомарного начисления баланса;
- нет Dockerfile и `docker-compose.yml`;
- нет автоматических тестов;
- нет `.gitignore`, поэтому перед git-инициализацией нужно исключить `.env`, `logs/`, `__pycache__/`, `.ruff_cache/`, `.pytest_cache/`.

## Сверка с ТЗ

| Этап | Статус | Комментарий |
| --- | --- | --- |
| Асинхронное REST API | Частично | FastAPI подключен, но REST-роуты из ТЗ еще не реализованы. |
| PostgreSQL | Частично | Есть async SQLAlchemy config и миграция; Docker Compose еще не готов. |
| SQLAlchemy | Частично | Есть `Base`, session, модели и Alembic migration flow. |
| Docker Compose | Не готово | Нужно добавить сервисы `postgres` и `app`. |
| Пользователь | Частично | Модель и login есть, но нет user API. |
| Администратор | Частично | Представлен через `Users.is_admin`, login есть, но нет admin API. |
| Счет | Готова модель | `Accounts` имеет `id`, `user_id`, `balance` и связи. |
| Платеж | Готова модель | `Transactions` хранит `transaction_id`, `user_id`, `account_id`, `amount`, `created_at`. |
| Уникальность платежа | Частично | В модели и миграции `transaction_id` является primary key; нужна обработка конфликтов в webhook-сервисе. |
| SHA256 подпись webhook | Не готово | Есть `EXTERNAL_SECRET_KEY`, но нет функции проверки и endpoint. |
| Стартовые данные в миграции | Готово | Миграция создает пользователя, счет и админа. |
| Auth login | Готово | `POST /api/v1/auth/login` принимает `username/password` и возвращает bearer token. |
| Auth admin check | Готово | `GET /api/v1/auth/is-admin` проверяет текущего пользователя по Bearer token и возвращает `is_admin`. |
| Инструкция запуска | Частично | Локальные команды актуальны; Docker-инструкция будет актуальна после Docker Compose. |

## Стек

Runtime:

- Python 3.12
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy 2.x async
- asyncpg
- Alembic
- Pydantic Settings

Auth/security:

- PyJWT
- pwdlib с Argon2
- SHA256 для проверки подписи webhook payload

Качество и тесты:

- Ruff
- pytest
- pytest-asyncio
- httpx
- pytest-cov

Инфраструктура:

- Docker
- Docker Compose
- PostgreSQL service
- application service

## Актуальная структура

Текущая структура проекта:

```text
.
├── app
│   ├── api
│   │   ├── deps.py
│   │   └── v1
│   │       ├── auth.py
│   │       └── router.py
│   ├── core
│   │   ├── config.py
│   │   └── security.py
│   ├── db
│   │   └── session.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── accounts.py
│   │   ├── base.py
│   │   ├── transactions.py
│   │   └── users.py
│   ├── schemas
│   │   └── auth.py
│   ├── services
│   │   └── auth.py
│   └── main.py
├── alembic
│   └── versions
├── example.json
├── poetry.lock
├── pyproject.toml
├── README.md
└── test_main.http
```

Целевая структура после завершения основной реализации:

```text
.
├── app
│   ├── api
│   │   ├── deps.py
│   │   └── v1
│   │       ├── auth.py
│   │       ├── payments.py
│   │       ├── router.py
│   │       └── users.py
│   ├── core
│   │   ├── config.py
│   │   └── security.py
│   ├── db
│   │   └── session.py
│   ├── models
│   ├── schemas
│   ├── services
│   └── main.py
├── alembic
│   └── versions
├── tests
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Модель данных

### Users

Файл: `app/models/users.py`.

Пользователь и администратор хранятся в одной таблице `users`. Администратор определяется флагом `is_admin=True`.

Текущие поля:

- `id` - integer primary key;
- `email` - уникальный email, индексируется;
- `full_name` - полное имя пользователя или администратора;
- `hashed_password` - хеш пароля;
- `is_active` - флаг активности;
- `is_admin` - флаг админских прав;
- `created_at` - timestamp создания;
- `updated_at` - timestamp обновления;
- `last_login_at` - timestamp последнего входа, nullable.

Связи:

- один пользователь имеет много счетов: `Users.accounts`;
- один пользователь имеет много транзакций: `Users.transactions`.

### Accounts

Файл: `app/models/accounts.py`.

Счет пользователя.

Текущие поля:

- `id` - integer primary key;
- `user_id` - foreign key на `users.id`;
- `balance` - баланс счета в `Float`.

Связи:

- один счет принадлежит одному пользователю: `Accounts.user`;
- один счет имеет много транзакций: `Accounts.transactions`.

Примечание: для production-финансов обычно лучше `Decimal` + PostgreSQL `Numeric`, но сейчас модель следует текущему требованию проекта использовать `float`.

### Transactions

Файл: `app/models/transactions.py`.

`Transactions` соответствует платежу/пополнению баланса из ТЗ.

Текущие поля:

- `transaction_id` - UUID-идентификатор транзакции во внешней системе, primary key, длина 36 символов;
- `user_id` - foreign key на `users.id`;
- `account_id` - foreign key на `accounts.id`;
- `amount` - сумма пополнения;
- `created_at` - timestamp создания.

Ограничения:

- `transaction_id` уникален как primary key;
- `amount > 0`;
- `user_id` индексируется;
- `account_id` индексируется.

Связи:

- одна транзакция принадлежит одному пользователю: `Transactions.user`;
- одна транзакция относится к одному счету: `Transactions.account`.

`signature` не хранится в таблице. Она нужна только для проверки входящего webhook payload.

## Кардинальность связей

Текущие связи соответствуют такой схеме:

```text
User 1 -> X Accounts
User 1 -> X Transactions

Account X -> 1 User
Account 1 -> X Transactions

Transaction X -> 1 User
Transaction X -> 1 Account
```

Физические связи в БД:

```text
accounts.user_id -> users.id
transactions.user_id -> users.id
transactions.account_id -> accounts.id
```

При обработке webhook нужно дополнительно проверять бизнес-инвариант: счет `account_id` должен принадлежать пользователю `user_id`.

## Конфигурация

Конфигурация находится в `app/core/config.py`.

Обязательные параметры:

- `JWT_SECRET_KEY`;
- `EXTERNAL_SECRET_KEY`;
- либо `DATABASE_URL`, либо полный набор:
  - `DB_USER`;
  - `DB_PASSWORD`;
  - `DB_HOST`;
  - `DB_PORT`;
  - `DB_NAME`.

Необязательные параметры с default-значениями:

- `APP_NAME=FastAPI SHA256`;
- `ENVIRONMENT=production`;
- `DEBUG=false`;
- `JWT_ALGORITHM=HS256`;
- `ACCESS_TOKEN_EXPIRE_MINUTES=1440`.

Пример `.env.example`:

```env
# App
ENVIRONMENT=production
DEBUG=false

# Database
DB_USER=postgres
DB_PASSWORD=change-me-db-password
DB_HOST=host.docker.internal
DB_PORT=2432
DB_NAME=fastapi_sha256_db

# Docker Compose host ports
POSTGRES_HOST_PORT=2432
APP_HOST_PORT=80

# Authorization
JWT_SECRET_KEY=change-me-jwt-secret-key-with-at-least-32-bytes

# External transaction system
EXTERNAL_SECRET_KEY=change-me-external-transaction-secret
```

Для Docker Compose удобнее передать `DATABASE_URL` или заменить `DB_HOST` на имя сервиса PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/fastapi_sha256_db
```

Если `.env` отсутствует, приложение логирует ошибку. При этом обязательные параметры все равно должны быть переданы через переменные окружения, что важно для Docker Compose.

## Alembic

Alembic настроен в async-режиме под SQLAlchemy URL вида `postgresql+asyncpg://...`.

Файлы:

- `alembic.ini` - основной конфиг Alembic;
- `alembic/env.py` - подключает `settings.database_url` и `Base.metadata`;
- `alembic/script.py.mako` - шаблон новых миграций;
- `alembic/versions/20260415_5710458efe00_initial.py` - первая миграция.

Первая миграция создает:

- `users`;
- `accounts`;
- `transactions`;
- `alembic_version`.

Также миграция добавляет seed-данные. Полная таблица находится в разделе
`Миграционные Тестовые Данные`.

Пароли сохранены в БД как Argon2-хеши.

Команды:

```bash
poetry run alembic current
poetry run alembic upgrade head
poetry run alembic downgrade base
poetry run alembic check
```

## API, Которое Нужно Реализовать

Рекомендуемый префикс: `/api/v1`.

### Auth

Авторизация уже реализована для обычных пользователей и администраторов.
Администратор не хранится в отдельной таблице: это запись в `users` с
`is_admin=true`.

```http
POST /api/v1/auth/login
```

Назначение:

- проверить `username` и `password`;
- найти пользователя по email;
- проверить Argon2-хеш пароля;
- обновить `last_login_at`;
- вернуть JWT access token.

Тело запроса:

```json
{
  "username": "user@example.com",
  "password": "user12345"
}
```

`username` трактуется как email пользователя. Это сделано для совместимости с
типовым login payload, хотя в ТЗ авторизация описана как `email/password`.

Успешный ответ `200 OK`:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

Токен содержит `sub=user_id`, `email` и `is_admin`.

Ошибка авторизации `401 Unauthorized`:

```json
{
  "detail": "Incorrect username or password"
}
```

Тестовые учетные данные из миграции:

| Роль | username | password |
| --- | --- | --- |
| Пользователь | `user@example.com` | `user12345` |
| Администратор | `admin@example.com` | `admin12345` |

Пример `curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"user12345"}'
```

### Auth: Проверка Админских Прав

Endpoint уже реализован и доступен любому авторизованному пользователю.
Он не выдает админский доступ сам по себе, а только возвращает актуальное
значение `users.is_admin` из базы данных.

```http
GET /api/v1/auth/is-admin
Authorization: Bearer <access_token>
```

Назначение:

- проверить Bearer token;
- найти активного пользователя по `sub` из JWT;
- вернуть `user_id`, `email` и флаг `is_admin`.

Успешный ответ обычного пользователя `200 OK`:

```json
{
  "user_id": 1,
  "email": "user@example.com",
  "is_admin": false
}
```

Успешный ответ администратора `200 OK`:

```json
{
  "user_id": 2,
  "email": "admin@example.com",
  "is_admin": true
}
```

Ошибка авторизации `401 Unauthorized`:

```json
{
  "detail": "Could not validate credentials"
}
```

Пример `curl`:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"admin12345"}' \
  | python -c 'import json, sys; print(json.load(sys.stdin)["access_token"])')

curl http://127.0.0.1:8000/api/v1/auth/is-admin \
  -H "Authorization: Bearer ${TOKEN}"
```

### User

Требуется JWT пользователя.

```http
GET /api/v1/users/me
GET /api/v1/users/me/accounts
GET /api/v1/users/me/payments
```

`GET /api/v1/users/me` должен вернуть:

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Test User"
}
```

### Admin

Требуется JWT пользователя с `is_admin=True`.

```http
GET    /api/v1/admin/me
POST   /api/v1/admin/users
GET    /api/v1/admin/users
PATCH  /api/v1/admin/users/{user_id}
DELETE /api/v1/admin/users/{user_id}
```

Список пользователей должен включать счета и балансы:

```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Test User",
    "accounts": [
      {
        "id": 1,
        "balance": 100.0
      }
    ]
  }
]
```

### Payment Webhook

Публичный endpoint, но с обязательной проверкой подписи.

```http
POST /api/v1/payments/webhook
```

Пример payload есть в `example.json`:

```json
{
  "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
  "user_id": 1,
  "account_id": 1,
  "amount": 100,
  "signature": "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"
}
```

Подпись формируется через SHA256 от строки:

```text
{account_id}{amount}{transaction_id}{user_id}{secret_key}
```

Для проекта имя секрета в конфиге:

```text
EXTERNAL_SECRET_KEY
```

Порядок ключей без `signature`:

```text
account_id
amount
transaction_id
user_id
```

Пример функции:

```python
import hashlib


def build_payment_signature(
    *,
    account_id: int,
    amount: str,
    transaction_id: str,
    user_id: int,
    secret_key: str,
) -> str:
    raw = f"{account_id}{amount}{transaction_id}{user_id}{secret_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
```

Важно: нужно стабильно договориться о строковом представлении `amount`. Для примера из ТЗ в подпись попадает `100`, а не `100.0` и не `100.00`.

## Алгоритм Webhook

1. Принять JSON через Pydantic-схему.
2. Пересчитать SHA256-подпись на сервере.
3. Сравнить подписи через `hmac.compare_digest`.
4. Проверить, что пользователь существует.
5. Найти счет по `account_id` и `user_id`.
6. Если счета нет, создать счет для пользователя.
7. Открыть транзакцию БД.
8. Проверить, есть ли `Transactions.transaction_id`.
9. Если транзакция уже есть, не начислять баланс повторно.
10. Создать `Transactions`.
11. Увеличить `Accounts.balance` на `amount`.
12. Зафиксировать транзакцию БД.

Уникальность должна защищаться и кодом, и БД:

```text
PRIMARY KEY (transaction_id)
```

## План Работ

1. Завершить модели:
   - заменить SQLAlchemy timestamp-аннотации на Python `datetime`, если хочется более строгой типизации;
   - принять окончательное решение по `Float` vs `Numeric` для денег.

2. Реализовать оставшиеся schemas:
   - user/admin profile;
   - account response;
   - transaction/payment response;
   - webhook request/response.

3. Реализовать REST API:
   - пользовательские endpoints;
   - админские endpoints;
   - webhook endpoint.

4. Реализовать payment service:
   - подпись;
   - idempotency;
   - создание счета при отсутствии;
   - атомарное начисление баланса.

5. Добавить Docker:
   - `Dockerfile`;
   - `docker-compose.yml`;
   - сервис `postgres`;
   - сервис `app`;
   - healthcheck БД;
   - запуск миграций перед стартом приложения.

6. Добавить тесты:
   - login пользователя;
   - login админа;
   - пользователь видит только свои данные;
   - админ управляет пользователями;
   - webhook отклоняет неверную подпись;
   - webhook создает счет при отсутствии;
   - повторный `transaction_id` не начисляет баланс второй раз.

7. Обновить Docker-инструкцию после появления Docker Compose.

## Миграционные Тестовые Данные

В первой миграции уже создаются:

Пользователи:

| id | email | password | full_name | is_admin | Назначение |
| --- | --- | --- | --- | --- | --- |
| 1 | `user@example.com` | `user12345` | `Test User` | `false` | Тестовый пользователь |
| 2 | `admin@example.com` | `admin12345` | `Test Admin` | `true` | Тестовый администратор |

Счета:

| id | user_id | balance | Назначение |
| --- | --- | --- | --- |
| 1 | 1 | `0.0` | Счет тестового пользователя |

Пароли в БД сохраняются как Argon2-хеши. Plaintext-пароли выше нужны только
для ручной проверки авторизации после реализации auth endpoints.

SQL-смысл seed-данных:

Пользователь:

```text
id: 1
email: user@example.com
password: user12345
full_name: Test User
is_admin: false
```

Счет пользователя:

```text
id: 1
user_id: 1
balance: 0.0
```

Администратор:

```text
id: 2
email: admin@example.com
password: admin12345
full_name: Test Admin
is_admin: true
```

## Запуск Сейчас

Текущий минимальный запуск без Docker:

```bash
poetry install
cp .env.example .env
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

Сейчас приложение поднимает базовые и auth endpoints:

```http
GET /
GET /healthcheck
POST /api/v1/auth/login
GET /api/v1/auth/is-admin
```

OpenAPI:

```text
http://localhost:8000/docs
```

Важно: из-за обязательных настроек приложение требует `.env` или переменные окружения с секретами и настройками БД даже до появления реальных API-роутов.

## Запуск Через Docker Compose

Docker Compose поднимает приложение на 80 порту и PostgreSQL 18:

```bash
cp .env.example .env
docker compose up --build
```

Миграции запускаются автоматически при старте контейнера приложения.

## Лучшие Практики

- Пароли хранить только в виде хеша.
- Секреты не коммитить в репозиторий.
- Для подписи использовать `EXTERNAL_SECRET_KEY`.
- Подписи сравнивать через `hmac.compare_digest`.
- Обработку webhook делать в транзакции БД.
- `transaction_id` должен быть primary key на уровне БД.
- Пользователь не должен видеть чужие счета и платежи.
- Админские endpoints должны проверять `Users.is_admin`.
- SQLAlchemy-модели не отдавать из API напрямую, использовать Pydantic-схемы.
- Перед git-инициализацией добавить `.gitignore`.

## Проверки

Актуальные команды качества:

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run python -m compileall app
```

Тесты пока не добавлены. После появления `tests/` основной командой будет:

```bash
poetry run pytest
```

## Критерии Готовности

Проект будет готов по ТЗ, когда:

- пользователь и админ авторизуются по email/password;
- пользователь получает свои данные, счета и платежи;
- админ получает свои данные;
- админ создает, обновляет, удаляет пользователей;
- админ получает список пользователей со счетами;
- webhook проверяет SHA256-подпись;
- webhook создает счет при отсутствии;
- webhook сохраняет уникальную транзакцию;
- повторный `transaction_id` не начисляет баланс второй раз;
- Docker Compose поднимает PostgreSQL и приложение;
- README содержит актуальные команды запуска и дефолтные email/password;
- автоматические тесты проходят локально.
