# Environment files
touch .env .env.example

# Main application directory
mkdir app
touch app/__init__.py app/main.py

# Core functionality
mkdir app/core
touch app/core/__init__.py app/core/{base,database,config}.py

# Authentication module
mkdir app/auth
touch app/auth/__init__.py app/auth/{model,routes,schema,service}.py

# Install some standard dependencies
uv add "fastapi[standard]" "sqlalchemy[asyncio]" alembic pydantic-settings asyncpg "passlib[bcrypt]" pyjwt