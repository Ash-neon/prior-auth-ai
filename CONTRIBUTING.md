# Contributing to Prior Authorization AI Platform

Thank you for your interest in contributing! This document provides guidelines and workflows for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Pull Request Process](#pull-request-process)
7. [Documentation](#documentation)
8. [Security](#security)

---

## Code of Conduct

### Our Standards

- **Be respectful** and considerate of others
- **Be collaborative** and open to feedback
- **Be professional** in all communications
- **Prioritize patient safety** and HIPAA compliance in all code
- **Ask questions** when you're unsure

### Unacceptable Behavior

- Harassment or discrimination of any kind
- Publishing private information without consent
- Unprofessional conduct or language
- Trolling or inflammatory comments

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. Read the [README.md](README.md)
2. Reviewed [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
3. Completed the [setup guide](docs/SETUP_GUIDE.md)
4. Successfully run the application locally

### Setting Up Your Development Environment

```bash
# Fork the repository on GitHub
# Clone your fork
git clone git@github.com:YOUR_USERNAME/prior-auth-ai.git
cd prior-auth-ai

# Add upstream remote
git remote add upstream git@github.com:yourorg/prior-auth-ai.git

# Run initial setup
make setup

# Start development environment
make dev
```

---

## Development Workflow

### Branch Naming Convention

Use the following prefixes for your branches:

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feature/` | New features | `feature/add-appeal-dashboard` |
| `bugfix/` | Bug fixes | `bugfix/fix-extraction-timeout` |
| `hotfix/` | Urgent production fixes | `hotfix/security-patch` |
| `refactor/` | Code refactoring | `refactor/simplify-pa-service` |
| `docs/` | Documentation updates | `docs/update-api-spec` |
| `test/` | Adding/updating tests | `test/add-pa-service-tests` |
| `chore/` | Maintenance tasks | `chore/update-dependencies` |

### Creating a New Feature

```bash
# Ensure you're on the latest develop
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/my-new-feature

# Make your changes...

# Run tests
make test

# Run linting
make lint

# Run formatting
make format

# Commit your changes
git add .
git commit -m "feat: add my new feature"

# Push to your fork
git push origin feature/my-new-feature

# Create pull request on GitHub
```

---

## Coding Standards

### Python (Backend)

#### Style Guide

Follow [PEP 8](https://pep8.org/) with these specifics:

- **Line length:** 100 characters (not 79)
- **Indentation:** 4 spaces
- **Quotes:** Double quotes for strings (except when single avoids escaping)
- **Imports:** Grouped and sorted (use `isort`)

#### Example

```python
"""Module for PA management services."""

from typing import List, Optional
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.prior_authorization import PriorAuthorization
from schemas.pa import PACreate, PAResponse
from utils.logging import get_logger


logger = get_logger(__name__)


class PAService:
    """Service for managing Prior Authorization requests."""

    def __init__(self, db: Session):
        self.db = db

    def create_pa(self, pa_data: PACreate) -> PAResponse:
        """
        Create a new PA request.

        Args:
            pa_data: PA creation data

        Returns:
            Created PA response

        Raises:
            HTTPException: If patient not found
        """
        logger.info(f"Creating PA for patient {pa_data.patient_id}")
        
        # Validate patient exists
        if not self._validate_patient(pa_data.patient_id):
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create PA
        pa = PriorAuthorization(**pa_data.dict())
        self.db.add(pa)
        self.db.commit()
        self.db.refresh(pa)
        
        logger.info(f"PA created with ID {pa.id}")
        return PAResponse.from_orm(pa)
```

#### Naming Conventions

- **Classes:** `PascalCase` (e.g., `PAService`, `DocumentProcessor`)
- **Functions/Methods:** `snake_case` (e.g., `create_pa`, `process_document`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private methods:** `_leading_underscore` (e.g., `_validate_patient`)

#### Type Hints

Always use type hints:

```python
def process_document(
    document_id: str,
    options: Optional[Dict[str, Any]] = None
) -> ProcessingResult:
    pass
```

#### Error Handling

```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail="Processing failed")
finally:
    cleanup_resources()
```

### TypeScript/React (Frontend)

#### Style Guide

- **Line length:** 100 characters
- **Indentation:** 2 spaces
- **Quotes:** Single quotes for strings
- **Semicolons:** Required

#### Example

```typescript
import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';

import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { PA } from '@/types/pa';

interface PAListProps {
  clinicId: string;
  onSelect: (pa: PA) => void;
}

export const PAList: React.FC<PAListProps> = ({ clinicId, onSelect }) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery(
    ['pas', clinicId],
    () => api.pa.list({ clinicId })
  );

  useEffect(() => {
    if (data && data.length > 0 && !selectedId) {
      setSelectedId(data[0].id);
    }
  }, [data, selectedId]);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading PAs</div>;

  return (
    <div className="space-y-2">
      {data?.map((pa) => (
        <Button
          key={pa.id}
          variant={pa.id === selectedId ? 'default' : 'outline'}
          onClick={() => onSelect(pa)}
        >
          {pa.pa_number}
        </Button>
      ))}
    </div>
  );
};
```

#### Naming Conventions

- **Components:** `PascalCase` (e.g., `PAList`, `DocumentViewer`)
- **Functions/Variables:** `camelCase` (e.g., `handleSubmit`, `isLoading`)
- **Types/Interfaces:** `PascalCase` (e.g., `PA`, `PAListProps`)
- **Constants:** `UPPER_SNAKE_CASE`

### Database Migrations

Always create descriptive migration messages:

```bash
# Good
alembic revision -m "add approval_rate column to clinics table"

# Bad
alembic revision -m "update db"
```

---

## Testing Requirements

### Backend Testing

#### Unit Tests

All services and utilities must have unit tests:

```python
# tests/unit/test_pa_service.py
import pytest
from unittest.mock import Mock

from services.pa_service import PAService
from schemas.pa import PACreate


def test_create_pa_success(mock_db):
    """Test successful PA creation."""
    service = PAService(mock_db)
    pa_data = PACreate(
        patient_id="test-patient",
        procedure_code="99213",
        diagnosis_codes=["E11.9"]
    )
    
    result = service.create_pa(pa_data)
    
    assert result.pa_number is not None
    assert result.status == "draft"
```

#### Integration Tests

Test API endpoints:

```python
# tests/integration/test_pa_api.py
def test_create_pa_endpoint(client, auth_headers):
    """Test POST /pa endpoint."""
    response = client.post(
        "/api/v1/pa",
        json={
            "patient_id": "test-patient",
            "procedure_code": "99213",
            "diagnosis_codes": ["E11.9"]
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert "pa_number" in response.json()
```

### Frontend Testing

#### Component Tests

```typescript
// components/__tests__/PAList.test.tsx
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';

import { PAList } from '../PAList';

describe('PAList', () => {
  it('renders loading state', () => {
    const queryClient = new QueryClient();
    
    render(
      <QueryClientProvider client={queryClient}>
        <PAList clinicId="test-clinic" onSelect={() => {}} />
      </QueryClientProvider>
    );
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});
```

### Test Coverage Requirements

- **Backend:** Minimum 80% coverage
- **Frontend:** Minimum 70% coverage
- **Critical paths:** 100% coverage (auth, PA creation, submission)

---

## Pull Request Process

### Before Submitting

1. **Update documentation** if you changed APIs or behavior
2. **Add tests** for new functionality
3. **Run full test suite:** `make test`
4. **Run linters:** `make lint`
5. **Format code:** `make format`
6. **Update CHANGELOG.md** if applicable

### PR Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

Examples:
feat(pa): add appeal generation endpoint
fix(extraction): handle malformed OCR output
docs(api): update submission endpoint examples
refactor(services): simplify PA state machine
test(pa): add integration tests for workflow
```

#### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Related Issue
Closes #123

## Changes Made
- Added X feature
- Fixed Y bug
- Updated Z documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] No new warnings
```

### Review Process

1. **Automated checks** must pass (tests, linting)
2. **At least 1 approval** required from team member
3. **Security review** if touching auth, PHI, or encryption
4. **HIPAA review** if changing how PHI is handled
5. **Merge** via squash or rebase (no merge commits)

---

## Documentation

### When to Update Documentation

Update docs when you:

- Add/change API endpoints → Update `docs/API_SPEC.md`
- Change architecture → Update `docs/ARCHITECTURE.md`
- Change data flow → Update `docs/DATA_FLOW.md`
- Add dependencies → Update README and setup guide
- Complete a phase → Update `docs/PHASE_COMPLETION.md`

### Documentation Standards

- Use **clear, concise language**
- Include **code examples** where helpful
- Add **diagrams** for complex flows (use Mermaid or ASCII)
- Keep **consistent formatting**
- Update **table of contents** if adding sections

---

## Security

### Reporting Security Issues

**DO NOT** create public GitHub issues for security vulnerabilities.

Instead:
1. Email security@yourorg.com
2. Include detailed description
3. Wait for response (within 48 hours)
4. Work with team to address

### Security Guidelines

- **Never commit secrets** (API keys, passwords, tokens)
- **Use environment variables** for all configuration
- **Encrypt PHI** always (at rest and in transit)
- **Validate all inputs** to prevent injection attacks
- **Use parameterized queries** to prevent SQL injection
- **Sanitize user input** before displaying
- **Keep dependencies updated** (run `npm audit`, `pip-audit`)

### HIPAA Compliance

When handling PHI:

- ✅ **Log access** to audit trail
- ✅ **Encrypt data** using approved methods
- ✅ **Minimize exposure** (only access what's needed)
- ✅ **Redact from logs** (use `[PATIENT_NAME]` placeholders)
- ✅ **Delete securely** when no longer needed

---

## Git Commit Messages

### Format

```
type(scope): subject

body (optional)

footer (optional)
```

### Examples

```
feat(pa): add multi-step approval workflow

Implements a configurable multi-step approval process for
high-cost procedures. Clinic admins can define approval
chains in settings.

Closes #456
```

```
fix(extraction): handle edge case in ICD-10 parsing

Previously, ICD-10 codes with decimal points in unusual
positions caused extraction failures. Updated regex to
handle all valid formats.
```

### Best Practices

- **Use imperative mood** ("add" not "added")
- **Keep subject under 50 chars**
- **Wrap body at 72 chars**
- **Explain why, not what** (code shows what)
- **Reference issues** in footer

---

## Questions?

If you have questions about contributing:

- **Technical questions:** Ask in #dev-help Slack channel
- **Architecture questions:** Review docs or ask in #architecture
- **Process questions:** Ask your team lead

---

**Thank you for contributing to making healthcare PA workflows better!**