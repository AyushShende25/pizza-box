# PizzaBox Backend API

A production-grade, asynchronous RESTful API and real-time backend service for **PizzaBox**, a modern pizza ordering and store management platform.

Built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL**, **Redis**, **Celery**, **Razorpay**, and **AWS S3 / S3-compatible object storage**.

---

## Live Deployments

- **API**: https://api.pizzabox.fullstackprojects.dev
- **Customer Portal**: https://pizzabox.fullstackprojects.dev
- **Admin Dashboard**: https://admin.pizzabox.fullstackprojects.dev


## Related Repositories

- **Admin Frontend**: https://github.com/AyushShende25/pizza-box-admin
- **Client Frontend**: https://github.com/AyushShende25/pizza-box-client

--- 

## Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation with UV](#installation-with-uv)
  - [Environment Configuration](#environment-configuration)
  - [Database Migrations & Seeding](#database-migrations--seeding)
  - [Running the Application](#running-the-application)
- [API Reference](#-api-reference)
  - [Authentication & Users](#1-authentication--users-apiv1auth)
  - [Menu & Customization](#2-menu--catalog-apiv1menu)
  - [Cart System](#3-cart-apiv1cart)
  - [Addresses](#4-delivery-addresses-apiv1addresses)
  - [Orders & Analytics](#5-orders--sales-analytics-apiv1orders)
  - [Payments](#6-payments-apiv1payments)
  - [Store Configuration](#7-store-configuration-apiv1store-config)
  - [Uploads](#8-file-uploads-apiv1uploads)
  - [Real-Time Notifications](#9-real-time-notifications-apiv1notifications)
- [Background Workers & Real-Time Events](#-background-workers--real-time-events)
- [Database Migrations (Alembic)](#-database-migrations-alembic)
- [Error Handling & Responses](#-error-handling--responses)

---

## Overview

PizzaBox API provides complete e-commerce and operational management for a pizzeria business, handling:
- **Customer lifecycle:** Registration, verification, guest & user shopping cart, multi-address management, order checkout, and real-time live tracking.
- **Admin management:** Custom pizza creation, crust/size/topping catalog management, store availability configuration, order pipeline lifecycle, and revenue/sales analytics.
- **Asynchronous processing:** Transactional emails via Celery + FastMail, distributed real-time events via Redis Pub/Sub + WebSockets, and secure direct-to-S3 media uploads.

---

## Key Features

- **Authentication & Security:**
  - JWT Access & Refresh Token workflow with Argon2id password hashing.
  - Multi-session management with session revocation in Redis.
  - Single-use Redis tokens for email verification and forgot/reset password workflows.
  - Role-based access control (RBAC) with `CUSTOMER` and `ADMIN` privileges.

- **Menu & Catalog Engine:**
  - Dynamic pizza builder with custom configurations: base crusts, sizes with pricing multipliers, and categorized toppings (veggies, cheese, meat, sauces).
  - Search, filtering (food type, availability, featured, status), and paginated menu queries.

- **Seamless Guest & User Cart:**
  - Hybrid cart support: cookie-backed guest carts and persistent user carts.
  - Cart merging utility transferring guest basket items into authenticated customer carts upon login.

- **Order Pipeline & Sales Analytics:**
  - End-to-end status lifecycle: `PENDING` → `CONFIRMED` → `PREPARING` → `OUT_FOR_DELIVERY` → `DELIVERED` / `CANCELLED`.
  - Admin analytics endpoints for order trends, revenue stats, top-selling pizzas, and monthly sales breakdowns.

- **Payment Integration:**
  - Integrated with **Razorpay** for order creation and cryptographic HMAC-SHA256 signature verification.

- **Real-Time Push Notifications:**
  - WebSocket gateway for authenticated customers (`/ws`) and admin operations (`/ws/admin`).
  - Redis Pub/Sub backplane ensuring horizontal scalability for instant order status alerts.

- **Media Storage & Background Jobs:**
  - S3 presigned URL generation for secure, direct-to-bucket media uploads (pizza banners, topping icons).
  - Celery worker for non-blocking asynchronous email delivery.

---

## Architecture & Tech Stack

| Layer / Concern | Technology |
|---|---|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.13+) |
| **Package Manager** | [Astral uv](https://github.com/astral-sh/uv) |
| **ORM & DB Access** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async Engine) + [asyncpg](https://github.com/MagicStack/asyncpg) |
| **Database** | [PostgreSQL](https://www.postgresql.org/) |
| **Migrations** | [Alembic](https://alembic.sqlalchemy.org/) |
| **Caching, Sessions & PubSub**| [Redis](https://redis.io/) (via `redis-py` async) |
| **Background Tasks** | [Celery](https://docs.celeryq.dev/) |
| **Authentication & Crypto** | PyJWT, Pwdlib (Argon2id) |
| **Storage / Object Store** | AWS S3 via `boto3` |
| **Payment Gateway** | Razorpay SDK |
| **Emails** | `fastapi-mail` |

---

## Project Directory Structure

```text
pizza-box/
├── alembic/                      # Database migration scripts & env
│   └── versions/                 # Versioned migration files
├── app/
│   ├── address/                  # Delivery address domain (models, schemas, CRUD)
│   ├── auth/                     # Authentication, JWT, Redis token store & hashing
│   ├── cart/                     # Cart & cart items domain (guest + user handling)
│   ├── core/                     # Application config, database engine, Celery app & exceptions
│   ├── libs/                     # Third-party integrations (S3, Redis, Razorpay, FastMail)
│   ├── menu/                     # Catalog domain (Pizzas, Crusts, Sizes, Toppings)
│   ├── notifications/            # WebSocket manager, Redis pub/sub dispatcher & listener
│   ├── orders/                   # Orders domain, status transitions & analytics
│   ├── payments/                 # Razorpay checkout & signature verification
│   ├── store_config/             # Store operating status, timings & delivery settings
│   ├── uploads/                  # Presigned S3 image upload URL generation
│   ├── utils/                    # Seed script, sample data & HTML email templates
│   ├── workers/                  # Celery worker background tasks (email dispatch)
│   └── main.py                   # FastAPI app entrypoint, CORS & lifespan handlers
├── Makefile                      # Command shortcuts (dev, migrate, celery-worker)
├── pyproject.toml                # Dependencies and project metadata
└── .env.example                  # Environment variable blueprint
```

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** (recommended fast package runner & installer)
- **PostgreSQL**
- **Redis**

---

### Installation with UV

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd pizza-box
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

---

### Environment Configuration

Create an `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Populate the required configuration variables:

```env
# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
BASE_URL=http://localhost:8000
CLIENT_URL=http://localhost:5173
ADMIN_URL=http://localhost:3000

# Database & Cache
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pizza_box_db
REDIS_URL=redis://localhost:6379/0

# Celery Task Broker & Result Backend
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT Security
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_HOURS=24

# Mail Server Configuration
MAIL_TOKEN_EXPIRE_SECONDS=900
MAIL_USERNAME=your_smtp_username
MAIL_PASSWORD=your_smtp_password
MAIL_FROM=no-reply@pizzabox.local
MAIL_FROM_NAME="PizzaBox"
MAIL_PORT=587
MAIL_SERVER=smtp.mailgun.org

# Object Storage (AWS S3 or S3-compatible)
BUCKET_CUSTOM_DOMAIN=https://your-bucket-cdn-or-url
BUCKET_NAME=pizzabox-assets
BUCKET_REGION_NAME=us-east-1

# Razorpay Payment Gateway
RAZORPAY_KEY_ID=rzp_test_xxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret
```

---

### Database Migrations & Seeding

1. **Run migrations to set up the database schema:**
   ```bash
   make migrate
   # or
   uv run alembic upgrade head
   ```

2. **(Optional) Seed initial dummy data (admin/user accounts, pizzas, crusts, toppings):**
   ```bash
   uv run python -m app.utils.seed
   ```

---

### Running the Application

#### 1. Start the FastAPI Application
```bash
make dev
# or
uv run fastapi dev app/main.py
```
- API Endpoint: `http://localhost:8000`  
- Interactive Swagger UI: `http://localhost:8000/docs`  
- ReDoc Documentation: `http://localhost:8000/redoc`

#### 2. Start the Celery Worker (in a separate terminal)
```bash
make celery-worker
# or
uv run celery -A app.core.celery_app.celery_app worker --loglevel=info
```

---

## API Reference

All endpoints are mounted under `/api/v1`.

### 1. Authentication & Users (`/api/v1/auth`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/register` | Public | Register new customer account (dispatches verification email). |
| `GET` | `/verify-email` | Public | Verify user account via email token. |
| `POST` | `/login` | Public | Authenticate user; returns tokens and sets secure HTTP-only cookies. |
| `POST` | `/refresh` | Public | Generate a new access & refresh token pair. |
| `POST` | `/logout` | Authenticated | Revoke current session and clear cookies. |
| `POST` | `/logout-all` | Authenticated | Invalidate all active sessions for the user across all devices. |
| `GET` | `/me` | Authenticated | Fetch current authenticated user profile. |
| `POST` | `/resend-verification` | Public | Resend account verification email. |
| `POST` | `/forgot-password` | Public | Request password reset token via email. |
| `POST` | `/reset-password` | Public | Set new password using reset token. |

---

### 2. Menu & Catalog (`/api/v1/menu`)

#### Pizzas
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/pizzas` | Public | List pizzas with filtering (`food_type`, `is_available`, `is_featured`), sorting & pagination. |
| `POST` | `/pizzas` | Admin | Create a new pizza. |
| `GET` | `/pizzas/{pizza_id}` | Public | Get detailed pizza information. |
| `PATCH` | `/pizzas/{pizza_id}` | Admin | Update pizza details, pricing, and availability. |
| `DELETE` | `/pizzas/{pizza_id}` | Admin | Delete a pizza from the menu. |

#### Toppings, Sizes & Crusts
- **Toppings:** `GET|POST /toppings`, `GET|PATCH|DELETE /toppings/{id}` (Categorized by meat, vegetable, cheese, sauce).
- **Sizes:** `GET|POST /sizes`, `PATCH|DELETE /sizes/{id}` (Base price multipliers e.g., Regular, Medium, Large).
- **Crusts:** `GET|POST /crusts`, `GET|PATCH|DELETE /crusts/{id}` (Crust styles and extra price modifiers).

---

### 3. Cart (`/api/v1/cart`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/` | Public / Guest / User | Retrieve cart contents with calculated pricing breakdown. |
| `POST` | `/items` | Public / Guest / User | Add pizza (customized with crust, size, extra toppings) to cart. |
| `PUT` | `/items/{item_id}` | Public / Guest / User | Update item quantity in cart. |
| `DELETE` | `/items/{item_id}` | Public / Guest / User | Remove item from cart. |
| `DELETE` | `/` | Public / Guest / User | Clear all cart contents. |
| `POST` | `/merge` | Authenticated | Merge cookie-based guest cart into user's account upon login. |

---

### 4. Delivery Addresses (`/api/v1/addresses`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/` | Authenticated | Add a new delivery address (max 5 addresses per user). |
| `GET` | `/` | Authenticated | List all saved delivery addresses. |
| `PATCH` | `/{address_id}` | Authenticated | Update address details or default address status. |
| `DELETE` | `/{address_id}` | Authenticated | Remove a delivery address. |

---

### 5. Orders & Sales Analytics (`/api/v1/orders`)

#### Customer Orders
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/` | Authenticated | Create a new order (`PENDING` status) from cart/checkout data. |
| `GET` | `/my-orders` | Authenticated | Paginated order history for the current customer. |
| `GET` | `/my-orders/{order_id}` | Authenticated | Retrieve detailed order breakdown & delivery progress. |
| `POST` | `/my-orders/{order_id}/cancel` | Authenticated | Cancel order (allowed only if still in `PENDING` state). |

#### Admin Order Operations & Analytics
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/` | Admin | Search and filter all store orders with status & date filters. |
| `GET` | `/{order_id}` | Admin | Get full order details. |
| `PATCH` | `/{order_id}/status` | Admin | Advance order lifecycle (`CONFIRMED`, `PREPARING`, `OUT_FOR_DELIVERY`, `DELIVERED`). |
| `GET` | `/stats/summary` | Admin | Aggregate sales summary, revenue, status breakdown, and top-selling pizzas. |
| `GET` | `/stats/monthly-sales` | Admin | Historical monthly revenue trends. |

---

### 6. Payments (`/api/v1/payments`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/checkout/{order_id}` | Authenticated | Initialize Razorpay payment order and transaction record. |
| `POST` | `/verify` | Authenticated | Cryptographically verify Razorpay signature and mark order as `CONFIRMED`. |

---

### 7. Store Configuration (`/api/v1/store-config`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/public` | Public | Fetch store operational status, opening/closing hours, and delivery fees. |
| `GET` | `/` | Admin | Fetch complete store administrative configuration. |
| `PATCH` | `/` | Admin | Update store availability, minimum order values, taxes, and operating schedule. |

---

### 8. File Uploads (`/api/v1/uploads`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/presigned-url` | Authenticated / Admin | Generate an S3 presigned URL for direct, secure file uploads (JPEG, PNG, WEBP). |

---

### 9. Real-Time Notifications (`/api/v1/notifications`)

#### REST Endpoints
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/` | Authenticated | Fetch paginated notification history. |
| `POST` | `/mark-read` | Authenticated | Mark one or multiple notifications as read. |
| `GET` | `/unread-count` | Authenticated | Get total count of unread notifications. |
| `DELETE` | `/{notification_id}` | Authenticated | Delete a notification. |

#### WebSockets
| Protocol | Endpoint | Access | Description |
|---|---|---|---|
| `WS` | `/ws` | Authenticated | Real-time connection for live order status updates & alerts for customers. |
| `WS` | `/ws/admin` | Admin | Real-time broadcast channel for new incoming orders and system alerts. |

---

## Background Workers & Real-Time Events

1. **Celery Worker Execution:**
   - Asynchronous transactional emails (welcome emails, email verification, password reset requests) are offloaded to Celery background tasks so HTTP request cycles remain fast.
   - Run worker with:
     ```bash
     uv run celery -A app.core.celery_app.celery_app worker --loglevel=info
     ```

2. **Redis Pub/Sub WebSocket Architecture:**
   - When order statuses transition, the `NotificationDispatcher` writes events to Redis channels (`ws:user:<id>` or `ws:admin`).
   - The `NotificationListener` processes Redis messages via pattern subscription and dispatches them directly to active client WebSocket connections managed by `WSManager`.

---

## Database Migrations (Alembic)

Create a new database migration after modifying SQLAlchemy models:
```bash
make makemigrations m="description_of_change"
# or
uv run alembic revision --autogenerate -m "description_of_change"
```

Apply pending migrations:
```bash
make migrate
# or
uv run alembic upgrade head
```

Roll back the last migration:
```bash
uv run alembic downgrade -1
```

---

## Error Handling & Responses

All API errors return standardized JSON responses:

```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Pizza with id '...' not found",
  "details": null
}
```

Common error codes:
- `VALIDATION_ERROR` (422) - Invalid input payload
- `UNAUTHORIZED` / `INVALID_TOKEN` (401) - Authentication missing or expired
- `FORBIDDEN` (403) - Insufficient permissions (admin required)
- `NOT_FOUND` (404) - Resource not found
- `BAD_REQUEST` (400) - Business logic or validation violations
- `INTERNAL_SERVER_ERROR` (500) - Unhandled exceptions

