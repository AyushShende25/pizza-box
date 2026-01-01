# Pizza Box API

A comprehensive REST API for a pizza ordering platform built with FastAPI, featuring real-time notifications, payment processing, and order management.

## Live Deployments

- **Customer Portal**: https://pizzabox.ayushshende.com
- **Admin Dashboard**: https://admin.pizzabox.ayushshende.com


## Related Repositories

- **Admin Frontend**: https://github.com/AyushShende25/pizza-box-admin
- **Client Frontend**: https://github.com/AyushShende25/pizza-box-client

## Tech Stack

- **Language**: Python
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Caching/Queue**: Redis
- **Task Queue**: Celery
- **Payment Gateway**: Razorpay
- **Email**: FastAPI-Mail with Mailtrap
- **File Storage**: AWS S3 with Cloudfront
- **Authentication**: JWT with Redis
- **Password Hashing**: Passlib with bcrypt
- **Real-time**: WebSockets with Redis pub/sub
- **Migrations**: Alembic
- **Package Manager**: uv
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Deployment**: Docker Swarm on VPS with Nginx

## Features

### Core Modules

- **Authentication**: JWT-based auth with email verification, password reset, and redis based refresh token mgmt.
- **Menu Management**: CRUD operations for pizzas, toppings, sizes, and crusts with filtering and pagination
- **Cart System**: Guest and user carts with merge functionality on login
- **Address Management**: Multiple delivery addresses per user with default selection
- **Order Processing**: Order creation, status tracking, denormalized snapshots to ensure historical correctness and cancellation with validation
- **Payment Integration**: Razorpay payment gateway with signature verification
- **Notifications**: Real-time WebSocket notifications with redis pub/sub and persistent notification storage
- **File Uploads**: Pre-signed URL generation for S3 uploads

## Prerequisites

- Python 3.13 or higher
- PostgreSQL
- Redis
- uv package manager
- Docker and Docker Compose (for containerized setup)

## Local Setup

### Using uv (Development)

1. Clone the repository:
```bash
git clone https://github.com/AyushShende25/pizza-box
cd pizza-box
```

2. Install uv if not already installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies:
```bash
uv sync
```

4. Create environment file:
```bash
cp .env.example .env.local
```

5. Configure environment variables in `.env.local` (see Configuration section)

6. Run database migrations:
```bash
make migrate
```

7. Start the development server:
```bash
make dev
```

8. In a separate terminal, start the Celery worker:
```bash
make celery-worker
```

The API will be available at `http://localhost:8000`

### Using Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/AyushShende25/pizza-box
cd pizza-box
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Configure environment variables in `.env` (see Configuration section)

4. Build and start all services:
```bash
docker compose up --build
```

The following services will be available:
- API: `http://localhost:8000`
- Redis Insight: `http://localhost:8001`
- Adminer (Database UI): `http://localhost:8080`

## Configuration

Create a `.env.local` file (for uv) or `.env` file (for Docker) based on `.env.example`. Key variables include:
```bash
# use service names instead of localhost when using docker
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/pizzabox
# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Razorpay
RAZORPAY_KEY_ID=your-key-id
RAZORPAY_KEY_SECRET=your-key-secret

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
BUCKET_NAME=your-bucket-name

# Email (Mailtrap)
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password
MAIL_FROM=noreply@example.com
MAIL_PORT=587
MAIL_SERVER=sandbox.smtp.mailtrap.io

# URLs
CLIENT_URL=http://localhost:5173
ADMIN_URL=http://localhost:3000
```

Refer to `.env.example` for the complete list of configuration options.

## Available Commands (Makefile)
```bash
# Start development server
make dev

# Generate new migration
make makemigrations m="migration message"

# Apply migrations
make migrate

# Start Celery worker
make celery-worker
```

## API Documentation

Once the server is running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`

## Project Structure
```
pizza-box/
├── app/
│   ├── auth/           # Authentication
│   ├── address/        # Delivery address management
│   ├── cart/           # Shopping cart operations
│   ├── menu/           # Menu items (pizzas, toppings, sizes, crusts)
│   ├── notifications/  # Real-time notifications and events
│   ├── orders/         # Order processing and management
│   ├── payments/       # Payment gateway integration
│   ├── uploads/        # File upload handling
│   ├── core/           # Core configuration and dependencies
│   ├── libs/           # External service integrations
│   ├── utils/          # Utility functions and helpers
│   ├── workers/        # Background task definitions
│   └── main.py         # Application entry point
├── alembic/            # Database migrations
├── nginx/              # Nginx configuration
├── compose.yaml        # Docker Compose configuration
├── docker-stack.yaml   # Docker Swarm stack definition
├── Dockerfile          # Container definition
├── Makefile            # Development commands
├── pyproject.toml      # Project dependencies
└── README.md           # This file
```

## Database Migrations

Generate a new migration after model changes:
```bash
make makemigrations m="description of changes"
```

Apply pending migrations:
```bash
make migrate
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

1. **Build Stage**: 
   - Builds Docker image on push to main branch
   - Pushes image to GitHub Container Registry with latest tag and commit SHA

2. **Deploy Stage**:
   - Copies configuration files to VPS
   - Deploys application using Docker Swarm
   - Uses specific image tag from build stage

The workflow automatically triggers on push to the main branch and handles the entire deployment process.

## Production Deployment

The application is deployed on a VPS using Docker Swarm with the following architecture:

- **Nginx**: Reverse proxy with SSL termination (Let's Encrypt)
- **API Service**: FastAPI application (scalable replicas)
- **Celery Worker**: Background task processor
- **PostgreSQL**: Persistent database storage
- **Redis**: Caching and pub/sub messaging
- **Networks**: Isolated Docker network for service communication
- **Volumes**: Persistent storage for database and Redis data

The deployment uses `docker-stack.yaml` for service orchestration and supports rolling updates with zero downtime.
