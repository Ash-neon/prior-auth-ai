# Prior Authorization AI Platform - Data Flow Documentation

**Version:** 1.0.0  
**Last Updated:** January 14, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [End-to-End PA Workflow](#end-to-end-pa-workflow)
3. [Detailed Data Flows](#detailed-data-flows)
4. [Error Handling & Retry Logic](#error-handling--retry-logic)
5. [Data Transformation Points](#data-transformation-points)
6. [Security & PHI Handling](#security--phi-handling)

---

## Overview

This document describes how data flows through the Prior Authorization AI platform, from initial document upload through final approval/denial and potential appeals. Understanding these flows is critical for:

- System integration and debugging
- Performance optimization
- Compliance auditing
- Feature development

### Flow Notation

```
→   Synchronous flow (HTTP request/response)
⇢   Asynchronous flow (queue/event)
[S]  Storage operation
[AI] AI/ML processing
[EXT] External system integration
```

---

## End-to-End PA Workflow

### High-Level Flow

```
1. Document Upload
   ↓
2. OCR & Data Extraction
   ↓
3. AI Clinical Analysis
   ↓
4. Insurance Rule Matching
   ↓
5. PA Packet Generation
   ↓
6. Multi-Channel Submission
   ↓
7. Status Tracking & Monitoring
   ↓
8. Response Processing
   ↓
9. Approval/Denial Handling
   ↓
10. (If Denied) Appeal Generation & Resubmission
```

### Detailed Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: DOCUMENT INTAKE                                    │
└─────────────────────────────────────────────────────────────┘

User (Frontend)
  → POST /api/v1/documents/upload
    {file: PDF, patient_id, document_type}
  
  → API Gateway
    • Authenticate JWT token
    • Validate file size (<50MB)
    • Check file type (PDF only for MVP)
    • Rate limit check
  
  → Document Processing Service
    • Generate unique document ID
    • Scan for malware (ClamAV - future)
    • Upload to S3/MinIO [S]
    • Create document record in PostgreSQL [S]
    • Publish event: "document.uploaded"
    • Return document ID to frontend
  
  ← Response: {document_id, status: "uploaded"}

┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: OCR & TEXT EXTRACTION                              │
└─────────────────────────────────────────────────────────────┘

Celery Worker (triggered by "document.uploaded" event)
  ⇢ Fetch document from S3 [S]
  
  → OCR Engine (Tesseract)
    • Extract text from PDF
    • Preserve layout information
    • Handle multi-page documents
    • Clean and normalize text
  
  → Store extracted text in PostgreSQL [S]
    • Update document.ocr_text field
    • Set document.ocr_completed = TRUE
  
  ⇢ Publish event: "document.ocr_completed"

┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: AI CLINICAL DATA EXTRACTION                        │
└─────────────────────────────────────────────────────────────┘

AI Orchestration Service (triggered by "document.ocr_completed")
  → Retrieve extracted text from DB [S]
  
  → [AI] Claude API Request
    Prompt Template: "clinical_extraction_v1"
    Input: {document_text, document_type}
    
    Claude Processing:
      • Extract patient demographics
      • Identify ICD-10 diagnosis codes
      • Extract CPT procedure codes
      • Parse clinical notes
      • Identify dates, providers, facilities
      • Assign confidence scores
    
    Output (JSON):
    {
      "patient": {
        "name": "John Doe",
        "dob": "1980-05-15",
        "mrn": "12345"
      },
      "diagnoses": [
        {"code": "E11.9", "description": "Type 2 diabetes", "confidence": 0.95}
      ],
      "procedures": [
        {"code": "99213", "description": "Office visit", "confidence": 0.88}
      ],
      "clinical_summary": "...",
      "providers": [...],
      "dates": {...}
    }
  
  → Validation Layer
    • Validate ICD-10 codes against master list
    • Validate CPT codes
    • Check date formats
    • Flag low-confidence extractions
  
  → Store extraction results [S]
    • Insert into extracted_data table
    • Link to document_id and patient_id
    • Set document.extraction_completed = TRUE
  
  ⇢ Publish event: "extraction.completed"

┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: PA CREATION & MEDICAL NECESSITY ANALYSIS           │
└─────────────────────────────────────────────────────────────┘

PA Management Service (triggered manually or by extraction event)
  → Create PA Record [S]
    • Generate unique PA number
    • Link to patient, clinic, payer
    • Status: "draft"
  
  → [AI] Medical Necessity Analysis
    Claude API Request:
    Prompt Template: "medical_necessity_v1"
    Input: {
      diagnosis_codes,
      procedure_codes,
      clinical_notes,
      patient_history
    }
    
    Output:
    {
      "is_medically_necessary": true,
      "justification": "Patient has failed conservative treatment...",
      "supporting_evidence": [...],
      "alternative_treatments_tried": [...],
      "clinical_guidelines_cited": [...]
    }
  
  → Store medical necessity in PA record [S]
  
  ⇢ Publish event: "pa.created"

┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: INSURANCE RULE MATCHING                            │
└─────────────────────────────────────────────────────────────┘

Rule Engine Service (triggered by "pa.created")
  → Fetch insurance rules from DB [S]
    Filter by: payer_id, procedure_code, diagnosis_codes
  
  → Rule Matching Algorithm
    For each rule:
      • Check if procedure matches
      • Check if diagnosis qualifies
      • Verify patient eligibility criteria
      • Check for required documentation
      • Evaluate prior authorization requirements
  
  → Generate Requirements Checklist
    {
      "required_documents": [
        "Clinical notes from last 6 months",
        "Lab results showing HbA1c > 7%",
        "Documentation of failed oral medications"
      ],
      "missing_documents": ["Lab results"],
      "estimated_approval_likelihood": 0.75,
      "typical_turnaround_days": 5,
      "appeal_success_rate": 0.60
    }
  
  → Update PA with rule matching results [S]
  
  ⇢ Publish event: "rules.matched"
  
  → If missing documents:
    ⇢ Send notification to clinic staff
    • Email: "Missing documents for PA #12345"
    • In-app notification
    • Update PA status to "pending_documents"

┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: PA PACKET GENERATION                               │
└─────────────────────────────────────────────────────────────┘

PA Packet Generator Service (triggered by "rules.matched" or manual)
  → Fetch PA data and all related documents [S]
  
  → Select payer-specific form template
    • Load PDF template from templates/ directory
    • Identify fillable form fields
  
  → Auto-fill PDF Form
    Using pdf-lib or PyPDF2:
    • Map extracted data to form fields
    • Fill patient demographics
    • Fill provider information
    • Fill diagnosis/procedure codes
    • Fill dates and authorization details
  
  → [AI] Generate Clinical Justification Letter
    Claude API Request:
    Prompt Template: "justification_letter_v1"
    Input: {
      patient_info,
      diagnosis,
      procedure,
      medical_necessity,
      payer_requirements
    }
    
    Output: Formatted letter (2-3 pages) with:
    • Patient summary
    • Clinical history
    • Medical necessity explanation
    • Supporting evidence
    • Provider signature block
  
  → Assemble Complete PA Packet
    • Cover page (generated)
    • PA form (filled)
    • Clinical justification letter
    • Supporting documents (clinical notes, labs, etc.)
    • Combine into single PDF
  
  → Store PA packet [S]
    • Upload to S3/MinIO
    • Create pa_packets table record
    • Link to PA ID
  
  → Update PA status to "ready_for_submission" [S]
  
  ⇢ Publish event: "packet.generated"

┌─────────────────────────────────────────────────────────────┐
│ PHASE 7: MULTI-CHANNEL SUBMISSION                           │
└─────────────────────────────────────────────────────────────┘

Submission Orchestration Service
  → Determine submission method
    Decision tree:
    • If payer has API → Use API connector
    • Else if payer portal supported → Use RPA
    • Else → Use fax
  
  ┌─── METHOD A: FAX SUBMISSION ───┐
  │                                 │
  │ → [EXT] Twilio Fax API         │
  │   POST /v1/Faxes               │
  │   {                            │
  │     To: "+1-555-PAYER-FAX",    │
  │     MediaUrl: "s3://packet.pdf"│
  │   }                            │
  │                                 │
  │ ← Response:                    │
  │   {                            │
  │     sid: "FX123...",           │
  │     status: "queued"           │
  │   }                            │
  │                                 │
  │ → Store submission record [S]  │
  │   • submission_method: "fax"   │
  │   • external_id: "FX123..."    │
  │   • status: "queued"           │
  │                                 │
  └─────────────────────────────────┘
  
  ┌─── METHOD B: RPA PORTAL ───────┐
  │                                 │
  │ → Queue RPA job                │
  │   Playwright Script:           │
  │   1. Launch headless browser   │
  │   2. Navigate to payer portal  │
  │   3. Login with credentials    │
  │   4. Navigate to PA form       │
  │   5. Fill form fields          │
  │   6. Upload documents          │
  │   7. Submit form               │
  │   8. Capture confirmation #    │
  │   9. Take screenshot           │
  │   10. Close browser            │
  │                                 │
  │ → Handle potential issues:     │
  │   • CAPTCHA → Manual fallback  │
  │   • Session timeout → Retry    │
  │   • Portal maintenance → Delay │
  │                                 │
  │ → Store submission record [S]  │
  │                                 │
  └─────────────────────────────────┘
  
  ┌─── METHOD C: PAYER API ────────┐
  │                                 │
  │ → [EXT] Payer API              │
  │   POST /prior-auth/submit      │
  │   Headers: {                   │
  │     Authorization: "Bearer..." │
  │   }                            │
  │   Body: {                      │
  │     patient: {...},            │
  │     diagnosis: [...],          │
  │     procedure: {...},          │
  │     documents: [...]           │
  │   }                            │
  │                                 │
  │ ← Response:                    │
  │   {                            │
  │     auth_number: "PA-2024-...",│
  │     status: "submitted"        │
  │   }                            │
  │                                 │
  └─────────────────────────────────┘
  
  → Update PA record [S]
    • Set status to "submitted"
    • Record submission timestamp
    • Store confirmation number
  
  ⇢ Publish event: "pa.submitted"
  
  → Send notification to clinic staff
    • Email: "PA #12345 submitted successfully"
    • In-app notification

┌─────────────────────────────────────────────────────────────┐
│ PHASE 8: STATUS TRACKING & MONITORING                       │
└─────────────────────────────────────────────────────────────┘

Tracking Engine Service (continuous background process)
  → Scheduled polling jobs (every 4 hours for routine, 30 min for urgent)
  
  For each submitted PA:
    ┌─── FAX STATUS CHECK ───────────┐
    │                                 │
    │ → [EXT] Twilio Fax API         │
    │   GET /v1/Faxes/{sid}          │
    │                                 │
    │ ← Response:                    │
    │   {                            │
    │     status: "delivered",       │
    │     delivered_at: "..."        │
    │   }                            │
    │                                 │
    │ → If status changed:           │
    │   • Update submission record   │
    │   • Log status change          │
    │                                 │
    └─────────────────────────────────┘
    
    ┌─── PORTAL STATUS CHECK ────────┐
    │                                 │
    │ → Queue RPA scraping job       │
    │   Playwright Script:           │
    │   1. Login to portal           │
    │   2. Navigate to PA status     │
    │   3. Search for PA number      │
    │   4. Extract current status    │
    │   5. Download any responses    │
    │                                 │
    └─────────────────────────────────┘
    
    ┌─── API STATUS CHECK ───────────┐
    │                                 │
    │ → [EXT] Payer API              │
    │   GET /prior-auth/{id}/status  │
    │                                 │
    │ ← Response:                    │
    │   {                            │
    │     status: "approved",        │
    │     decision_date: "...",      │
    │     auth_number: "...",        │
    │     valid_through: "..."       │
    │   }                            │
    │                                 │
    └─────────────────────────────────┘
  
  → If status = "approved":
    ⇢ Update PA status to "approved" [S]
    ⇢ Send notification (email, SMS, in-app)
    ⇢ Publish event: "pa.approved"
  
  → If status = "denied":
    ⇢ Update PA status to "denied" [S]
    ⇢ Extract denial reason
    ⇢ Calculate appeal deadline
    ⇢ Send urgent notification
    ⇢ Publish event: "pa.denied"
  
  → If status = "more_info_needed":
    ⇢ Update PA status to "info_requested" [S]
    ⇢ Extract requested information
    ⇢ Send notification with details
    ⇢ Set reminder for response deadline

┌─────────────────────────────────────────────────────────────┐
│ PHASE 9: DENIAL & APPEAL HANDLING                           │
└─────────────────────────────────────────────────────────────┘

Appeal Engine Service (triggered by "pa.denied" event)
  → Fetch PA and denial details [S]
  
  → [AI] Denial Reason Analysis
    Claude API Request:
    Prompt Template: "denial_analysis_v1"
    Input: {
      denial_letter_text,
      original_pa_request,
      clinical_notes
    }
    
    Output:
    {
      "denial_category": "medical_necessity",
      "specific_reasons": [
        "Insufficient documentation of failed conservative treatment"
      ],
      "appeal_strategy": "Provide detailed trial of physical therapy",
      "required_additional_evidence": [
        "PT notes from 6-week trial",
        "Pain scores before/after PT"
      ],
      "success_likelihood": 0.70
    }
  
  → [AI] Generate Appeal Letter
    Claude API Request:
    Prompt Template: "appeal_letter_v1"
    Input: {
      denial_reasons,
      appeal_strategy,
      original_justification,
      additional_evidence
    }
    
    Output: Professional appeal letter with:
    • Formal header and greeting
    • Reference to original PA
    • Point-by-point response to denial reasons
    • New supporting evidence
    • Medical literature citations (future)
    • Strong closing argument
    • Physician signature block
  
  → Create Appeal Record [S]
    • Link to original PA
    • Store appeal letter
    • Status: "draft"
  
  → Manual Review Step (optional)
    • Notify physician for review/approval
    • Allow edits to appeal letter
    • Physician approves/rejects
  
  → If approved:
    ⇢ Assemble appeal packet (similar to Phase 6)
    ⇢ Submit via appropriate channel (similar to Phase 7)
    ⇢ Update appeal status to "submitted" [S]
    ⇢ Track appeal status (similar to Phase 8)

┌─────────────────────────────────────────────────────────────┐
│ PHASE 10: REAL-TIME UPDATES TO FRONTEND                     │
└─────────────────────────────────────────────────────────────┘

WebSocket Service
  ← Client connects: ws://api.example.com/ws?token={jwt}
  
  ← Subscribe to updates for clinic_id
  
  → On any status change event:
    ⇢ Publish to WebSocket
    {
      "event": "pa.status_changed",
      "pa_id": "uuid",
      "old_status": "submitted",
      "new_status": "approved",
      "timestamp": "2026-01-14T10:30:00Z"
    }
  
  → Frontend receives event
    • Update dashboard in real-time
    • Show toast notification
    • Play sound alert (optional)
    • Update PA detail view if open
```

---

## Detailed Data Flows

### Flow 1: Document Upload to Extraction

**Participants:** Frontend, API Gateway, Document Service, S3, PostgreSQL, AI Service, Claude API

```
┌─────────┐     ┌────────┐     ┌─────────┐     ┌──┐     ┌──────┐     ┌───────┐
│Frontend │     │  API   │     │Document │     │S3│     │ PG   │     │Claude │
│         │     │Gateway │     │ Service │     │  │     │ DB   │     │ API   │
└────┬────┘     └───┬────┘     └────┬────┘     └┬─┘     └──┬───┘     └───┬───┘
     │              │               │           │          │             │
     │─upload PDF──>│               │           │          │             │
     │              │─auth check───>│           │          │             │
     │              │<─authorized───│           │          │             │
     │              │               │           │          │             │
     │              │─forward req──>│           │          │             │
     │              │               │           │          │             │
     │              │               │─save PDF─>│          │             │
     │              │               │<─S3 URL───│          │             │
     │              │               │           │          │             │
     │              │               │─insert record──────>│             │
     │              │               │<─document_id────────│             │
     │              │               │           │          │             │
     │              │<─doc ID───────│           │          │             │
     │<─response────│               │           │          │             │
     │              │               │           │          │             │
     │              │               │─queue OCR job────────>│             │
     │              │               │           │          │             │
     │              │               │           │          │ (async)     │
     │              │               │─fetch PDF─────────>  │             │
     │              │               │           │          │             │
     │              │               │─OCR text────────────>│             │
     │              │               │           │          │             │
     │              │               │─extract request──────┼────────────>│
     │              │               │           │          │             │
     │              │               │<─extracted data──────┼─────────────│
     │              │               │           │          │             │
     │              │               │─save results────────>│             │
     │              │               │           │          │             │
     │─WebSocket────┼───────────────┼───status update─────>│             │
     │  notification│               │           │          │             │
     │              │               │           │          │             │
```

### Flow 2: PA Submission via Fax

```
┌──────────┐     ┌──────────┐     ┌────────┐     ┌──────────┐
│Submission│     │   Fax    │     │ Twilio │     │PostgreSQL│
│  Service │     │ Gateway  │     │  API   │     │    DB    │
└─────┬────┘     └────┬─────┘     └───┬────┘     └────┬─────┘
      │               │               │               │
      │─submit PA────>│               │               │
      │               │               │               │
      │               │─prepare PDF──>│               │
      │               │               │               │
      │               │─send fax─────>│               │
      │               │               │               │
      │               │<─fax SID──────│               │
      │               │               │               │
      │               │─store record─────────────────>│
      │               │               │               │
      │<─submitted────│               │               │
      │               │               │               │
      │               │ (polling)     │               │
      │               │─check status─>│               │
      │               │<─delivered────│               │
      │               │               │               │
      │               │─update status────────────────>│
      │               │               │               │
```

### Flow 3: Appeal Generation

```
┌───────┐     ┌──────┐     ┌────────┐     ┌───────┐     ┌──────────┐
│PA Svc │     │Appeal│     │ Claude │     │  PG   │     │Submission│
│       │     │Engine│     │  API   │     │  DB   │     │  Service │
└───┬───┘     └──┬───┘     └───┬────┘     └───┬───┘     └────┬─────┘
    │            │             │              │              │
    │─denied─────>│             │              │              │
    │  event      │             │              │              │
    │            │             │              │              │
    │            │─fetch denial────────────────>│              │
    │            │<─denial data─────────────────│              │
    │            │             │              │              │
    │            │─analyze─────>│              │              │
    │            │<─strategy────│              │              │
    │            │             │              │              │
    │            │─generate────>│              │              │
    │            │  letter      │              │              │
    │            │<─appeal text─│              │              │
    │            │             │              │              │
    │            │─save appeal─────────────────>│              │
    │            │             │              │              │
    │            │─submit appeal────────────────┼─────────────>│
    │            │             │              │              │
```

---

## Error Handling & Retry Logic

### Retry Strategies

#### OCR Failures
- **Retry:** 3 times with exponential backoff (1s, 2s, 4s)
- **Fallback:** Manual review queue
- **Notification:** Alert clinic staff if OCR confidence < 0.7

#### AI API Failures
- **Retry:** 5 times with exponential backoff (2s, 4s, 8s, 16s, 32s)
- **Fallback:** Queue for later processing
- **Circuit Breaker:** Stop requests if 50% fail in 5 minutes
- **Notification:** Alert DevOps if API down > 10 minutes

#### Fax Delivery Failures
- **Retry:** 3 attempts over 24 hours
- **Fallback:** Generate manual fax instructions for staff
- **Notification:** Immediate alert to clinic

#### Portal RPA Failures
- **Retry:** 2 attempts with 1-hour delay
- **Fallback:** Generate PDF submission packet for manual upload
- **Notification:** Alert clinic with manual instructions

#### Payer API Failures
- **Retry:** 5 times with exponential backoff
- **Fallback:** Switch to portal RPA or fax
- **Notification:** Log for DevOps review

### Dead Letter Queues

Failed jobs after all retries are moved to dead letter queues for manual review:

```
failed_ocr_jobs/
failed_extractions/
failed_submissions/
failed_status_checks/
```

Admin dashboard shows dead letter queue items for manual intervention.

---

## Data Transformation Points

### Point 1: PDF → Text (OCR)

**Input:** Binary PDF file  
**Process:** Tesseract OCR  
**Output:** Plain text with layout preservation  
**Quality Check:** Confidence score per word  

### Point 2: Text → Structured Data (AI Extraction)

**Input:** Plain text clinical notes  
**Process:** Claude API with structured prompts  
**Output:** JSON with patient, diagnosis, procedure, dates  
**Validation:** 
- ICD-10 code validation against master list
- CPT code validation
- Date format standardization
- Confidence threshold (0.7 minimum)

### Point 3: Structured Data → PDF Form

**Input:** Extracted JSON data  
**Process:** PDF form filling (pdf-lib)  
**Output:** Completed PA form  
**Validation:**
- Required fields populated
- Checkbox/dropdown values valid
- Signature fields identified

### Point 4: Multiple PDFs → Single Packet

**Input:** PA form + supporting documents  
**Process:** PDF merging  
**Output:** Single submission-ready PDF  
**Validation:**
- Page order correct
- Table of contents generated
- Total size < 25MB

### Point 5: Denial Letter → Appeal Strategy

**Input:** Denial letter text (PDF or text)  
**Process:** Claude API analysis  
**Output:** Structured appeal plan + generated letter  
**Validation:**
- Denial reasons identified
- Appeal strategy aligns with reasons
- Required evidence listed

---

## Security & PHI Handling

### PHI Data Flow Controls

1. **Encryption in Transit**
   - All API calls use TLS 1.3
   - WebSocket connections encrypted
   - External API calls over HTTPS

2. **Encryption at Rest**
   - PostgreSQL database encrypted (AES-256)
   - S3/MinIO objects encrypted
   - Redis encrypted (if PHI stored)

3. **PHI Minimization in Logs**
   - Patient names → [PATIENT_NAME]
   - DOB → [DOB]
   - SSN → [SSN]
   - MRN → [MRN]

4. **Access Logging**
   - Every PHI access logged with:
     - user_id
     - timestamp
     - resource_id
     - action (read/write/delete)
     - IP address

5. **Data Retention**
   - Documents: 7 years
   - Audit logs: 7 years
   - Operational logs: 90 days

### Data Flow Audit Trail

Every data transformation is logged:

```json
{
  "event_id": "uuid",
  "timestamp": "2026-01-14T10:30:00Z",
  "transformation": "pdf_to_text",
  "input_resource": "document:uuid",
  "output_resource": "extracted_data:uuid",
  "user_id": "uuid",
  "success": true,
  "confidence_score": 0.92,
  "processing_time_ms": 1234
}
```

---

## Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Document Upload | < 5s | Time to return document_id |
| OCR Processing | < 30s/page | Time to complete OCR |
| AI Extraction | < 15s | Claude API response time |
| PA Packet Generation | < 20s | Time to create final PDF |
| Fax Submission | < 60s | Time to queue fax |
| Status Check | < 10s | Time to update status |
| Dashboard Load | < 2s | Time to render PA list |
| WebSocket Latency | < 500ms | Event delivery time |

---

## Monitoring & Observability

### Key Metrics to Track

1. **Throughput Metrics**
   - PAs created per day
   - Documents processed per hour
   - Submissions sent per hour
   - Status checks performed per hour

2. **Latency Metrics**
   - API response times (p50, p95, p99)
   - Background job processing times
   - External API call times

3. **Error Rates**
   - OCR failures
   - AI extraction failures
   - Submission failures
   - API errors (4xx, 5xx)

4. **Business Metrics**
   - Approval rate
   - Average turnaround time
   - Appeal success rate
   - Time saved vs manual process

5. **System Health**
   - Database connection pool utilization
   - Redis memory usage
   - Queue depth
   - Worker utilization

---

**End of DATA_FLOW.md**