# Multi-Agent Architecture Extension

**Version:** 1.0.0  
**Last Updated:** January 14, 2026  
**Status:** Phase 1B - Multi-Agent Integration

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Agent Specifications](#agent-specifications)
4. [Workflow Orchestration](#workflow-orchestration)
5. [Integration Points](#integration-points)
6. [Data Flow](#data-flow)
7. [Deployment](#deployment)
8. [Monitoring](#monitoring)

---

## Overview

The multi-agent system extends the existing Prior Authorization platform with an intelligent orchestration layer. Rather than replacing existing services, agents **use** the platform's tools, services, and AI engines through a standardized protocol.

### Key Design Principles

1. **Non-Invasive**: Agents sit on top of existing services
2. **Tool-Using**: All agents call existing backend services
3. **State-Aware**: Workflow state persisted in PostgreSQL
4. **Resumable**: Workflows can be paused and resumed
5. **Observable**: Full audit trail of agent actions

### Benefits

- **Autonomous Workflows**: End-to-end PA processing with minimal human intervention
- **Intelligent Routing**: Agents make context-aware decisions
- **Fault Tolerance**: Built-in retry logic and error handling
- **Flexibility**: Easy to add new agents or modify workflows
- **Auditability**: Complete execution history for compliance

---

## Architecture Design

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                            │
│              (Next.js Frontend - Existing)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     API GATEWAY                              │
│                (FastAPI - Existing)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              ★ MULTI-AGENT ORCHESTRATION LAYER ★            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Coordinator Agent (Supervisor)             │   │
│  └──────────────────────────────────────────────────────┘   │
│         │       │       │       │       │       │            │
│         ▼       ▼       ▼       ▼       ▼       ▼            │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │
│  │Clin-│ │Insur│ │Pack-│ │Submi│ │Track│ │Appea│           │
│  │ical │ │ance │ │  et │ │ssion│ │ ing │ │  ls │           │
│  │Intk │ │Compl│ │Asm. │ │Agent│ │Agent│ │Agent│           │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘           │
└─────────────────────────────────────────────────────────────┘
         │       │       │       │       │       │
         ▼       ▼       ▼       ▼       ▼       ▼
┌─────────────────────────────────────────────────────────────┐
│           EXISTING APPLICATION SERVICES                      │
│  • PA Service       • Document Service   • AI Service        │
│  • Submission Svc   • Tracking Service   • Appeal Service    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               EXISTING AI/ML & AUTOMATION                    │
│  • Claude API       • OCR Engine         • RPA Portal        │
│  • Rule Engine      • Fax Gateway        • Payer APIs        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  EXISTING DATA LAYER                         │
│  • PostgreSQL       • Redis              • S3/MinIO          │
└─────────────────────────────────────────────────────────────┘
```

### Agent Communication Flow

```
┌──────────────┐
│ User creates │
│   new PA     │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ API creates AgentTask│
│ workflow_type="std"  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│        COORDINATOR AGENT                     │
│  - Loads STANDARD_PA_WORKFLOW                │
│  - Creates AgentState                        │
│  - Starts workflow execution                 │
└──────┬───────────────────────────────────────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌─────────────────┐                  ┌─────────────────┐
│ Clinical Intake │ ──(success)───>  │ Insurance       │
│     Agent       │                  │ Compliance Agent│
│                 │                  │                 │
│ Tools:          │                  │ Tools:          │
│ - OCR Service   │                  │ - Rule Engine   │
│ - Claude API    │                  │ - Rules DB      │
│ - Validators    │                  │ - PA Service    │
└─────────────────┘                  └─────────┬───────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │ Packet Assembly │
                                    │     Agent       │
                                    │                 │
                                    │ Tools:          │
                                    │ - Packet Gen    │
                                    │ - Claude API    │
                                    │ - PDF Utils     │
                                    └─────────┬───────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │  Submission     │
                                    │     Agent       │
                                    │                 │
                                    │ Tools:          │
                                    │ - RPA Service   │
                                    │ - Fax Gateway   │
                                    │ - Payer APIs    │
                                    └─────────┬───────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │ Tracking/Resp.  │
                                    │     Agent       │
                                    │                 │
                                    │ Tools:          │
                                    │ - Tracking Svc  │
                                    │ - Status Poller │
                                    └─────────┬───────┘
                                              │
                                      ┌───────┴───────┐
                                      │               │
                                      ▼               ▼
                              ┌──────────┐    ┌──────────┐
                              │ APPROVED │    │ DENIED   │
                              │  (Done)  │    │ (Appeal) │
                              └──────────┘    └────┬─────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │   Appeals   │
                                            │    Agent    │
                                            └─────────────┘
```

---

## Agent Specifications

### 1. Clinical Intake Agent

**Purpose**: Extract and validate clinical data from documents

**Responsibilities**:
- Trigger OCR on uploaded documents
- Extract structured medical data using Claude API
- Validate ICD-10, CPT, LOINC codes
- Check for step-therapy compliance
- Flag missing clinical evidence
- Populate AgentContext.clinical_data

**Tools Used**:
- `document_service.get_document()`
- `ocr_worker.process_document()`
- `ai_service.extract_clinical_data()`
- `validators.validate_icd10()`
- `validators.validate_cpt()`

**Input Schema**:
```python
{
    "document_ids": List[str],
    "patient_id": str,
    "pa_id": str
}
```

**Output Schema**:
```python
{
    "clinical_data": {
        "patient": {...},
        "diagnoses": [...],
        "procedures": [...],
        "clinical_notes": str,
        "providers": [...],
        "medications": [...]
    },
    "validation_results": {
        "icd10_valid": bool,
        "cpt_valid": bool,
        "missing_fields": List[str]
    },
    "confidence_score": float
}
```

**Decision Logic**:
- If validation fails → escalate to manual review
- If confidence < 0.7 → flag for review
- If successful → proceed to Insurance Compliance Agent

---

### 2. Insurance Compliance Agent

**Purpose**: Match clinical data to payer-specific requirements

**Responsibilities**:
- Load payer-specific rules from rules_db
- Match diagnoses/procedures to coverage criteria
- Identify required documentation
- Check for pre-authorization requirements
- Determine approval likelihood
- Populate AgentContext.insurance_requirements

**Tools Used**:
- `rule_engine_service.match_rules()`
- `insurance_rule.query()`
- `pa_service.update_requirements()`

**Input Schema**:
```python
{
    "clinical_data": Dict[str, Any],
    "payer_id": str,
    "payer_name": str
}
```

**Output Schema**:
```python
{
    "insurance_requirements": {
        "required_documents": List[str],
        "missing_documents": List[str],
        "coverage_criteria_met": bool,
        "prior_auth_required": bool,
        "estimated_approval_likelihood": float
    },
    "matched_rules": List[Dict],
    "recommendations": List[str]
}
```

**Decision Logic**:
- If missing critical documents → escalate for document collection
- If coverage criteria not met → flag for review
- If successful → proceed to Packet Assembly Agent

---

### 3. Packet Assembly Agent

**Purpose**: Build complete PA submission packet

**Responsibilities**:
- Select correct payer form template
- Fill form with extracted data
- Generate clinical justification letter (AI)
- Assemble all supporting documents
- Create final submission-ready PDF
- Populate AgentContext.packet_info

**Tools Used**:
- `packet_generator.select_template()`
- `packet_generator.fill_form()`
- `ai_service.generate_justification()`
- `document_service.merge_pdfs()`
- `s3_service.upload_packet()`

**Input Schema**:
```python
{
    "clinical_data": Dict[str, Any],
    "insurance_requirements": Dict[str, Any],
    "supporting_document_ids": List[str]
}
```

**Output Schema**:
```python
{
    "packet_info": {
        "packet_id": str,
        "packet_url": str,
        "form_template": str,
        "pages": int,
        "size_bytes": int
    },
    "justification_letter": str,
    "assembly_log": List[str]
}
```

**Decision Logic**:
- If form template not found → escalate
- If PDF assembly fails → retry or escalate
- If successful → proceed to Submission Agent

---

### 4. Submission Agent

**Purpose**: Submit PA via appropriate channel

**Responsibilities**:
- Determine submission method (API > Portal > Fax)
- Handle authentication for payer portals
- Manage retries and throttling
- Handle CAPTCHA scenarios
- Record submission confirmation
- Populate AgentContext.submission_info

**Tools Used**:
- `submission_service.determine_method()`
- `fax_service.send_fax()`
- `rpa_portal.submit_form()`
- `insurer_api.submit_pa()`
- `submission_worker.queue_submission()`

**Input Schema**:
```python
{
    "packet_info": Dict[str, Any],
    "payer_id": str,
    "submission_preferences": Dict[str, Any]
}
```

**Output Schema**:
```python
{
    "submission_info": {
        "submission_id": str,
        "method": str,  # "api", "portal", "fax"
        "confirmation_number": Optional[str],
        "status": str,  # "sent", "delivered", "failed"
        "timestamp": datetime
    },
    "delivery_status": str,
    "retry_count": int
}
```

**Decision Logic**:
- If payer API available → use API
- Else if portal credentials exist → use RPA
- Else → use fax
- If all methods fail after retries → escalate

---

### 5. Tracking & Response Agent

**Purpose**: Monitor status and process responses

**Responsibilities**:
- Poll for status updates
- Parse response documents
- Detect status changes (approved/denied/info requested)
- Update PA record
- Trigger notifications
- Populate AgentContext.tracking_info

**Tools Used**:
- `tracking_service.poll_status()`
- `tracking_worker.schedule_check()`
- `ai_service.parse_response()`
- `notification_service.send_alert()`

**Input Schema**:
```python
{
    "submission_info": Dict[str, Any],
    "poll_interval": int  # seconds
}
```

**Output Schema**:
```python
{
    "tracking_info": {
        "current_status": str,  # "pending", "approved", "denied", etc.
        "decision_date": Optional[datetime],
        "auth_number": Optional[str],
        "denial_reason": Optional[str],
        "last_checked": datetime
    },
    "status_history": List[Dict],
    "next_action": str  # "wait", "appeal", "complete"
}
```

**Decision Logic**:
- If status = "approved" → workflow complete
- If status = "denied" → route to Appeals Agent
- If status = "info_requested" → escalate for document provision
- If status = "pending" → continue monitoring

---

### 6. Appeals Agent

**Purpose**: Generate and submit appeals for denials

**Responsibilities**:
- Analyze denial reasons
- Generate appeal strategy
- Create appeal letter (AI)
- Assemble appeal packet
- Submit appeal
- Populate AgentContext.appeal_info

**Tools Used**:
- `appeal_service.analyze_denial()`
- `ai_service.generate_appeal_letter()`
- `appeal_generator.create_strategy()`
- `packet_generator.create_appeal_packet()`

**Input Schema**:
```python
{
    "clinical_data": Dict[str, Any],
    "denial_info": Dict[str, Any],
    "original_packet_id": str
}
```

**Output Schema**:
```python
{
    "appeal_info": {
        "appeal_id": str,
        "denial_reasons_analyzed": List[str],
        "appeal_strategy": str,
        "appeal_letter": str,
        "success_likelihood": float,
        "appeal_deadline": datetime
    },
    "appeal_packet_id": str,
    "submitted": bool
}
```

**Decision Logic**:
- Analyze denial reasons
- Generate targeted appeal
- Route back to Packet Assembly → Submission → Tracking

---

### 7. Coordinator Agent (Supervisor)

**Purpose**: Orchestrate entire workflow

**Responsibilities**:
- Start and manage workflows
- Route tasks to agents
- Monitor execution
- Handle failures and retries
- Manage state persistence
- Coordinate handoffs
- Make routing decisions

**Key Methods**:
```python
async def start_workflow(pa_id, workflow_definition)
async def execute_agent_with_retry(agent, task, context)
async def determine_next_agent(current_result, context)
async def handle_agent_failure(agent, error)
async def resume_workflow(workflow_id)
async def cancel_workflow(workflow_id, reason)
```

**Decision Logic**:
- Follows WorkflowDefinition agent_sequence
- Checks dependencies before executing agents
- Applies retry policies per agent
- Routes based on agent results
- Escalates on repeated failures

---

## Workflow Orchestration

### Standard PA Workflow

```python
STANDARD_PA_WORKFLOW = WorkflowDefinition(
    workflow_name="standard_pa_workflow",
    agent_sequence=[
        AgentRole.CLINICAL_INTAKE,
        AgentRole.INSURANCE_COMPLIANCE,
        AgentRole.PACKET_ASSEMBLY,
        AgentRole.SUBMISSION,
        AgentRole.TRACKING_RESPONSE
    ],
    dependencies={
        AgentRole.INSURANCE_COMPLIANCE: [AgentRole.CLINICAL_INTAKE],
        AgentRole.PACKET_ASSEMBLY: [
            AgentRole.CLINICAL_INTAKE,
            AgentRole.INSURANCE_COMPLIANCE
        ],
        AgentRole.SUBMISSION: [AgentRole.PACKET_ASSEMBLY],
        AgentRole.TRACKING_RESPONSE: [AgentRole.SUBMISSION]
    },
    retry_policies={
        AgentRole.CLINICAL_INTAKE: {"max_retries": 2, "base_delay": 1.0},
        AgentRole.INSURANCE_COMPLIANCE: {"max_retries": 2, "base_delay": 1.0},
        AgentRole.PACKET_ASSEMBLY: {"max_retries": 3, "base_delay": 2.0},
        AgentRole.SUBMISSION: {"max_retries": 5, "base_delay": 5.0},
        AgentRole.TRACKING_RESPONSE: {"max_retries": 3, "base_delay": 10.0}
    },
    timeouts={
        AgentRole.CLINICAL_INTAKE: 300,  # 5 minutes
        AgentRole.INSURANCE_COMPLIANCE: 180,  # 3 minutes
        AgentRole.PACKET_ASSEMBLY: 600,  # 10 minutes
        AgentRole.SUBMISSION: 900,  # 15 minutes
        AgentRole.TRACKING_RESPONSE: 300  # 5 minutes
    }
)
```

### Appeal Workflow

Triggered when Tracking Agent detects denial:

```python
APPEAL_WORKFLOW = WorkflowDefinition(
    workflow_name="appeal_workflow",
    agent_sequence=[
        AgentRole.APPEALS,
        AgentRole.PACKET_ASSEMBLY,
        AgentRole.SUBMISSION,
        AgentRole.TRACKING_RESPONSE
    ],
    # ... (retry policies, timeouts, etc.)
)
```

### Workflow State Machine

```
START
  ↓
RUNNING ──┐
  ↓       │ (retry)
  ├─→ SUCCESS
  ├─→ FAILED
  ├─→ WAITING (escalated)
  └─→ RETRY ──┘
```

### State Persistence

All workflow state stored in PostgreSQL:

```sql
CREATE TABLE agent_workflow_states (
    workflow_id UUID PRIMARY KEY,
    pa_id UUID REFERENCES prior_authorizations(id),
    current_agent VARCHAR(50),
    current_task_id UUID,
    workflow_status VARCHAR(20),
    started_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_agents JSONB,
    failed_agents JSONB,
    context JSONB,  -- Full AgentContext serialized
    history JSONB,  -- Execution history
    metadata JSONB
);
```

---

## Integration Points

### 1. API Endpoints

New endpoints in `backend/api/v1/endpoints/agents.py`:

```python
POST /api/v1/agents/workflows/start
  # Start a new agent workflow
  Body: {
    "pa_id": str,
    "workflow_type": str,  # "standard_pa" or "appeal"
    "priority": str
  }
  Response: {
    "workflow_id": str,
    "status": str
  }

GET /api/v1/agents/workflows/{workflow_id}/status
  # Get workflow status
  Response: AgentState

POST /api/v1/agents/workflows/{workflow_id}/cancel
  # Cancel a running workflow
  Body: {"reason": str}

POST /api/v1/agents/workflows/{workflow_id}/resume
  # Resume a paused/failed workflow
```

### 2. Service Integration

Agents call existing services through tool registry:

```python
# In agent code:
result = await self.call_tool(
    tool_name="document_service",
    function_name="get_document",
    document_id=doc_id
)

# Tool registry maps to actual service:
ToolRegistry.register("document_service", document_service_instance)
```

### 3. Celery Integration

Agents execute as Celery tasks:

```python
# backend/workers/agent_worker.py
@celery_app.task
def execute_agent_workflow(workflow_id: str, pa_id: str):
    """Background task to execute agent workflow."""
    coordinator = get_coordinator()
    asyncio.run(
        coordinator.start_workflow(
            pa_id=pa_id,
            workflow=STANDARD_PA_WORKFLOW,
            initial_context=create_context(...)
        )
    )
```

### 4. WebSocket Events

Real-time workflow updates:

```python
# When agent completes
websocket.send({
    "event": "agent.completed",
    "workflow_id": workflow_id,
    "agent_role": agent_role,
    "status": status
})
```

---

## Data Flow

### AgentContext Flow

```
┌─────────────────────┐
│ Clinical Intake     │
│  adds:              │
│  - clinical_data    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Insurance Compliance│
│  adds:              │
│  - insurance_req    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Packet Assembly     │
│  adds:              │
│  - packet_info      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Submission          │
│  adds:              │
│  - submission_info  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Tracking/Response   │
│  adds:              │
│  - tracking_info    │
└─────────────────────┘
```

Each agent:
1. Reads from AgentContext
2. Performs its work using tools
3. Writes results back to AgentContext
4. Returns AgentResult to Coordinator

---

## Deployment

### Kubernetes Configuration

```yaml
# k8s/agent-coordinator-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-coordinator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agent-coordinator
  template:
    metadata:
      labels:
        app: agent-coordinator
    spec:
      containers:
      - name: coordinator
        image: priorauth/agent-coordinator:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secrets
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Celery Worker Configuration

```yaml
# k8s/agent-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-worker
spec:
  replicas: 4  # Scale based on load
  selector:
    matchLabels:
      app: agent-worker
  template:
    spec:
      containers:
      - name: worker
        image: priorauth/agent-worker:latest
        command: ["celery", "-A", "workers.agent_worker", "worker"]
        env:
        - name: CELERY_BROKER_URL
          value: "redis://redis:6379/0"
```

---

## Monitoring

### Metrics to Track

1. **Workflow Metrics**:
   - Workflows started/completed/failed per hour
   - Average workflow duration
   - Workflow success rate

2. **Agent Metrics**:
   - Agent execution time per agent role
   - Agent success/failure rate
   - Tool call success rate

3. **Business Metrics**:
   - End-to-end PA processing time
   - Autonomous completion rate (no human intervention)
   - Escalation rate

### Prometheus Metrics

```python
# In agent code
from prometheus_client import Counter, Histogram

agent_executions = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_role', 'status']
)

agent_duration = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration',
    ['agent_role']
)
```

### Grafana Dashboards

Create dashboards showing:
- Active workflows
- Agent execution timeline
- Failure rates and retry counts
- Tool call latencies
- Workflow completion funnel

---

## Future Enhancements

1. **Machine Learning Integration**:
   - Predict approval likelihood using historical data
   - Optimize agent routing based on success patterns
   - Anomaly detection for unusual workflows

2. **Advanced Routing**:
   - A/B testing different workflow configurations
   - Dynamic agent selection based on workload
   - Priority queue management

3. **Multi-Tenancy**:
   - Clinic-specific agent configurations
   - Custom workflow definitions per clinic
   - Isolated agent execution environments

4. **Human-in-the-Loop**:
   - Approval checkpoints for critical decisions
   - Expert review interface
   - Training mode for new agent behaviors

---

**End of Multi-Agent Architecture Documentation**