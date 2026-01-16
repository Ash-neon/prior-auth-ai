# Multi-Agent System Implementation Guide

**Version:** 1.0.0  
**Date:** January 14, 2026

---

## Implementation Roadmap

### Phase 1B: Multi-Agent Foundation (Current)

**Status:** ✅ COMPLETE

**Deliverables:**
- [x] Agent protocol definition (`agent_protocol.py`)
- [x] Coordinator agent implementation (`coordinator.py`)
- [x] Multi-agent architecture documentation
- [x] Workflow definitions (standard PA, appeal)
- [x] Integration specifications

### Phase 1B-Extended: Agent Implementations

**Estimated Duration:** 2-3 sessions

**Agent Implementation Order:**

1. **Clinical Intake Agent** (Priority: HIGH)
   - Implementation file: `ai-agents/clinical_intake_agent.py`
   - Depends on: document_service, ai_service, validators
   - Estimated: 4-6 hours

2. **Insurance Compliance Agent** (Priority: HIGH)
   - Implementation file: `ai-agents/insurance_compliance_agent.py`
   - Depends on: rule_engine_service, insurance_rules
   - Estimated: 4-6 hours

3. **Packet Assembly Agent** (Priority: HIGH)
   - Implementation file: `ai-agents/packet_assembly_agent.py`
   - Depends on: packet_generator, document_service
   - Estimated: 4-6 hours

4. **Submission Agent** (Priority: MEDIUM)
   - Implementation file: `ai-agents/submission_agent.py`
   - Depends on: fax_service, rpa_portal, insurer_apis
   - Estimated: 6-8 hours

5. **Tracking Agent** (Priority: MEDIUM)
   - Implementation file: `ai-agents/tracking_agent.py`
   - Depends on: tracking_service, notification_service
   - Estimated: 4-6 hours

6. **Appeals Agent** (Priority: LOW)
   - Implementation file: `ai-agents/appeals_agent.py`
   - Depends on: appeal_service, ai_service
   - Estimated: 4-6 hours

### Phase 1C: Integration & Testing

**Estimated Duration:** 1-2 sessions

**Tasks:**
1. Tool registry setup
2. API endpoint creation
3. Celery worker configuration
4. Database migration for workflow states
5. Unit tests for each agent
6. Integration tests for workflows
7. End-to-end workflow tests

---

## Sequence Diagrams

### 1. Standard PA Workflow - Happy Path

```
User          API         Coordinator    Clinical    Insurance    Packet      Submission  Tracking
 │             │               │          Intake      Compliance   Assembly                
 │─POST PA───>│               │            │             │            │           │           │
 │             │               │            │             │            │           │           │
 │             │─start_wf()──>│            │             │            │           │           │
 │             │               │            │             │            │           │           │
 │             │               │─execute──>│             │            │           │           │
 │             │               │            │             │            │           │           │
 │             │               │            │─OCR────────>│            │           │           │
 │             │               │            │─Claude─────>│            │           │           │
 │             │               │            │─validate───>│            │           │           │
 │             │               │            │             │            │           │           │
 │             │               │<──SUCCESS──│             │            │           │           │
 │             │               │            │             │            │           │           │
 │             │               │─execute───────────────>│            │           │           │
 │             │               │                         │            │           │           │
 │             │               │                         │─rules_db──>│           │           │
 │             │               │                         │─matcher───>│           │           │
 │             │               │                         │            │           │           │
 │             │               │<────SUCCESS─────────────│            │           │           │
 │             │               │                                      │           │           │
 │             │               │─execute──────────────────────────>│           │           │
 │             │               │                                      │           │           │
 │             │               │                                      │─template─>│           │
 │             │               │                                      │─Claude───>│           │
 │             │               │                                      │─merge────>│           │
 │             │               │                                      │           │           │
 │             │               │<────SUCCESS──────────────────────────│           │           │
 │             │               │                                                  │           │
 │             │               │─execute──────────────────────────────────────>│           │
 │             │               │                                                  │           │
 │             │               │                                                  │─RPA─────>│
 │             │               │                                                  │─or_fax──>│
 │             │               │                                                  │           │
 │             │               │<────SUCCESS──────────────────────────────────────│           │
 │             │               │                                                              │
 │             │               │─execute──────────────────────────────────────────────────>│
 │             │               │                                                              │
 │             │               │                                                              │─poll──>│
 │             │               │                                                              │        │
 │             │               │                                                              │<─status│
 │             │               │                                                              │        │
 │             │               │<────APPROVED─────────────────────────────────────────────────│        │
 │             │               │                                                                       │
 │             │<─notify_complete()                                                                   │
 │             │                                                                                       │
 │<──200 OK────│                                                                                       │
 │  workflow   │                                                                                       │
 │  complete   │                                                                                       │
```

### 2. Denial & Appeal Workflow

```
Tracking      Coordinator    Appeals      Packet       Submission    Tracking
   │               │           Agent       Assembly                      │
   │               │             │            │              │           │
   │─DENIED───────>│             │            │              │           │
   │               │             │            │              │           │
   │               │─start──────>│            │              │           │
   │               │  appeal_wf  │            │              │           │
   │               │             │            │              │           │
   │               │             │─analyze───>│              │           │
   │               │             │─Claude────>│              │           │
   │               │             │            │              │           │
   │               │<─SUCCESS────│            │              │           │
   │               │                          │              │           │
   │               │─execute─────────────────>│              │           │
   │               │                          │              │           │
   │               │                          │─build_appeal>│           │
   │               │                          │              │           │
   │               │<─SUCCESS─────────────────│              │           │
   │               │                                         │           │
   │               │─execute────────────────────────────────>│           │
   │               │                                         │           │
   │               │                                         │─submit──>│
   │               │                                         │           │
   │               │<─SUCCESS────────────────────────────────│           │
   │               │                                                     │
   │               │─execute────────────────────────────────────────────>│
   │               │                                                     │
   │               │                                                     │─monitor>│
   │               │                                                     │         │
```

### 3. Agent Failure & Retry

```
Coordinator    Agent     Tool/Service
     │           │            │
     │─execute─>│            │
     │           │            │
     │           │─call_tool─>│
     │           │            │
     │           │<─ERROR─────│
     │           │            │
     │<─FAILED───│            │
     │           │            │
     │ (wait 1s)              │
     │           │            │
     │─retry 1───>│            │
     │           │            │
     │           │─call_tool─>│
     │           │            │
     │           │<─ERROR─────│
     │           │            │
     │<─FAILED───│            │
     │           │            │
     │ (wait 2s)              │
     │           │            │
     │─retry 2───>│            │
     │           │            │
     │           │─call_tool─>│
     │           │            │
     │           │<─SUCCESS───│
     │           │            │
     │<─SUCCESS──│            │
     │ (retry_count=2)        │
```

### 4. Agent State Persistence

```
Coordinator    Database    Agent
     │             │          │
     │─start_wf()──│          │
     │             │          │
     │─save_state─>│          │
     │<─OK─────────│          │
     │             │          │
     │─execute────────────────>│
     │             │          │
     │             │          │
     │<─SUCCESS───────────────│
     │             │          │
     │─update_state>│          │
     │<─OK─────────│          │
     │             │          │
     │─execute────────────────>│
     │             │   (crash)│
     │             │          X
     │             │
     │ (later)     │
     │─resume_wf() │
     │             │
     │─load_state─>│
     │<─state──────│
     │             │
     │─execute────────────────>│
     │             │   (from  │
     │             │   saved  │
     │             │   state) │
```

---

## Code Structure

### Complete Directory Structure

```
backend/
├── ai-agents/                        # ★ NEW: Agent layer
│   ├── __init__.py
│   ├── agent_protocol.py            # ✅ Base protocol & interfaces
│   ├── coordinator.py               # ✅ Coordinator agent
│   ├── clinical_intake_agent.py     # TODO: Clinical intake
│   ├── insurance_compliance_agent.py # TODO: Insurance compliance
│   ├── packet_assembly_agent.py     # TODO: Packet assembly
│   ├── submission_agent.py          # TODO: Submission
│   ├── tracking_agent.py            # TODO: Tracking
│   ├── appeals_agent.py             # TODO: Appeals
│   └── tools/                       # Tool implementations
│       ├── __init__.py
│       ├── document_tools.py        # Document service wrappers
│       ├── ai_tools.py              # AI service wrappers
│       ├── submission_tools.py      # Submission service wrappers
│       └── tracking_tools.py        # Tracking service wrappers
│
├── api/
│   └── v1/
│       └── endpoints/
│           └── agents.py            # ★ NEW: Agent endpoints
│
├── models/
│   └── agent_workflow.py            # ★ NEW: AgentState model
│
├── workers/
│   └── agent_worker.py              # ★ NEW: Celery worker for agents
│
└── services/
    └── agent_service.py             # ★ NEW: Agent service layer

docs/
├── MULTI_AGENT_ARCHITECTURE.md      # ✅ Architecture documentation
└── AGENT_IMPLEMENTATION_GUIDE.md    # ✅ This file
```

---

## Database Schema Changes

### New Table: agent_workflow_states

```sql
CREATE TABLE agent_workflow_states (
    workflow_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pa_id UUID NOT NULL REFERENCES prior_authorizations(id),
    workflow_type VARCHAR(50) NOT NULL,  -- 'standard_pa', 'appeal'
    
    current_agent VARCHAR(50) NOT NULL,
    current_task_id UUID,
    
    workflow_status VARCHAR(20) NOT NULL,  -- 'running', 'success', 'failed', etc.
    
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    completed_agents JSONB DEFAULT '[]',  -- Array of completed agent roles
    failed_agents JSONB DEFAULT '[]',     -- Array of failed agent roles
    
    context JSONB NOT NULL DEFAULT '{}',  -- Serialized AgentContext
    history JSONB DEFAULT '[]',           -- Execution history
    
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (
        workflow_status IN ('idle', 'running', 'waiting', 'success', 'failed', 'retry', 'escalated')
    ),
    
    INDEX idx_workflow_pa_id (pa_id),
    INDEX idx_workflow_status (workflow_status),
    INDEX idx_workflow_created (started_at DESC)
);
```

### Alembic Migration

```python
# backend/alembic/versions/xxx_add_agent_workflows.py

def upgrade():
    op.create_table(
        'agent_workflow_states',
        sa.Column('workflow_id', UUID(), primary_key=True),
        sa.Column('pa_id', UUID(), nullable=False),
        sa.Column('workflow_type', sa.String(50), nullable=False),
        sa.Column('current_agent', sa.String(50), nullable=False),
        sa.Column('current_task_id', UUID()),
        sa.Column('workflow_status', sa.String(20), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('completed_agents', JSONB()),
        sa.Column('failed_agents', JSONB()),
        sa.Column('context', JSONB(), nullable=False),
        sa.Column('history', JSONB()),
        sa.Column('metadata', JSONB())
    )
    
    op.create_foreign_key(
        'fk_agent_workflow_pa',
        'agent_workflow_states',
        'prior_authorizations',
        ['pa_id'],
        ['id']
    )


def downgrade():
    op.drop_table('agent_workflow_states')
```

---

## API Integration

### 1. Start Agent Workflow Endpoint

```python
# backend/api/v1/endpoints/agents.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user
from ai_agents.coordinator import create_coordinator
from ai_agents.agent_protocol import create_context, TaskPriority
from schemas.agents import WorkflowStartRequest, WorkflowStartResponse

router = APIRouter()


@router.post("/workflows/start", response_model=WorkflowStartResponse)
async def start_agent_workflow(
    request: WorkflowStartRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Start a new multi-agent workflow for a PA.
    
    This creates an AgentTask and delegates to the Coordinator Agent.
    """
    # Get PA from database
    pa = db.query(PriorAuthorization).filter_by(id=request.pa_id).first()
    if not pa:
        raise HTTPException(status_code=404, detail="PA not found")
    
    # Verify user has access to this PA
    if pa.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create coordinator
    coordinator = create_coordinator(db)
    
    # Register all agents (this would be done once at startup in production)
    from ai_agents import (
        clinical_intake_agent,
        insurance_compliance_agent,
        # ... etc
    )
    coordinator.register_agent(clinical_intake_agent.ClinicalIntakeAgent())
    coordinator.register_agent(insurance_compliance_agent.InsuranceComplianceAgent())
    # ... register remaining agents
    
    # Create initial context
    context = create_context(
        pa_id=str(pa.id),
        workflow_id="",  # Will be set by coordinator
        clinic_id=str(pa.clinic_id),
        patient_id=str(pa.patient_id)
    )
    
    # Determine workflow type
    workflow_map = {
        "standard_pa": STANDARD_PA_WORKFLOW,
        "appeal": APPEAL_WORKFLOW
    }
    workflow = workflow_map.get(request.workflow_type)
    
    if not workflow:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow type: {request.workflow_type}"
        )
    
    # Start workflow (async)
    workflow_state = await coordinator.start_workflow(
        pa_id=str(pa.id),
        workflow=workflow,
        initial_context=context
    )
    
    return WorkflowStartResponse(
        workflow_id=workflow_state.workflow_id,
        status=workflow_state.workflow_status,
        started_at=workflow_state.started_at
    )
```

### 2. Get Workflow Status Endpoint

```python
@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current status of a workflow."""
    coordinator = create_coordinator(db)
    
    state = await coordinator.get_workflow_status(workflow_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Verify access
    pa = db.query(PriorAuthorization).filter_by(id=state.pa_id).first()
    if pa.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return state
```

---

## Tool Registry Setup

### Registering Services as Tools

```python
# backend/ai_agents/tools/__init__.py

from ai_agents.agent_protocol import ToolRegistry
from services import (
    document_service,
    ai_service,
    pa_service,
    packet_generator,
    submission_service,
    tracking_service,
    appeal_service
)


def register_all_tools():
    """Register all backend services as tools for agents."""
    
    # Document tools
    ToolRegistry.register("document_service", document_service)
    ToolRegistry.register("ocr_worker", ocr_worker)
    
    # AI tools
    ToolRegistry.register("ai_service", ai_service)
    ToolRegistry.register("extraction_service", extraction_service)
    
    # PA management
    ToolRegistry.register("pa_service", pa_service)
    
    # Rule engine
    ToolRegistry.register("rule_engine", rule_engine_service)
    
    # Packet generation
    ToolRegistry.register("packet_generator", packet_generator)
    
    # Submission
    ToolRegistry.register("fax_service", fax_service)
    ToolRegistry.register("rpa_portal", rpa_portal)
    ToolRegistry.register("insurer_api", insurer_api_connector)
    
    # Tracking
    ToolRegistry.register("tracking_service", tracking_service)
    
    # Appeals
    ToolRegistry.register("appeal_service", appeal_service)
    
    # Notifications
    ToolRegistry.register("notification_service", notification_service)
```

Call this at application startup:

```python
# backend/main.py

from ai_agents.tools import register_all_tools

@app.on_event("startup")
async def startup_event():
    # ... existing startup code
    
    # Register agent tools
    register_all_tools()
```

---

## Testing Strategy

### 1. Unit Tests per Agent

```python
# backend/ai_agents/tests/test_clinical_intake_agent.py

import pytest
from ai_agents.clinical_intake_agent import ClinicalIntakeAgent
from ai_agents.agent_protocol import create_task, create_context, AgentRole


@pytest.mark.asyncio
async def test_clinical_intake_success(mock_tools):
    """Test successful clinical data extraction."""
    
    agent = ClinicalIntakeAgent()
    
    task = create_task(
        pa_id="test-pa-123",
        agent_role=AgentRole.CLINICAL_INTAKE,
        input_data={
            "document_ids": ["doc-1", "doc-2"]
        }
    )
    
    context = create_context(
        pa_id="test-pa-123",
        workflow_id="workflow-456",
        clinic_id="clinic-789",
        patient_id="patient-111"
    )
    
    result = await agent.execute(task, context)
    
    assert result.status == AgentStatus.SUCCESS
    assert "clinical_data" in result.output_data
    assert context.clinical_data is not None
```

### 2. Integration Tests for Workflows

```python
# backend/ai_agents/tests/test_workflow_integration.py

@pytest.mark.asyncio
async def test_standard_pa_workflow_end_to_end(test_db):
    """Test complete standard PA workflow."""
    
    coordinator = create_coordinator(test_db)
    
    # Register all agents
    coordinator.register_agent(ClinicalIntakeAgent())
    coordinator.register_agent(InsuranceComplianceAgent())
    # ... etc
    
    # Start workflow
    workflow_state = await coordinator.start_workflow(
        pa_id="test-pa-123",
        workflow=STANDARD_PA_WORKFLOW,
        initial_context=test_context
    )
    
    # Wait for completion
    await asyncio.sleep(10)
    
    # Check final state
    final_state = await coordinator.get_workflow_status(workflow_state.workflow_id)
    
    assert final_state.workflow_status == AgentStatus.SUCCESS
    assert len(final_state.completed_agents) == 5
    assert AgentRole.CLINICAL_INTAKE in final_state.completed_agents
```

---

## Monitoring & Observability

### Prometheus Metrics

```python
# backend/ai_agents/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Workflow metrics
workflows_started = Counter(
    'agent_workflows_started_total',
    'Total agent workflows started',
    ['workflow_type']
)

workflows_completed = Counter(
    'agent_workflows_completed_total',
    'Total agent workflows completed',
    ['workflow_type', 'status']
)

workflow_duration = Histogram(
    'agent_workflow_duration_seconds',
    'Workflow execution duration',
    ['workflow_type'],
    buckets=[10, 30, 60, 300, 600, 1800, 3600]
)

# Agent metrics
agent_executions = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_role', 'status']
)

agent_duration = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration',
    ['agent_role'],
    buckets=[1, 5, 10, 30, 60, 300, 600]
)

agent_retry_count = Counter(
    'agent_retries_total',
    'Total agent retries',
    ['agent_role']
)

# Active workflows gauge
active_workflows = Gauge(
    'agent_active_workflows',
    'Number of currently active workflows'
)
```

### Logging Standards

```python
# All agents should log:
logger.info(
    f"Agent {self.role.value} starting execution",
    extra={
        "workflow_id": context.workflow_id,
        "pa_id": context.pa_id,
        "task_id": task.task_id
    }
)

logger.info(
    f"Agent {self.role.value} completed successfully",
    extra={
        "workflow_id": context.workflow_id,
        "execution_time_ms": result.execution_time_ms,
        "confidence": result.confidence_score,
        "tools_used": result.tools_used
    }
)
```

---

## Deployment Checklist

### Prerequisites

- [ ] Backend services (Phase 2-14) implemented and tested
- [ ] Database migrations applied
- [ ] Redis configured for Celery
- [ ] Tool registry initialized
- [ ] All agents implemented and tested

### Deployment Steps

1. **Deploy Database Changes**
   ```bash
   alembic upgrade head
   ```

2. **Deploy Backend with Agent Code**
   ```bash
   docker build -t priorauth/backend:agent-v1 .
   kubectl apply -f k8s/backend-deployment.yaml
   ```

3. **Deploy Agent Workers**
   ```bash
   kubectl apply -f k8s/agent-worker-deployment.yaml
   kubectl scale deployment agent-worker --replicas=4
   ```

4. **Verify Deployment**
   ```bash
   kubectl get pods -l app=agent-coordinator
   kubectl logs -f deployment/agent-coordinator
   ```

5. **Run Smoke Tests**
   ```bash
   python scripts/test_agent_workflow.py
   ```

---

## Troubleshooting

### Common Issues

**Issue**: Workflow stuck in "running" state

**Solution**:
- Check coordinator logs for errors
- Verify agent services are running
- Check database for workflow state
- Use `resume_workflow()` if needed

**Issue**: Agent keeps retrying

**Solution**:
- Check tool call errors in logs
- Verify service dependencies are healthy
- Review retry policy configuration
- Check for transient errors (network, API limits)

**Issue**: Context data missing between agents

**Solution**:
- Verify agents are writing to context
- Check context serialization/deserialization
- Review database for context JSONB field

---

## Next Steps

1. **Implement remaining agents** (Clinical Intake → Appeals)
2. **Create agent-specific tests**
3. **Set up monitoring dashboards**
4. **Run integration tests**
5. **Deploy to staging environment**
6. **Conduct user acceptance testing**
7. **Deploy to production**

---

**End of Implementation Guide**