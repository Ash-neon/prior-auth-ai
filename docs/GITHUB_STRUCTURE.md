# GitHub Repository Structure

**Project:** Prior Authorization AI Automation Platform  
**Last Updated:** January 14, 2026

---

## Complete Folder Hierarchy

```
prior-auth-ai/
│
├── .github/                           # GitHub-specific configurations
│   ├── workflows/                     # GitHub Actions CI/CD
│   │   ├── backend-tests.yml         # Backend testing workflow
│   │   ├── frontend-tests.yml        # Frontend testing workflow
│   │   ├── deploy-staging.yml        # Staging deployment
│   │   └── deploy-production.yml     # Production deployment
│   ├── ISSUE_TEMPLATE/               # Issue templates
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── question.md
│   ├── PULL_REQUEST_TEMPLATE.md      # PR template
│   └── CODEOWNERS                     # Code ownership
│
├── backend/                           # Python/FastAPI backend
│   ├── alembic/                      # Database migrations
│   │   ├── versions/                 # Migration files
│   │   ├── env.py                    # Alembic environment
│   │   └── script.py.mako           # Migration template
│   │
│   ├── api/                          # API layer (FastAPI routes)
│   │   ├── v1/                       # API version 1
│   │   │   ├── endpoints/           # Route handlers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py          # Auth endpoints
│   │   │   │   ├── pa.py            # PA management
│   │   │   │   ├── documents.py     # Document management
│   │   │   │   ├── submissions.py   # Submission endpoints
│   │   │   │   ├── appeals.py       # Appeal management
│   │   │   │   ├── analytics.py     # Analytics endpoints
│   │   │   │   ├── users.py         # User management
│   │   │   │   └── admin.py         # Admin endpoints
│   │   │   ├── __init__.py
│   │   │   └── router.py            # V1 router aggregation
│   │   ├── __init__.py
│   │   ├── dependencies.py           # Shared dependencies (auth, db)
│   │   └── middleware.py             # Custom middleware
│   │
│   ├── core/                         # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py                # Settings (from env vars)
│   │   ├── security.py              # JWT, password hashing
│   │   ├── logging.py               # Logging configuration
│   │   └── exceptions.py            # Custom exceptions
│   │
│   ├── db/                           # Database layer
│   │   ├── __init__.py
│   │   ├── base.py                  # Base model class
│   │   ├── session.py               # DB session management
│   │   └── init_db.py               # DB initialization
│   │
│   ├── models/                       # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py                  # User model
│   │   ├── clinic.py                # Clinic model
│   │   ├── patient.py               # Patient model
│   │   ├── prior_authorization.py   # PA model
│   │   ├── document.py              # Document model
│   │   ├── extracted_data.py        # Extracted data model
│   │   ├── insurance_rule.py        # Insurance rules
│   │   ├── pa_packet.py             # PA packet model
│   │   ├── submission.py            # Submission model
│   │   ├── appeal.py                # Appeal model
│   │   └── audit_log.py             # Audit trail
│   │
│   ├── schemas/                      # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── auth.py                  # Auth schemas
│   │   ├── pa.py                    # PA schemas
│   │   ├── document.py              # Document schemas
│   │   ├── submission.py            # Submission schemas
│   │   ├── appeal.py                # Appeal schemas
│   │   ├── analytics.py             # Analytics schemas
│   │   └── user.py                  # User schemas
│   │
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── pa_service.py            # PA management logic
│   │   ├── document_service.py      # Document processing
│   │   ├── ai_service.py            # AI orchestration
│   │   ├── extraction_service.py    # Data extraction
│   │   ├── rule_engine_service.py   # Rule matching
│   │   ├── packet_generator.py      # PA packet generation
│   │   ├── submission_service.py    # Submission orchestration
│   │   ├── tracking_service.py      # Status tracking
│   │   ├── appeal_service.py        # Appeal generation
│   │   ├── analytics_service.py     # Analytics calculations
│   │   ├── notification_service.py  # Email/SMS notifications
│   │   └── audit_service.py         # Audit logging
│   │
│   ├── workers/                      # Celery background workers
│   │   ├── __init__.py
│   │   ├── celery_app.py           # Celery configuration
│   │   ├── ocr_worker.py           # OCR processing
│   │   ├── extraction_worker.py     # AI extraction
│   │   ├── submission_worker.py     # Submission jobs
│   │   ├── tracking_worker.py       # Status polling
│   │   └── notification_worker.py   # Send notifications
│   │
│   ├── utils/                        # Utility functions
│   │   ├── __init__.py
│   │   ├── validators.py            # Data validators
│   │   ├── formatters.py            # Data formatters
│   │   ├── encryption.py            # PHI encryption
│   │   ├── pdf_utils.py             # PDF manipulation
│   │   ├── date_utils.py            # Date helpers
│   │   └── constants.py             # Constants
│   │
│   ├── tests/                        # Backend tests
│   │   ├── __init__.py
│   │   ├── conftest.py              # Pytest fixtures
│   │   ├── unit/                    # Unit tests
│   │   │   ├── test_services/
│   │   │   ├── test_utils/
│   │   │   └── test_models/
│   │   ├── integration/             # Integration tests
│   │   │   ├── test_api/
│   │   │   └── test_workflows/
│   │   └── fixtures/                # Test data
│   │       ├── sample_documents/
│   │       └── mock_responses/
│   │
│   ├── .env.example                 # Environment template
│   ├── .gitignore
│   ├── alembic.ini                  # Alembic config
│   ├── Dockerfile                   # Backend Docker image
│   ├── main.py                      # FastAPI application entry
│   ├── requirements.txt             # Python dependencies
│   ├── requirements-dev.txt         # Dev dependencies
│   └── pytest.ini                   # Pytest configuration
│
├── frontend/                         # Next.js/React frontend
│   ├── components/                   # React components
│   │   ├── ui/                      # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── table.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...
│   │   ├── layout/                  # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Layout.tsx
│   │   ├── auth/                    # Auth components
│   │   │   ├── LoginForm.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   └── AuthProvider.tsx
│   │   ├── pa/                      # PA components
│   │   │   ├── PAList.tsx
│   │   │   ├── PADetail.tsx
│   │   │   ├── CreatePAForm.tsx
│   │   │   ├── PAStatusBadge.tsx
│   │   │   └── PATimeline.tsx
│   │   ├── documents/               # Document components
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentViewer.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   └── ExtractionResults.tsx
│   │   ├── analytics/               # Analytics components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── MetricsCard.tsx
│   │   │   ├── ApprovalChart.tsx
│   │   │   └── TurnaroundChart.tsx
│   │   └── common/                  # Shared components
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── Pagination.tsx
│   │       └── SearchBar.tsx
│   │
│   ├── pages/                        # Next.js pages (routing)
│   │   ├── _app.tsx                 # App wrapper
│   │   ├── _document.tsx            # Document wrapper
│   │   ├── index.tsx                # Home/Dashboard
│   │   ├── login.tsx                # Login page
│   │   ├── pa/                      # PA pages
│   │   │   ├── index.tsx            # PA list
│   │   │   ├── [id].tsx             # PA detail
│   │   │   └── create.tsx           # Create PA
│   │   ├── analytics/               # Analytics pages
│   │   │   └── index.tsx
│   │   ├── admin/                   # Admin pages
│   │   │   ├── users.tsx
│   │   │   └── settings.tsx
│   │   └── api/                     # API routes (Next.js)
│   │       └── health.ts
│   │
│   ├── hooks/                        # Custom React hooks
│   │   ├── useAuth.ts               # Auth hook
│   │   ├── usePA.ts                 # PA data hook
│   │   ├── useDocuments.ts          # Documents hook
│   │   ├── useWebSocket.ts          # WebSocket hook
│   │   └── useAnalytics.ts          # Analytics hook
│   │
│   ├── lib/                          # Libraries and utilities
│   │   ├── api.ts                   # API client
│   │   ├── websocket.ts             # WebSocket client
│   │   ├── auth.ts                  # Auth utilities
│   │   └── utils.ts                 # General utilities
│   │
│   ├── store/                        # State management (Zustand)
│   │   ├── authStore.ts             # Auth state
│   │   ├── paStore.ts               # PA state
│   │   └── uiStore.ts               # UI state
│   │
│   ├── styles/                       # Global styles
│   │   └── globals.css              # Global CSS
│   │
│   ├── types/                        # TypeScript types
│   │   ├── api.ts                   # API types
│   │   ├── pa.ts                    # PA types
│   │   ├── document.ts              # Document types
│   │   └── user.ts                  # User types
│   │
│   ├── public/                       # Static assets
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   │
│   ├── .env.local.example           # Environment template
│   ├── .eslintrc.json               # ESLint config
│   ├── .gitignore
│   ├── Dockerfile                   # Frontend Docker image
│   ├── next.config.js               # Next.js config
│   ├── package.json                 # Dependencies
│   ├── postcss.config.js            # PostCSS config
│   ├── tailwind.config.js           # Tailwind config
│   └── tsconfig.json                # TypeScript config
│
├── ai-engines/                       # AI processing modules
│   ├── extraction/                   # Clinical data extraction
│   │   ├── __init__.py
│   │   ├── extractor.py             # Main extraction engine
│   │   ├── validators.py            # ICD-10/CPT validators
│   │   └── confidence.py            # Confidence scoring
│   │
│   ├── rule-engine/                  # Insurance rule matching
│   │   ├── __init__.py
│   │   ├── matcher.py               # Rule matching logic
│   │   ├── rules_db/                # JSON rule repository
│   │   │   ├── blue_cross.json
│   │   │   ├── aetna.json
│   │   │   └── united_healthcare.json
│   │   └── rule_schema.json         # Rule format schema
│   │
│   ├── summarizer/                   # Medical necessity analyzer
│   │   ├── __init__.py
│   │   └── medical_necessity.py     # AI summarization
│   │
│   ├── appeal-generator/             # Appeal letter generator
│   │   ├── __init__.py
│   │   ├── analyzer.py              # Denial analysis
│   │   └── generator.py             # Letter generation
│   │
│   └── prompts/                      # AI prompt templates
│       ├── clinical_extraction.txt
│       ├── medical_necessity.txt
│       ├── denial_analysis.txt
│       └── appeal_letter.txt
│
├── automation/                       # RPA and integrations
│   ├── fax-service/                  # Fax automation
│   │   ├── __init__.py
│   │   ├── twilio_fax.py            # Twilio integration
│   │   ├── efax.py                  # eFax integration
│   │   └── fax_manager.py           # Fax orchestration
│   │
│   ├── rpa-portal/                   # Portal automation
│   │   ├── __init__.py
│   │   ├── base_portal.py           # Base portal class
│   │   ├── portals/                 # Payer-specific scripts
│   │   │   ├── blue_cross.py
│   │   │   ├── aetna.py
│   │   │   └── united_healthcare.py
│   │   ├── credentials.py           # Credential management
│   │   └── captcha_handler.py       # CAPTCHA handling
│   │
│   └── insurer-apis/                 # Payer API connectors
│       ├── __init__.py
│       ├── base_connector.py        # Base API connector
│       ├── availity.py              # Availity integration
│       ├── covermymeds.py           # CoverMyMeds
│       └── surescripts.py           # Surescripts
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md              # System architecture
│   ├── API_SPEC.md                  # API specification
│   ├── DATA_FLOW.md                 # Data flow diagrams
│   ├── PHASE_COMPLETION.md          # Development tracker
│   ├── DEPLOYMENT.md                # Deployment guide
│   ├── USER_MANUAL.md               # User manual
│   ├── ADMIN_GUIDE.md               # Admin guide
│   ├── TROUBLESHOOTING.md           # Troubleshooting
│   └── images/                      # Documentation images
│       └── architecture-diagram.png
│
├── infra/                            # Infrastructure as Code
│   ├── docker/                      # Docker configurations
│   │   ├── backend.Dockerfile       # Backend image
│   │   ├── frontend.Dockerfile      # Frontend image
│   │   ├── worker.Dockerfile        # Celery worker
│   │   └── nginx.Dockerfile         # NGINX
│   │
│   ├── k8s/                         # Kubernetes manifests
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── worker-deployment.yaml
│   │   ├── postgres-statefulset.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── ingress.yaml
│   │   └── services.yaml
│   │
│   ├── nginx/                       # NGINX configurations
│   │   ├── nginx.conf               # Main config
│   │   └── ssl/                     # SSL certificates
│   │
│   └── terraform/                   # Terraform IaC
│       ├── main.tf                  # Main terraform file
│       ├── variables.tf             # Variables
│       ├── outputs.tf               # Outputs
│       ├── modules/                 # Terraform modules
│       │   ├── vpc/
│       │   ├── rds/
│       │   ├── eks/
│       │   └── s3/
│       └── environments/            # Environment configs
│           ├── dev/
│           ├── staging/
│           └── production/
│
├── scripts/                          # Utility scripts
│   ├── seed_data.py                 # Database seeding
│   ├── backup.sh                    # Backup script
│   ├── restore.sh                   # Restore script
│   ├── migrate.sh                   # Migration helper
│   ├── deploy.sh                    # Deployment script
│   └── run_integration_tests.sh     # Integration tests
│
├── .env.example                      # Global env template
├── .gitignore                        # Git ignore rules
├── .dockerignore                     # Docker ignore rules
├── CONTRIBUTING.md                   # Contribution guidelines
├── LICENSE                           # License file
├── README.md                         # Project README
├── docker-compose.yml                # Local development
├── docker-compose.prod.yml           # Production compose
└── Makefile                          # Common commands
```

---

## File Descriptions by Category

### Configuration Files

| File | Purpose |
|------|---------|
| `.env.example` | Template for environment variables |
| `docker-compose.yml` | Local development orchestration |
| `docker-compose.prod.yml` | Production orchestration |
| `Makefile` | Common development commands |
| `.gitignore` | Files to exclude from Git |
| `.dockerignore` | Files to exclude from Docker builds |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `CONTRIBUTING.md` | Contribution guidelines |
| `LICENSE` | Software license |
| `docs/ARCHITECTURE.md` | Detailed system architecture |
| `docs/API_SPEC.md` | Complete API documentation |
| `docs/DATA_FLOW.md` | Data flow diagrams and explanations |
| `docs/PHASE_COMPLETION.md` | Development phase tracker |
| `docs/DEPLOYMENT.md` | Deployment instructions |

### Backend Core

| Directory | Purpose |
|-----------|---------|
| `backend/api/` | FastAPI routes and endpoints |
| `backend/core/` | Configuration, security, logging |
| `backend/db/` | Database connection and session |
| `backend/models/` | SQLAlchemy ORM models |
| `backend/schemas/` | Pydantic validation schemas |
| `backend/services/` | Business logic layer |
| `backend/workers/` | Celery background tasks |
| `backend/utils/` | Utility functions |
| `backend/tests/` | Backend test suite |

### Frontend Core

| Directory | Purpose |
|-----------|---------|
| `frontend/components/` | React components |
| `frontend/pages/` | Next.js pages and routing |
| `frontend/hooks/` | Custom React hooks |
| `frontend/lib/` | API clients and utilities |
| `frontend/store/` | Zustand state management |
| `frontend/types/` | TypeScript type definitions |
| `frontend/public/` | Static assets |

### AI & Automation

| Directory | Purpose |
|-----------|---------|
| `ai-engines/extraction/` | Clinical data extraction |
| `ai-engines/rule-engine/` | Insurance rule matching |
| `ai-engines/summarizer/` | Medical necessity analysis |
| `ai-engines/appeal-generator/` | Appeal letter generation |
| `automation/fax-service/` | Fax API integrations |
| `automation/rpa-portal/` | Portal automation scripts |
| `automation/insurer-apis/` | Payer API connectors |

### Infrastructure

| Directory | Purpose |
|-----------|---------|
| `infra/docker/` | Dockerfile definitions |
| `infra/k8s/` | Kubernetes manifests |
| `infra/nginx/` | NGINX configurations |
| `infra/terraform/` | Infrastructure as Code |

---

## Naming Conventions

### Files
- **Python:** `snake_case.py`
- **TypeScript/React:** `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **Configuration:** `kebab-case.yml` or `lowercase.conf`

### Directories
- **All lowercase:** `snake_case/` or `kebab-case/`
- **Consistent naming:** Use full names, not abbreviations

### Branches
- **Feature:** `feature/description-of-feature`
- **Bugfix:** `bugfix/description-of-bug`
- **Hotfix:** `hotfix/description-of-issue`
- **Release:** `release/vX.Y.Z`

---

## Best Practices

### Code Organization

1. **Separation of Concerns:** Keep API routes, business logic, and data models separate
2. **DRY Principle:** Extract common functionality into utilities
3. **Single Responsibility:** Each module should have one clear purpose
4. **Dependency Injection:** Pass dependencies rather than importing globally

### File Size

- **Maximum:** 500 lines per file (guideline, not strict rule)
- **Ideal:** 200-300 lines for most files
- **If larger:** Consider splitting into multiple files

### Import Order

**Python:**
```python
# Standard library
import os
import sys

# Third-party
from fastapi import FastAPI
from sqlalchemy import Column

# Local
from app.models import User
from app.utils import hash_password
```

**TypeScript:**
```typescript
// React/Next
import React from 'react';
import { NextPage } from 'next';

// Third-party
import { useQuery } from 'react-query';

// Components
import { Button } from '@/components/ui/button';

// Local
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';
```

---

## Version Control

### Protected Branches
- `main` - Production-ready code
- `develop` - Development integration branch
- `staging` - Staging environment

### Required Reviewers
- Backend changes: 1+ backend developer
- Frontend changes: 1+ frontend developer
- Infrastructure: DevOps lead
- Security-sensitive: Security reviewer

---

**Last Updated:** January 14, 2026  
**Maintained By:** Development Team