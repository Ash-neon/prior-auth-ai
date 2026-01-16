"""
Multi-Agent Protocol Definition
================================

This module defines the core protocol, schemas, and base classes for all agents
in the Prior Authorization AI platform. All agents must conform to these interfaces.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
import logging


# ==================== Agent Role Definitions ====================

class AgentRole(str, Enum):
    """Enumeration of all agent roles in the system."""
    
    COORDINATOR = "coordinator"
    CLINICAL_INTAKE = "clinical_intake"
    INSURANCE_COMPLIANCE = "insurance_compliance"
    PACKET_ASSEMBLY = "packet_assembly"
    SUBMISSION = "submission"
    TRACKING_RESPONSE = "tracking_response"
    APPEALS = "appeals"


class AgentStatus(str, Enum):
    """Agent execution status."""
    
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    ESCALATED = "escalated"


class TaskPriority(str, Enum):
    """Task priority levels."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


# ==================== Core Data Models ====================

class AgentTask(BaseModel):
    """
    Standard task structure for agent execution.
    All agents receive and produce AgentTask objects.
    """
    
    task_id: str = Field(description="Unique task identifier")
    pa_id: str = Field(description="Prior authorization ID this task relates to")
    agent_role: AgentRole = Field(description="Which agent should handle this")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input data specific to this task"
    )
    
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Shared context from previous agents"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task metadata (timestamps, retries, etc.)"
    )
    
    parent_task_id: Optional[str] = Field(
        default=None,
        description="ID of parent task if this is a subtask"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class AgentResult(BaseModel):
    """
    Standard result structure returned by all agents.
    """
    
    task_id: str
    agent_role: AgentRole
    status: AgentStatus
    
    output_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Output data produced by the agent"
    )
    
    next_agent: Optional[AgentRole] = Field(
        default=None,
        description="Which agent should run next (if any)"
    )
    
    next_task_input: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Input data for the next agent"
    )
    
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the result (0-1)"
    )
    
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools/services called"
    )
    
    execution_time_ms: Optional[int] = None
    retry_count: int = 0
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class AgentState(BaseModel):
    """
    Represents the current state of an agent workflow.
    Stored in database for workflow resumption.
    """
    
    workflow_id: str = Field(description="Unique workflow execution ID")
    pa_id: str
    
    current_agent: AgentRole
    current_task_id: str
    
    workflow_status: AgentStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    completed_agents: List[AgentRole] = Field(default_factory=list)
    failed_agents: List[AgentRole] = Field(default_factory=list)
    
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Shared context accessible by all agents"
    )
    
    history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Execution history for audit"
    )
    
    class Config:
        use_enum_values = True


class AgentContext(BaseModel):
    """
    Shared context passed between agents in a workflow.
    Contains accumulated data from all previous agents.
    """
    
    pa_id: str
    workflow_id: str
    clinic_id: str
    patient_id: str
    
    # Clinical data (accumulated by Clinical Intake Agent)
    clinical_data: Optional[Dict[str, Any]] = None
    
    # Insurance rules (determined by Insurance Compliance Agent)
    insurance_requirements: Optional[Dict[str, Any]] = None
    
    # PA packet info (created by Packet Assembly Agent)
    packet_info: Optional[Dict[str, Any]] = None
    
    # Submission details (from Submission Agent)
    submission_info: Optional[Dict[str, Any]] = None
    
    # Tracking status (from Tracking Agent)
    tracking_info: Optional[Dict[str, Any]] = None
    
    # Appeal details (from Appeals Agent)
    appeal_info: Optional[Dict[str, Any]] = None
    
    # Global metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.dict(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentContext":
        """Create from dictionary."""
        return cls(**data)


# ==================== Tool Call Structure ====================

class ToolCall(BaseModel):
    """Represents a call to an existing system service/tool."""
    
    tool_name: str = Field(description="Name of the tool/service")
    function_name: str = Field(description="Function or method to call")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    response: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None
    
    execution_time_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolRegistry:
    """
    Registry of available tools that agents can call.
    Maps tool names to actual service implementations.
    """
    
    _tools: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, name: str, tool: Any):
        """Register a tool."""
        cls._tools[name] = tool
    
    @classmethod
    def get(cls, name: str) -> Any:
        """Get a registered tool."""
        if name not in cls._tools:
            raise ValueError(f"Tool '{name}' not registered")
        return cls._tools[name]
    
    @classmethod
    def list_tools(cls) -> List[str]:
        """List all registered tools."""
        return list(cls._tools.keys())


# ==================== Base Agent Class ====================

class BaseAgent(ABC):
    """
    Abstract base class that all agents must inherit from.
    Provides common functionality and enforces interface contract.
    """
    
    def __init__(
        self,
        role: AgentRole,
        logger: Optional[logging.Logger] = None
    ):
        self.role = role
        self.logger = logger or logging.getLogger(f"agent.{role.value}")
        self.tool_registry = ToolRegistry()
    
    @abstractmethod
    async def execute(
        self,
        task: AgentTask,
        context: AgentContext
    ) -> AgentResult:
        """
        Execute the agent's primary function.
        
        Args:
            task: The task to execute
            context: Shared context from workflow
            
        Returns:
            AgentResult with output and next steps
        """
        pass
    
    @abstractmethod
    def get_required_tools(self) -> List[str]:
        """
        Return list of tools this agent requires.
        Used for dependency checking and validation.
        """
        pass
    
    async def validate_input(self, task: AgentTask) -> bool:
        """
        Validate input data before execution.
        Override in subclass for custom validation.
        """
        return True
    
    async def call_tool(
        self,
        tool_name: str,
        function_name: str,
        **parameters
    ) -> ToolCall:
        """
        Call a registered tool/service.
        
        Args:
            tool_name: Name of the tool
            function_name: Function to call
            **parameters: Function parameters
            
        Returns:
            ToolCall with response data
        """
        start_time = datetime.utcnow()
        tool_call = ToolCall(
            tool_name=tool_name,
            function_name=function_name,
            parameters=parameters
        )
        
        try:
            tool = self.tool_registry.get(tool_name)
            
            # Get the function
            if not hasattr(tool, function_name):
                raise AttributeError(
                    f"Tool '{tool_name}' has no function '{function_name}'"
                )
            
            func = getattr(tool, function_name)
            
            # Call the function
            result = await func(**parameters) if callable(func) else func
            
            tool_call.response = result
            tool_call.success = True
            
        except Exception as e:
            self.logger.error(
                f"Tool call failed: {tool_name}.{function_name} - {str(e)}"
            )
            tool_call.success = False
            tool_call.error = str(e)
        
        finally:
            end_time = datetime.utcnow()
            tool_call.execution_time_ms = int(
                (end_time - start_time).total_seconds() * 1000
            )
        
        return tool_call
    
    async def retry_with_backoff(
        self,
        func,
        max_retries: int = 3,
        base_delay: float = 1.0
    ):
        """
        Execute a function with exponential backoff retry.
        
        Args:
            func: Async function to execute
            max_retries: Maximum retry attempts
            base_delay: Base delay in seconds
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        import asyncio
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"All {max_retries} attempts failed: {e}"
                    )
        
        raise last_exception
    
    def log_execution(
        self,
        task: AgentTask,
        result: AgentResult,
        context: AgentContext
    ):
        """Log agent execution for audit trail."""
        log_entry = {
            "agent_role": self.role.value,
            "task_id": task.task_id,
            "pa_id": task.pa_id,
            "status": result.status.value,
            "execution_time_ms": result.execution_time_ms,
            "tools_used": result.tools_used,
            "confidence": result.confidence_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"Agent execution: {log_entry}")
        
        # Add to workflow history
        context.metadata.setdefault("execution_log", []).append(log_entry)


# ==================== Agent Communication Protocol ====================

class AgentMessage(BaseModel):
    """Message structure for inter-agent communication."""
    
    from_agent: AgentRole
    to_agent: AgentRole
    message_type: str  # "request", "response", "notification", "error"
    
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    correlation_id: Optional[str] = Field(
        default=None,
        description="ID to correlate request/response"
    )
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class AgentCommunicationBus:
    """
    Pub/sub bus for agent-to-agent communication.
    Allows agents to send messages without tight coupling.
    """
    
    def __init__(self):
        self._subscribers: Dict[AgentRole, List[callable]] = {}
    
    def subscribe(self, agent_role: AgentRole, callback: callable):
        """Subscribe to messages for a specific agent role."""
        if agent_role not in self._subscribers:
            self._subscribers[agent_role] = []
        self._subscribers[agent_role].append(callback)
    
    async def publish(self, message: AgentMessage):
        """Publish a message to subscribers."""
        if message.to_agent in self._subscribers:
            for callback in self._subscribers[message.to_agent]:
                await callback(message)
    
    def unsubscribe(self, agent_role: AgentRole, callback: callable):
        """Unsubscribe from messages."""
        if agent_role in self._subscribers:
            self._subscribers[agent_role].remove(callback)


# ==================== Workflow Orchestration ====================

class WorkflowDefinition(BaseModel):
    """
    Defines the sequence and dependencies of agents in a workflow.
    """
    
    workflow_name: str
    description: str
    
    # Ordered list of agents to execute
    agent_sequence: List[AgentRole]
    
    # Dependencies between agents (agent -> list of required agents)
    dependencies: Dict[AgentRole, List[AgentRole]] = Field(default_factory=dict)
    
    # Conditional routing rules
    routing_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Rules for conditional agent routing"
    )
    
    # Retry policies per agent
    retry_policies: Dict[AgentRole, Dict[str, Any]] = Field(default_factory=dict)
    
    # Timeout settings per agent (in seconds)
    timeouts: Dict[AgentRole, int] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


# Standard PA workflow definition
STANDARD_PA_WORKFLOW = WorkflowDefinition(
    workflow_name="standard_pa_workflow",
    description="Standard end-to-end prior authorization workflow",
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


# Appeal workflow (triggered on denial)
APPEAL_WORKFLOW = WorkflowDefinition(
    workflow_name="appeal_workflow",
    description="Appeal workflow for denied PAs",
    agent_sequence=[
        AgentRole.APPEALS,
        AgentRole.PACKET_ASSEMBLY,
        AgentRole.SUBMISSION,
        AgentRole.TRACKING_RESPONSE
    ],
    dependencies={
        AgentRole.PACKET_ASSEMBLY: [AgentRole.APPEALS],
        AgentRole.SUBMISSION: [AgentRole.PACKET_ASSEMBLY],
        AgentRole.TRACKING_RESPONSE: [AgentRole.SUBMISSION]
    },
    retry_policies={
        AgentRole.APPEALS: {"max_retries": 2, "base_delay": 2.0},
        AgentRole.PACKET_ASSEMBLY: {"max_retries": 3, "base_delay": 2.0},
        AgentRole.SUBMISSION: {"max_retries": 5, "base_delay": 5.0},
        AgentRole.TRACKING_RESPONSE: {"max_retries": 3, "base_delay": 10.0}
    },
    timeouts={
        AgentRole.APPEALS: 600,
        AgentRole.PACKET_ASSEMBLY: 600,
        AgentRole.SUBMISSION: 900,
        AgentRole.TRACKING_RESPONSE: 300
    }
)


# ==================== Utility Functions ====================

def create_task(
    pa_id: str,
    agent_role: AgentRole,
    input_data: Dict[str, Any],
    priority: TaskPriority = TaskPriority.NORMAL,
    parent_task_id: Optional[str] = None
) -> AgentTask:
    """Helper function to create a new agent task."""
    import uuid
    
    return AgentTask(
        task_id=str(uuid.uuid4()),
        pa_id=pa_id,
        agent_role=agent_role,
        priority=priority,
        input_data=input_data,
        parent_task_id=parent_task_id
    )


def create_context(
    pa_id: str,
    workflow_id: str,
    clinic_id: str,
    patient_id: str
) -> AgentContext:
    """Helper function to create a new agent context."""
    return AgentContext(
        pa_id=pa_id,
        workflow_id=workflow_id,
        clinic_id=clinic_id,
        patient_id=patient_id
    )


# ==================== Exports ====================

__all__ = [
    # Enums
    "AgentRole",
    "AgentStatus",
    "TaskPriority",
    
    # Core models
    "AgentTask",
    "AgentResult",
    "AgentState",
    "AgentContext",
    
    # Tool system
    "ToolCall",
    "ToolRegistry",
    
    # Base classes
    "BaseAgent",
    
    # Communication
    "AgentMessage",
    "AgentCommunicationBus",
    
    # Workflow
    "WorkflowDefinition",
    "STANDARD_PA_WORKFLOW",
    "APPEAL_WORKFLOW",
    
    # Helpers
    "create_task",
    "create_context"
]