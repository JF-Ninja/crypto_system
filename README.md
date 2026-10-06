Микросервисная платформа для асинхронного мониторинга цен криптовалют/акций, анализа рынка и мгновенной рассылки уведомлений пользователям.

Система разделена на независимые модули (микросервисы), которые общаются друг с другом через брокер сообщений и http:

 **Основа:** 
   NginX сервер с подключением RabbiMQ, основная настройка всей системы для общего запуска.
1. **Микросервис №1 (Users):** 
   Отвечает за регистрацию, управление данными пользователя, аунтефикацию.
2. **Микросервис №2 (Assets):**
   Подключение к внешней API и парсинг актуальных данных добавленных тикеров, передаёт данные в шину данных RabbitMQ.
2. **Микросервис №3 (Alerts):**
   Получается сообщения из RabbitMQ и создаёт фоновую задачу по отслеживанию цены и отправки уведомления пользователю на почту.
3. **БД, Кэш-слой и Брокер:**
   Основные базы данных (users, alerts) - postgresql
   Кэш (users, assets, alerts) - redis
   Брокер сообщений - RabbitMQ



**Стек технологий**

* **Язык:** Python 3.12+
* **Фреймворк:** FastAPI 
* **Асинхронность:** Asyncio, aiohttp
* **База данных:** PostgreSQL
* **ORM & Миграции:** SQLAlchemy 2.0, Alembic
* **Кэширование & Очереди:** Redis, RabbitMQ 
* **Контейнеризация:** Docker, Docker Compose
* **Контроль версий:** Git

---

## Структура проекта (Текущий этап)

```text
crypto_system/
├── alerts_microservice/              
├── assets_microservice/
├── infra/
├── users_microservice/
├── docker-compose.yaml
```

---

## Как запустить 

### 1. Клонировать репозиторий
```bash
git clone https://github.com/JF-Ninja/crypto_system.git
cd crypto_system
```

### 3. Установить зависимости
```bash
uv sync
```

### 4. Запустить миграции базы данных
```bash
docker compose run --rm users-app uv run alembic upgrade head
docker compose run --rm alerts-app uv run alembic upgrade head
```

### 5. Запустить сервер разработки FastAPI
```bash
docker compose up -d --build 
```
