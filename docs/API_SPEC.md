# Prior Authorization AI Platform - API Specification

**Version:** 1.0.0  
**Base URL:** `https://api.priorauth.ai/v1`  
**Authentication:** JWT Bearer Token  
**Last Updated:** January 14, 2026

---

## Table of Contents

1. [Authentication](#authentication)
2. [Common Patterns](#common-patterns)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Endpoints](#endpoints)
   - [Auth Endpoints](#auth-endpoints)
   - [PA Management](#pa-management)
   - [Document Management](#document-management)
   - [Submission Management](#submission-management)
   - [Appeal Management](#appeal-management)
   - [Analytics](#analytics)
   - [User Management](#user-management)
   - [Admin Endpoints](#admin-endpoints)
6. [WebSocket Events](#websocket-events)
7. [Webhooks](#webhooks)

---

## Authentication

### JWT Token Structure

All API requests (except `/auth/login`) require a JWT token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Payload

```json
{
  "user_id": "uuid",
  "email": "user@clinic.com",
  "role": "clinician",
  "clinic_id": "uuid",
  "exp": 1640000000,
  "iat": 1639996400
}
```

### Token Expiration

- **Access Token:** 30 minutes
- **Refresh Token:** 7 days

---

## Common Patterns

### Pagination

List endpoints support pagination:

**Request:**
```
GET /api/v1/pa/list?page=1&per_page=20&sort_by=created_at&sort_order=desc
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_pages": 5,
    "total_items": 87,
    "has_next": true,
    "has_prev": false
  }
}
```

### Filtering

```
GET /api/v1/pa/list?status=pending&payer=BlueCross&from_date=2026-01-01
```

### Sorting

```
GET /api/v1/pa/list?sort_by=updated_at&sort_order=desc
```

### Field Selection (Sparse Fieldsets)

```
GET /api/v1/pa/{id}?fields=id,pa_number,status,patient_name
```

### Including Related Resources

```
GET /api/v1/pa/{id}?include=documents,submissions,patient
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Prior authorization with ID xyz not found",
    "details": {
      "resource_type": "prior_authorization",
      "resource_id": "xyz"
    },
    "timestamp": "2026-01-14T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE with no body |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource or state conflict |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Temporary unavailability |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |
| `UNAUTHORIZED` | Authentication failed |
| `FORBIDDEN` | Insufficient permissions |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `EXTERNAL_SERVICE_ERROR` | Third-party API failed |
| `AI_EXTRACTION_FAILED` | Claude API error |
| `INVALID_STATE_TRANSITION` | Cannot change to requested state |

---

## Rate Limiting

### Limits by Endpoint Category

| Category | Limit | Window |
|----------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Read Operations | 100 requests | 1 minute |
| Write Operations | 50 requests | 1 minute |
| Document Upload | 20 requests | 1 minute |
| AI Operations | 30 requests | 1 minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73
X-RateLimit-Reset: 1640000000
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 45 seconds.",
    "details": {
      "limit": 100,
      "window_seconds": 60,
      "retry_after": 45
    }
  }
}
```

---

## Endpoints

### Auth Endpoints

#### POST /auth/login

Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "email": "doctor@clinic.com",
  "password": "secure_password",
  "mfa_code": "123456"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "doctor@clinic.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "clinician",
    "clinic_id": "uuid",
    "clinic_name": "Main Street Clinic"
  }
}
```

#### POST /auth/refresh

Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800
}
```

#### POST /auth/logout

Invalidate current session.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (204):** No content

#### POST /auth/forgot-password

Request password reset email.

**Request:**
```json
{
  "email": "doctor@clinic.com"
}
```

**Response (200):**
```json
{
  "message": "If an account exists with this email, a password reset link has been sent."
}
```

---

### PA Management

#### POST /pa

Create a new prior authorization request.

**Request:**
```json
{
  "patient_id": "uuid",
  "payer_name": "Blue Cross Blue Shield",
  "payer_id": "BCBS-001",
  "procedure_code": "99213",
  "diagnosis_codes": ["E11.9", "I10"],
  "requested_service": "Office visit for diabetes management",
  "priority": "routine",
  "clinical_notes": "Patient presents with...",
  "provider_npi": "1234567890"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "pa_number": "PA-2026-00123",
  "patient_id": "uuid",
  "patient_name": "John Smith",
  "clinic_id": "uuid",
  "payer_name": "Blue Cross Blue Shield",
  "payer_id": "BCBS-001",
  "procedure_code": "99213",
  "diagnosis_codes": ["E11.9", "I10"],
  "status": "draft",
  "priority": "routine",
  "created_at": "2026-01-14T10:30:00Z",
  "updated_at": "2026-01-14T10:30:00Z",
  "created_by": {
    "id": "uuid",
    "name": "Dr. Jane Doe"
  }
}
```

#### GET /pa/{id}

Retrieve a specific PA request.

**Response (200):**
```json
{
  "id": "uuid",
  "pa_number": "PA-2026-00123",
  "patient": {
    "id": "uuid",
    "name": "John Smith",
    "dob": "1980-05-15",
    "mrn": "MRN-12345"
  },
  "clinic": {
    "id": "uuid",
    "name": "Main Street Clinic",
    "npi": "1234567890"
  },
  "payer_name": "Blue Cross Blue Shield",
  "payer_id": "BCBS-001",
  "procedure_code": "99213",
  "procedure_description": "Office or other outpatient visit",
  "diagnosis_codes": [
    {
      "code": "E11.9",
      "description": "Type 2 diabetes mellitus without complications"
    },
    {
      "code": "I10",
      "description": "Essential (primary) hypertension"
    }
  ],
  "status": "submitted",
  "priority": "routine",
  "medical_necessity": "Patient requires ongoing management...",
  "submission_method": "fax",
  "submitted_at": "2026-01-14T11:00:00Z",
  "decision_received_at": null,
  "decision": null,
  "auth_number": null,
  "effective_date": null,
  "expiration_date": null,
  "documents": [
    {
      "id": "uuid",
      "type": "clinical_note",
      "file_name": "progress_note.pdf",
      "uploaded_at": "2026-01-14T10:35:00Z"
    }
  ],
  "submissions": [
    {
      "id": "uuid",
      "method": "fax",
      "status": "delivered",
      "submitted_at": "2026-01-14T11:00:00Z",
      "confirmation_number": "FX123456"
    }
  ],
  "timeline": [
    {
      "event": "created",
      "timestamp": "2026-01-14T10:30:00Z",
      "user": "Dr. Jane Doe"
    },
    {
      "event": "document_uploaded",
      "timestamp": "2026-01-14T10:35:00Z",
      "user": "Dr. Jane Doe"
    },
    {
      "event": "submitted",
      "timestamp": "2026-01-14T11:00:00Z",
      "user": "System"
    }
  ],
  "created_at": "2026-01-14T10:30:00Z",
  "updated_at": "2026-01-14T11:00:00Z"
}
```

#### GET /pa/list

List all PA requests for the clinic.

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `status` (string, optional): `draft`, `pending_documents`, `ready_for_submission`, `submitted`, `approved`, `denied`, `appealed`
- `priority` (string, optional): `routine`, `urgent`, `emergent`
- `payer` (string, optional): Filter by payer name
- `from_date` (date, optional): Filter PAs created after this date
- `to_date` (date, optional): Filter PAs created before this date
- `search` (string, optional): Search by PA number or patient name
- `sort_by` (string, default: `created_at`): Field to sort by
- `sort_order` (string, default: `desc`): `asc` or `desc`

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "pa_number": "PA-2026-00123",
      "patient_name": "John Smith",
      "payer_name": "Blue Cross Blue Shield",
      "procedure_code": "99213",
      "status": "submitted",
      "priority": "routine",
      "submitted_at": "2026-01-14T11:00:00Z",
      "created_at": "2026-01-14T10:30:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_pages": 3,
    "total_items": 47,
    "has_next": true,
    "has_prev": false
  }
}
```

#### PATCH /pa/{id}

Update a PA request.

**Request:**
```json
{
  "status": "ready_for_submission",
  "medical_necessity": "Updated justification text...",
  "priority": "urgent"
}
```

**Response (200):** Returns updated PA object

#### DELETE /pa/{id}

Soft delete a PA request (only in draft status).

**Response (204):** No content

#### POST /pa/{id}/submit

Submit a PA request for processing.

**Request:**
```json
{
  "submission_method": "fax",
  "priority": "urgent"
}
```

**Response (200):**
```json
{
  "pa_id": "uuid",
  "submission_id": "uuid",
  "status": "queued",
  "estimated_delivery": "2026-01-14T11:30:00Z",
  "message": "PA submission queued successfully"
}
```

#### GET /pa/{id}/status-history

Retrieve status change history for a PA.

**Response (200):**
```json
{
  "pa_id": "uuid",
  "history": [
    {
      "status": "draft",
      "timestamp": "2026-01-14T10:30:00Z",
      "user": "Dr. Jane Doe",
      "note": "PA created"
    },
    {
      "status": "submitted",
      "timestamp": "2026-01-14T11:00:00Z",
      "user": "System",
      "note": "Submitted via fax"
    },
    {
      "status": "approved",
      "timestamp": "2026-01-17T14:22:00Z",
      "user": "System",
      "note": "Payer approved - Auth #AUTH123456"
    }
  ]
}
```

---

### Document Management

#### POST /documents/upload

Upload a clinical document.

**Request (multipart/form-data):**
```
file: <PDF binary>
patient_id: uuid
pa_id: uuid (optional)
document_type: clinical_note | lab_result | imaging | prescription | other
```

**Response (201):**
```json
{
  "id": "uuid",
  "file_name": "progress_note.pdf",
  "file_size_bytes": 1048576,
  "document_type": "clinical_note",
  "patient_id": "uuid",
  "pa_id": "uuid",
  "upload_status": "completed",
  "ocr_status": "pending",
  "extraction_status": "pending",
  "uploaded_at": "2026-01-14T10:35:00Z",
  "uploaded_by": {
    "id": "uuid",
    "name": "Dr. Jane Doe"
  }
}
```

#### GET /documents/{id}

Retrieve document metadata.

**Response (200):**
```json
{
  "id": "uuid",
  "file_name": "progress_note.pdf",
  "file_size_bytes": 1048576,
  "mime_type": "application/pdf",
  "document_type": "clinical_note",
  "patient_id": "uuid",
  "pa_id": "uuid",
  "ocr_completed": true,
  "extraction_completed": true,
  "ocr_confidence": 0.92,
  "extracted_data": {
    "patient_name": "John Smith",
    "dob": "1980-05-15",
    "visit_date": "2026-01-10",
    "diagnoses": [
      {
        "code": "E11.9",
        "description": "Type 2 diabetes",
        "confidence": 0.95
      }
    ],
    "procedures": [
      {
        "code": "99213",
        "description": "Office visit",
        "confidence": 0.88
      }
    ]
  },
  "uploaded_at": "2026-01-14T10:35:00Z",
  "processed_at": "2026-01-14T10:36:00Z"
}
```

#### GET /documents/{id}/download

Download the original document file.

**Response (200):**
- Content-Type: application/pdf
- Content-Disposition: attachment; filename="progress_note.pdf"
- Binary PDF content

#### POST /documents/{id}/extract

Trigger AI extraction on a document (if not auto-triggered).

**Response (202):**
```json
{
  "document_id": "uuid",
  "job_id": "uuid",
  "status": "queued",
  "message": "Extraction job queued successfully"
}
```

#### DELETE /documents/{id}

Delete a document.

**Response (204):** No content

---

### Submission Management

#### GET /submissions/{id}

Retrieve submission details.

**Response (200):**
```json
{
  "id": "uuid",
  "pa_id": "uuid",
  "submission_method": "fax",
  "status": "delivered",
  "fax_number": "+1-555-123-4567",
  "confirmation_number": "FX123456",
  "submitted_at": "2026-01-14T11:00:00Z",
  "delivered_at": "2026-01-14T11:05:00Z",
  "pages_sent": 12,
  "retry_count": 0,
  "error_message": null
}
```

#### POST /submissions/{id}/retry

Retry a failed submission.

**Response (200):**
```json
{
  "submission_id": "uuid",
  "new_attempt_id": "uuid",
  "status": "queued",
  "message": "Retry queued successfully"
}
```

#### GET /submissions/list

List all submissions for a clinic.

**Query Parameters:** Similar to PA list

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "pa_number": "PA-2026-00123",
      "submission_method": "fax",
      "status": "delivered",
      "submitted_at": "2026-01-14T11:00:00Z"
    }
  ],
  "pagination": {...}
}
```

---

### Appeal Management

#### POST /appeals

Create an appeal for a denied PA.

**Request:**
```json
{
  "pa_id": "uuid",
  "additional_evidence": [
    {
      "document_id": "uuid",
      "description": "Physical therapy notes showing 6-week trial"
    }
  ],
  "custom_justification": "Optional custom text to add to AI-generated letter"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "pa_id": "uuid",
  "appeal_number": "APL-2026-00045",
  "status": "draft",
  "denial_reasons_analyzed": [
    "Insufficient documentation of failed conservative treatment"
  ],
  "appeal_strategy": "Provide detailed PT trial documentation",
  "generated_letter": "Dear Appeals Reviewer,...",
  "success_likelihood": 0.70,
  "deadline": "2026-02-14",
  "created_at": "2026-01-14T12:00:00Z"
}
```

#### GET /appeals/{id}

Retrieve appeal details.

**Response (200):** Full appeal object

#### PATCH /appeals/{id}

Update appeal (e.g., edit generated letter).

**Request:**
```json
{
  "generated_letter": "Modified letter text...",
  "status": "approved"
}
```

**Response (200):** Updated appeal object

#### POST /appeals/{id}/submit

Submit an appeal.

**Response (200):**
```json
{
  "appeal_id": "uuid",
  "submission_id": "uuid",
  "status": "submitted",
  "submitted_at": "2026-01-14T13:00:00Z"
}
```

#### GET /appeals/list

List appeals for a clinic.

**Response (200):** Paginated list of appeals

---

### Analytics

#### GET /analytics/dashboard

Retrieve dashboard metrics for a clinic.

**Query Parameters:**
- `from_date` (date, optional)
- `to_date` (date, optional)
- `payer` (string, optional)

**Response (200):**
```json
{
  "period": {
    "from": "2026-01-01",
    "to": "2026-01-14"
  },
  "metrics": {
    "total_pas_submitted": 127,
    "total_approved": 98,
    "total_denied": 18,
    "total_pending": 11,
    "approval_rate": 0.77,
    "average_turnaround_days": 4.2,
    "total_appeals_filed": 12,
    "appeal_success_rate": 0.67
  },
  "by_payer": [
    {
      "payer_name": "Blue Cross Blue Shield",
      "total_submitted": 45,
      "approved": 38,
      "denied": 5,
      "approval_rate": 0.84,
      "avg_turnaround_days": 3.8
    }
  ],
  "by_procedure": [
    {
      "procedure_code": "99213",
      "description": "Office visit",
      "total_submitted": 32,
      "approval_rate": 0.91
    }
  ],
  "trends": {
    "weekly": [
      {
        "week_starting": "2026-01-07",
        "submitted": 23,
        "approved": 18,
        "denied": 3
      }
    ]
  }
}
```

#### GET /analytics/approval-rates

Detailed approval rate analysis.

**Query Parameters:**
- `from_date`, `to_date`
- `group_by`: `payer` | `procedure` | `diagnosis` | `provider`

**Response (200):**
```json
{
  "group_by": "payer",
  "data": [
    {
      "payer_name": "Blue Cross Blue Shield",
      "total_submitted": 45,
      "approved": 38,
      "denied": 5,
      "pending": 2,
      "approval_rate": 0.844,
      "denial_rate": 0.111
    }
  ]
}
```

#### GET /analytics/turnaround-times

Turnaround time analysis.

**Response (200):**
```json
{
  "overall": {
    "average_days": 4.2,
    "median_days": 3.0,
    "p95_days": 9.0
  },
  "by_payer": [
    {
      "payer_name": "Blue Cross Blue Shield",
      "average_days": 3.8,
      "median_days": 3.0
    }
  ],
  "distribution": {
    "0-2_days": 15,
    "3-5_days": 78,
    "6-10_days": 25,
    "11+_days": 9
  }
}
```

---

### User Management

#### GET /users/me

Get current user profile.

**Response (200):**
```json
{
  "id": "uuid",
  "email": "doctor@clinic.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "clinician",
  "clinic_id": "uuid",
  "clinic_name": "Main Street Clinic",
  "mfa_enabled": true,
  "preferences": {
    "email_notifications": true,
    "sms_notifications": false
  },
  "created_at": "2025-06-01T00:00:00Z",
  "last_login_at": "2026-01-14T09:00:00Z"
}
```

#### PATCH /users/me

Update current user profile.

**Request:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "preferences": {
    "email_notifications": false
  }
}
```

**Response (200):** Updated user object

#### POST /users/me/change-password

Change password.

**Request:**
```json
{
  "current_password": "old_password",
  "new_password": "new_secure_password"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

---

### Admin Endpoints

(Restricted to admin role)

#### GET /admin/users

List all users in the system.

**Response (200):** Paginated user list

#### POST /admin/users

Create a new user.

**Request:**
```json
{
  "email": "newdoctor@clinic.com",
  "first_name": "John",
  "last_name": "Smith",
  "role": "clinician",
  "clinic_id": "uuid"
}
```

**Response (201):** Created user object

#### PATCH /admin/users/{id}

Update a user (e.g., change role, deactivate).

**Request:**
```json
{
  "role": "admin",
  "is_active": false
}
```

**Response (200):** Updated user object

#### GET /admin/clinics

List all clinics.

**Response (200):** Paginated clinic list

#### POST /admin/clinics

Create a new clinic.

**Request:**
```json
{
  "name": "New Medical Center",
  "npi": "1234567890",
  "tax_id": "12-3456789",
  "address": {
    "street": "123 Main St",
    "city": "Boston",
    "state": "MA",
    "zip": "02101"
  },
  "phone": "+1-555-987-6543",
  "fax": "+1-555-987-6544"
}
```

**Response (201):** Created clinic object

---

## WebSocket Events

### Connection

```
ws://api.priorauth.ai/ws?token={jwt_token}
```

### Client → Server Messages

#### Subscribe to PA Updates

```json
{
  "action": "subscribe",
  "channel": "pa_updates",
  "clinic_id": "uuid"
}
```

#### Unsubscribe

```json
{
  "action": "unsubscribe",
  "channel": "pa_updates"
}
```

### Server → Client Messages

#### PA Status Changed

```json
{
  "event": "pa.status_changed",
  "data": {
    "pa_id": "uuid",
    "pa_number": "PA-2026-00123",
    "old_status": "submitted",
    "new_status": "approved",
    "auth_number": "AUTH123456",
    "timestamp": "2026-01-17T14:22:00Z"
  }
}
```

#### Document Processed

```json
{
  "event": "document.processed",
  "data": {
    "document_id": "uuid",
    "pa_id": "uuid",
    "extraction_completed": true,
    "confidence": 0.92
  }
}
```

#### Submission Completed

```json
{
  "event": "submission.completed",
  "data": {
    "submission_id": "uuid",
    "pa_id": "uuid",
    "status": "delivered",
    "confirmation_number": "FX123456"
  }
}
```

---

## Webhooks

Clinics can configure webhooks to receive notifications at their own endpoints.

### Configuration

Stored in clinic settings:

```json
{
  "webhook_url": "https://clinic-system.com/webhooks/pa",
  "webhook_secret": "secret_key_for_hmac_validation",
  "events": ["pa.approved", "pa.denied", "pa.info_requested"]
}
```

### Webhook Payload

```json
{
  "event": "pa.approved",
  "timestamp": "2026-01-17T14:22:00Z",
  "data": {
    "pa_id": "uuid",
    "pa_number": "PA-2026-00123",
    "auth_number": "AUTH123456",
    "effective_date": "2026-01-17",
    "expiration_date": "2026-07-17"
  }
}
```

### Signature Verification

Webhooks include an `X-Signature` header with HMAC-SHA256 signature:

```
X-Signature: sha256=abcdef123456...
```

Verify using:
```python
import hmac
import hashlib

signature = hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()
```

---

**End of API_SPEC.md**