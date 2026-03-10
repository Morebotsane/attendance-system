.PHONY: help install run test clean docker-up docker-down migrate

help:
	@echo "Hospital Attendance System - Available Commands:"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make migrate      - Run database migrations"
	@echo "  make clean        - Clean up generated files"
	@echo ""

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

run:
	cd backend && uvicorn main:app --reload

test:
	cd backend && pytest --cov=app

docker-up:
	docker-compose up -d
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/api/docs"

docker-down:
	docker-compose down

migrate:
	cd backend && alembic upgrade head

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.log" -delete
	rm -rf backend/.pytest_cache
	rm -rf backend/htmlcov
