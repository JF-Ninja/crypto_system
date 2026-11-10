A microservice platform for asynchronous cryptocurrency and stock price monitoring, market analysis, and instant user notifications.

The system is divided into independent modules (microservices) that communicate with each other via a message broker and HTTP:

* **Core Infrastructure:** 
  Nginx server integrated with RabbitMQ, along with the main system configuration for unified deployment.
1. **Microservice #1 (Users):** 
   Handles user registration, profile management, and authentication.
2. **Microservice #2 (Assets):** 
   Connects to external APIs, parses real-time data for tracked tickers, and publishes updates to the RabbitMQ data bus.
3. **Microservice #3 (Alerts):** 
   Consumes messages from RabbitMQ and creates background tasks to track target prices and send email notifications to users.
4. **Database, Cache & Message Broker:**
   * Primary databases (`users`, `alerts`) — PostgreSQL
   * Cache (`users`, `assets`, `alerts`) — Redis
   * Message broker — RabbitMQ
5. **Monitoring & Logging:**
   Centralized catching and typing of business/system errors. Log and metric collection with visualization in Grafana.

---

## Tech Stack

* **Language:** Python 3.12+
* **Framework:** FastAPI 
* **Concurrency:** Asyncio, httpx, aio-pika
* **Database:** PostgreSQL
* **ORM & Migrations:** SQLAlchemy 2.0, Alembic
* **Caching & Queues:** Redis, RabbitMQ 
* **Containerization:** Docker, Docker Compose
* **Observability:** Grafana
* **Version Control:** Git

---

## Project Structure (Current Stage)

```text
crypto_system/
├── alerts_microservice/              
├── assets_microservice/
├── infra/
├── users_microservice/
│   └── generate_keys.py
├── docker-compose.yaml
└── README.md
```

---

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/JF-Ninja/crypto_system.git
cd crypto_system
```

### 2. Install dependencies
```bash
uv sync
```
Create `.env` files inside the microservice directories based on the `.env.example` templates.

### 3. Generate asymmetric JWT keys (RS256)
To enable authentication in `user_microservice`, you need to generate a local key pair (private and public).

Run the automatic generation script:
```bash
cd user_microservice
uv run generate_keys.py
cd ..
```

### 4. Run database migrations
```bash
docker compose run --rm users-app uv run alembic upgrade head
docker compose run --rm alerts-app uv run alembic upgrade head
```

### 5. Start the FastAPI development server
```bash
docker compose up -d --build
```
