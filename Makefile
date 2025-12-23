dev:
	uv run fastapi dev

makemigrations:
	@echo "Making migrations..."
	uv run alembic revision --autogenerate -m "$(m)"

migrate:
	@echo "Applying migrations..."
	uv run alembic upgrade head

celery-worker:
	uv run celery -A app.core.celery_app.celery_app worker --loglevel=info
