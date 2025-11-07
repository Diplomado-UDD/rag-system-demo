#!/bin/bash
# Development helper script

set -e

case "$1" in
  start)
    echo "Starting development server..."
    uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
    ;;

  test)
    echo "Running tests..."
    uv run pytest tests/unit/ -v
    ;;

  test-all)
    echo "Running all tests..."
    uv run pytest -v
    ;;

  coverage)
    echo "Running tests with coverage..."
    uv run pytest --cov=src --cov-report=html --cov-report=term
    echo "Coverage report: htmlcov/index.html"
    ;;

  db-migrate)
    echo "Running database migrations..."
    uv run alembic upgrade head
    ;;

  db-revision)
    if [ -z "$2" ]; then
      echo "Usage: ./scripts/dev.sh db-revision 'migration message'"
      exit 1
    fi
    echo "Creating new migration..."
    uv run alembic revision --autogenerate -m "$2"
    ;;

  db-reset)
    echo "Resetting database..."
    docker-compose down postgres
    docker volume rm rag-system-demo_postgres_data || true
    docker-compose up -d postgres
    sleep 5
    uv run alembic upgrade head
    ;;

  lint)
    echo "Running linter..."
    uv run ruff check src/ tests/
    ;;

  format)
    echo "Formatting code..."
    uv run ruff format src/ tests/
    ;;

  clean)
    echo "Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    rm -rf htmlcov/ .coverage
    echo "Cleanup complete"
    ;;

  *)
    echo "Usage: ./scripts/dev.sh {start|test|test-all|coverage|db-migrate|db-revision|db-reset|lint|format|clean}"
    exit 1
    ;;
esac
