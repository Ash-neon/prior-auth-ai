# Makefile for Prior Authorization AI Platform
# Usage: make [target]

.PHONY: help setup dev backend frontend worker stop clean test lint format db-migrate db-reset docker-build docker-push docs

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Prior Authorization AI Platform - Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ==================== Setup ====================

setup: ## Initial project setup
	@echo "$(BLUE)Setting up project...$(NC)"
	@cp -n .env.example .env || true
	@cp -n backend/.env.example backend/.env || true
	@cp -n frontend/.env.local.example frontend/.env.local || true
	@echo "$(GREEN)✓ Environment files created$(NC)"
	@echo "$(YELLOW)! Please edit .env files with your configuration$(NC)"
	@echo ""
	@echo "$(BLUE)Creating Python virtual environment...$(NC)"
	@cd backend && python3 -m venv venv
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@echo ""
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@cd backend && . venv/bin/activate && pip install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"
	@echo ""
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@cd frontend && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"
	@echo ""
	@echo "$(GREEN)✓ Setup complete! Run 'make dev' to start development environment$(NC)"

install-backend: ## Install backend Python dependencies
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@cd backend && . venv/bin/activate && pip install -r requirements.txt
	@echo "$(GREEN)✓ Done$(NC)"

install-frontend: ## Install frontend Node.js dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@cd frontend && npm install
	@echo "$(GREEN)✓ Done$(NC)"

# ==================== Development ====================

dev: ## Start full development environment (Docker)
	@echo "$(BLUE)Starting development environment...$(NC)"
	@docker-compose up

dev-detached: ## Start development environment in background
	@echo "$(BLUE)Starting development environment (detached)...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@docker-compose ps

backend: ## Run backend server (local)
	@echo "$(BLUE)Starting backend server...$(NC)"
	@cd backend && . venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Run frontend dev server (local)
	@echo "$(BLUE)Starting frontend server...$(NC)"
	@cd frontend && npm run dev

worker: ## Run Celery worker (local)
	@echo "$(BLUE)Starting Celery worker...$(NC)"
	@cd backend && . venv/bin/activate && celery -A workers.celery_app worker --loglevel=info

logs: ## Show logs from all services
	@docker-compose logs -f

logs-backend: ## Show backend logs only
	@docker-compose logs -f backend

logs-frontend: ## Show frontend logs only
	@docker-compose logs -f frontend

logs-postgres: ## Show PostgreSQL logs
	@docker-compose logs -f postgres

ps: ## Show running services
	@docker-compose ps

stop: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ All services stopped$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting all services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)✓ All services restarted$(NC)"

# ==================== Database ====================

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@cd backend && . venv/bin/activate && alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

db-rollback: ## Rollback last migration
	@echo "$(BLUE)Rolling back last migration...$(NC)"
	@cd backend && . venv/bin/activate && alembic downgrade -1
	@echo "$(GREEN)✓ Rollback complete$(NC)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)⚠ WARNING: This will delete ALL data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(BLUE)Resetting database...$(NC)"
	@cd backend && . venv/bin/activate && alembic downgrade base
	@cd backend && . venv/bin/activate && alembic upgrade head
	@echo "$(GREEN)✓ Database reset$(NC)"

db-seed: ## Seed database with initial data
	@echo "$(BLUE)Seeding database...$(NC)"
	@cd backend && . venv/bin/activate && python scripts/seed_data.py
	@echo "$(GREEN)✓ Database seeded$(NC)"

db-shell: ## Open PostgreSQL shell
	@docker-compose exec postgres psql -U priorauth_user -d priorauth

db-backup: ## Backup database
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U priorauth_user priorauth > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Backup created in backups/$(NC)"

db-restore: ## Restore database from latest backup
	@echo "$(BLUE)Restoring from latest backup...$(NC)"
	@docker-compose exec -T postgres psql -U priorauth_user priorauth < $$(ls -t backups/*.sql | head -1)
	@echo "$(GREEN)✓ Database restored$(NC)"

# ==================== Testing ====================

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@make test-backend
	@make test-frontend

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	@cd backend && . venv/bin/activate && pytest -v
	@echo "$(GREEN)✓ Backend tests complete$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@cd frontend && npm test -- --passWithNoTests
	@echo "$(GREEN)✓ Frontend tests complete$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@cd backend && . venv/bin/activate && pytest --cov=. --cov-report=html
	@cd frontend && npm test -- --coverage --passWithNoTests
	@echo "$(GREEN)✓ Coverage reports generated$(NC)"
	@echo "$(YELLOW)Backend coverage: backend/htmlcov/index.html$(NC)"
	@echo "$(YELLOW)Frontend coverage: frontend/coverage/lcov-report/index.html$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@./scripts/run_integration_tests.sh
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

# ==================== Code Quality ====================

lint: ## Run linters
	@echo "$(BLUE)Running linters...$(NC)"
	@make lint-backend
	@make lint-frontend

lint-backend: ## Lint backend code
	@echo "$(BLUE)Linting backend...$(NC)"
	@cd backend && . venv/bin/activate && flake8 .
	@echo "$(GREEN)✓ Backend linting complete$(NC)"

lint-frontend: ## Lint frontend code
	@echo "$(BLUE)Linting frontend...$(NC)"
	@cd frontend && npm run lint
	@echo "$(GREEN)✓ Frontend linting complete$(NC)"

format: ## Format all code
	@echo "$(BLUE)Formatting code...$(NC)"
	@make format-backend
	@make format-frontend

format-backend: ## Format backend code with Black
	@echo "$(BLUE)Formatting backend...$(NC)"
	@cd backend && . venv/bin/activate && black .
	@cd backend && . venv/bin/activate && isort .
	@echo "$(GREEN)✓ Backend formatting complete$(NC)"

format-frontend: ## Format frontend code with Prettier
	@echo "$(BLUE)Formatting frontend...$(NC)"
	@cd frontend && npm run format
	@echo "$(GREEN)✓ Frontend formatting complete$(NC)"

type-check: ## Run type checking
	@echo "$(BLUE)Running type checks...$(NC)"
	@cd backend && . venv/bin/activate && mypy . || true
	@cd frontend && npm run type-check
	@echo "$(GREEN)✓ Type checking complete$(NC)"

# ==================== Docker ====================

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker-compose build
	@echo "$(GREEN)✓ Images built$(NC)"

docker-build-prod: ## Build production Docker images
	@echo "$(BLUE)Building production images...$(NC)"
	@docker-compose -f docker-compose.prod.yml build
	@echo "$(GREEN)✓ Production images built$(NC)"

docker-push: ## Push Docker images to registry
	@echo "$(BLUE)Pushing Docker images...$(NC)"
	@docker-compose push
	@echo "$(GREEN)✓ Images pushed$(NC)"

docker-clean: ## Remove all Docker containers, images, and volumes
	@echo "$(RED)⚠ WARNING: This will remove all Docker resources!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@docker-compose down -v --remove-orphans
	@docker system prune -af --volumes
	@echo "$(GREEN)✓ Docker cleaned$(NC)"

# ==================== Utilities ====================

clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

shell-backend: ## Open shell in backend container
	@docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	@docker-compose exec frontend /bin/sh

shell-postgres: ## Open shell in PostgreSQL container
	@docker-compose exec postgres /bin/bash

redis-cli: ## Open Redis CLI
	@docker-compose exec redis redis-cli

# ==================== Documentation ====================

docs: ## Generate API documentation
	@echo "$(BLUE)Generating API documentation...$(NC)"
	@cd backend && . venv/bin/activate && python -c "from main import app; import json; print(json.dumps(app.openapi(), indent=2))" > docs/openapi.json
	@echo "$(GREEN)✓ Documentation generated at docs/openapi.json$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8000/docs$(NC)"
	@make backend

# ==================== CI/CD ====================

ci-test: ## Run CI test suite
	@echo "$(BLUE)Running CI tests...$(NC)"
	@make lint
	@make type-check
	@make test
	@echo "$(GREEN)✓ CI tests passed$(NC)"

pre-commit: ## Run pre-commit checks
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	@make format
	@make lint
	@make test-backend
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

# ==================== Deployment ====================

deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(NC)"
	@./scripts/deploy.sh staging
	@echo "$(GREEN)✓ Deployed to staging$(NC)"

deploy-production: ## Deploy to production environment
	@echo "$(RED)⚠ WARNING: Deploying to PRODUCTION!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@./scripts/deploy.sh production
	@echo "$(GREEN)✓ Deployed to production$(NC)"

# ==================== Health Checks ====================

health-check: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "$(YELLOW)Backend:$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)✗ Backend unhealthy$(NC)"
	@echo "$(YELLOW)Frontend:$(NC)"
	@curl -f http://localhost:3000 || echo "$(RED)✗ Frontend unhealthy$(NC)"
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@docker-compose exec postgres pg_isready || echo "$(RED)✗ PostgreSQL unhealthy$(NC)"
	@echo "$(YELLOW)Redis:$(NC)"
	@docker-compose exec redis redis-cli ping || echo "$(RED)✗ Redis unhealthy$(NC)"
	@echo "$(GREEN)✓ Health check complete$(NC)"

status: ## Show current status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(BLUE)Resource Usage:$(NC)"
	@docker stats --no-stream

# ==================== Monitoring ====================

monitor: ## Show real-time logs and stats
	@echo "$(BLUE)Monitoring services...$(NC)"
	@docker-compose logs -f &
	@docker stats