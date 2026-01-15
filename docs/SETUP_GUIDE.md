# Developer Setup Guide

**Prior Authorization AI Automation Platform**  
**Last Updated:** January 14, 2026

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Initial Setup](#initial-setup)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Database Setup](#database-setup)
6. [External Services](#external-services)
7. [Running the Application](#running-the-application)
8. [Development Workflow](#development-workflow)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Operating System
- **Recommended:** macOS 11+ or Ubuntu 20.04+
- **Supported:** Windows 10+ with WSL2

### Software Prerequisites

| Software | Minimum Version | Recommended | Installation |
|----------|----------------|-------------|--------------|
| Docker | 24.0 | Latest | [Download](https://docker.com) |
| Docker Compose | 2.0 | Latest | Included with Docker Desktop |
| Python | 3.11 | 3.11+ | [Download](https://python.org) |
| Node.js | 18.0 | 20.x LTS | [Download](https://nodejs.org) |
| npm | 9.0 | Latest | Included with Node.js |
| Git | 2.30 | Latest | [Download](https://git-scm.com) |
| Make | 3.81+ | Latest | Pre-installed on macOS/Linux |

### Hardware Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB free space

**Recommended:**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 50 GB free space (SSD)

---

## Initial Setup

### 1. Clone the Repository

```bash
# Clone via HTTPS
git clone https://github.com/yourorg/prior-auth-ai.git

# OR clone via SSH (recommended)
git clone git@github.com:yourorg/prior-auth-ai.git

# Navigate to project directory
cd prior-auth-ai
```

### 2. Verify Prerequisites

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python3 --version

# Check Node.js and npm
node --version
npm --version

# Check Git
git --version

# Check Make
make --version
```

All commands should output version numbers. If any fail, install the missing software.

### 3. Set Up Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your preferred editor
nano .env
# or
code .env
```

**Required Environment Variables:**

```bash
# Application
APP_NAME=PriorAuthAI
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here-change-this-in-production

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=priorauth
POSTGRES_USER=priorauth_user
POSTGRES_PASSWORD=change-this-password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# MinIO/S3
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=documents
MINIO_USE_SSL=false

# Anthropic API (Required for AI features)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Twilio (Optional - for fax functionality)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FAX_NUMBER=

# Email (Optional - for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@priorauth.ai

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Backend Setup

### 1. Create Python Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows (WSL):
source venv/bin/activate

# On Windows (PowerShell):
# .\venv\Scripts\Activate.ps1
```

### 2. Install Python Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Verify installation
pip list
```

### 3. Install Additional Tools

```bash
# Install Tesseract OCR
# On macOS:
brew install tesseract

# On Ubuntu:
sudo apt-get install tesseract-ocr

# On Windows (WSL):
sudo apt-get install tesseract-ocr

# Verify installation
tesseract --version
```

---

## Frontend Setup

### 1. Install Node.js Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Or use yarn if preferred
# yarn install

# Verify installation
npm list --depth=0
```

### 2. Set Up Frontend Environment

```bash
# Copy frontend environment template
cp .env.local.example .env.local

# Edit .env.local
nano .env.local
```

**Frontend Environment Variables:**

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=PriorAuth AI
```

---

## Database Setup

### 1. Start PostgreSQL with Docker

```bash
# Return to project root
cd ..

# Start only PostgreSQL
docker-compose up -d postgres

# Verify PostgreSQL is running
docker-compose ps postgres
docker-compose logs postgres
```

### 2. Run Database Migrations

```bash
# Navigate to backend
cd backend

# Ensure virtual environment is activated
source venv/bin/activate

# Run migrations
alembic upgrade head

# Verify migration
alembic current
```

### 3. Seed Initial Data (Optional)

```bash
# Run seed script
python scripts/seed_data.py

# This creates:
# - Default admin user (admin@example.com / changeme)
# - Sample clinic
# - Sample insurance rules
```

---

## External Services

### 1. Start All Services with Docker Compose

```bash
# From project root
docker-compose up -d

# Verify all services are running
docker-compose ps

# Should show:
# - postgres (running)
# - redis (running)
# - minio (running)
```

### 2. Access Service UIs

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| PostgreSQL | localhost:5432 | priorauth_user / [your-password] |
| Redis | localhost:6379 | (no auth in dev) |

### 3. Configure MinIO

```bash
# Access MinIO Console at http://localhost:9001
# Login with minioadmin / minioadmin

# Create bucket 'documents'
# Set bucket policy to 'private'
```

---

## Running the Application

### Method 1: Using Docker Compose (Recommended for Full Stack)

```bash
# From project root
docker-compose up

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

### Method 2: Running Services Individually (For Development)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Celery Worker:**
```bash
cd backend
source venv/bin/activate
celery -A workers.celery_app worker --loglevel=info
```

**Terminal 4 - Redis & PostgreSQL (Docker):**
```bash
docker-compose up postgres redis minio
```

### Method 3: Using Makefile Commands

```bash
# Start development environment
make dev

# Run backend only
make backend

# Run frontend only
make frontend

# Run tests
make test

# Stop all services
make stop

# Clean up
make clean
```

---

## Development Workflow

### Creating a New Feature

```bash
# 1. Create feature branch
git checkout -b feature/my-new-feature

# 2. Make your changes

# 3. Run tests
make test

# 4. Commit changes
git add .
git commit -m "feat: add my new feature"

# 5. Push to remote
git push origin feature/my-new-feature

# 6. Create pull request on GitHub
```

### Running Tests

**Backend Tests:**
```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/unit/test_pa_service.py

# Run with verbose output
pytest -v
```

**Frontend Tests:**
```bash
cd frontend

# Run unit tests
npm test

# Run E2E tests
npm run test:e2e

# Run with coverage
npm test -- --coverage
```

### Code Quality Checks

**Backend:**
```bash
cd backend

# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Sort imports
isort .
```

**Frontend:**
```bash
cd frontend

# Format code
npm run format

# Lint code
npm run lint

# Type checking
npm run type-check
```

### Database Operations

**Create a new migration:**
```bash
cd backend
source venv/bin/activate

# Auto-generate migration from model changes
alembic revision --autogenerate -m "add new table"

# Create empty migration
alembic revision -m "custom migration"

# Edit the generated file in backend/alembic/versions/
```

**Apply migrations:**
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# View migration history
alembic history
```

**Reset database:**
```bash
# WARNING: This deletes all data!

# Drop all tables
alembic downgrade base

# Recreate all tables
alembic upgrade head

# Re-seed data
python scripts/seed_data.py
```

---

## Troubleshooting

### Common Issues

#### Docker Issues

**Problem:** "Cannot connect to Docker daemon"
```bash
# Solution: Start Docker Desktop
# On macOS: Open Docker Desktop application
# On Linux: 
sudo systemctl start docker
```

**Problem:** Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 [PID]

# Or change port in docker-compose.yml
```

#### Database Issues

**Problem:** "Connection refused" to PostgreSQL
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**Problem:** Migration fails
```bash
# Check current migration state
alembic current

# Check pending migrations
alembic history

# Force downgrade and re-upgrade
alembic downgrade base
alembic upgrade head
```

#### Python Issues

**Problem:** Package installation fails
```bash
# Upgrade pip
pip install --upgrade pip

# Clear cache and reinstall
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

**Problem:** Import errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Verify PYTHONPATH
echo $PYTHONPATH

# Add backend to PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Frontend Issues

**Problem:** npm install fails
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem:** "Module not found" errors
```bash
# Check if module is in package.json
cat package.json | grep [module-name]

# Install missing module
npm install [module-name]

# Restart dev server
npm run dev
```

#### API Issues

**Problem:** CORS errors
```bash
# Check CORS settings in backend/core/config.py
# Ensure NEXT_PUBLIC_API_URL is correct in frontend/.env.local
```

**Problem:** 401 Unauthorized errors
```bash
# Check JWT token in browser DevTools > Application > Cookies
# Verify token hasn't expired
# Try logging out and logging back in
```

---

## Development Tools

### Recommended IDE Setup

**Visual Studio Code Extensions:**
- Python (Microsoft)
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Docker
- GitLens

**VS Code Settings (`.vscode/settings.json`):**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Useful Commands Reference

```bash
# Docker
docker-compose up -d          # Start in detached mode
docker-compose down           # Stop all services
docker-compose logs -f        # Follow logs
docker-compose ps             # List running services
docker-compose restart        # Restart all services

# Database
alembic upgrade head          # Run migrations
alembic downgrade -1          # Rollback one migration
alembic history               # View migration history
alembic current               # Show current migration

# Python
pip freeze > requirements.txt # Update requirements
pytest -v                     # Run tests verbosely
black .                       # Format code
flake8 .                      # Lint code

# Node
npm run dev                   # Start dev server
npm run build                 # Build for production
npm test                      # Run tests
npm run lint                  # Lint code
npm run format                # Format code

# Git
git status                    # Check status
git log --oneline            # View commit history
git branch -a                # List all branches
git pull origin develop      # Pull latest from develop
```

---

## Next Steps

After completing the setup:

1. **Verify Installation:**
   - Access frontend at http://localhost:3000
   - Access API docs at http://localhost:8000/docs
   - Login with default credentials (admin@example.com / changeme)

2. **Explore Codebase:**
   - Read [ARCHITECTURE.md](docs/ARCHITECTURE.md)
   - Review [API_SPEC.md](docs/API_SPEC.md)
   - Check [PHASE_COMPLETION.md](docs/PHASE_COMPLETION.md)

3. **Start Development:**
   - Pick a task from the project board
   - Create a feature branch
   - Make your changes
   - Submit a pull request

---

## Getting Help

- **Documentation:** See `/docs` folder
- **Issues:** GitHub Issues
- **Chat:** Slack #prior-auth-ai
- **Email:** dev-team@yourorg.com

---

**Last Updated:** January 14, 2026  
**Maintained By:** Development Team