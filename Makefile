dev:
	uv run fastapi dev app/main.py

makemigrations:
	@echo "Making migrations..."
	uv run alembic revision --autogenerate -m "$(m)"

migrate:
	@echo "Applying migrations..."
	uv run alembic upgrade head