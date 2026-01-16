"""
Coordinator Agent (Supervisor)
===============================

The Coordinator Agent is the supervisor that orchestrates the entire
multi-agent workflow. It manages agent handoffs, monitors progress,
handles failures, and ensures end-to-end PA workflow completion.

Responsibilities:
- Start and manage workflows
- Route tasks to appropriate agents
- Monitor agent execution
- Handle failures and retries
- Manage workflow state persistence
- Coordinate agent handoffs
- Make routing decisions based on context

Author: Prior Auth AI Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from agent_protocol import (
    BaseAgent,
    AgentRole,
    AgentTask,
    AgentResult,
    AgentContext,
    AgentState,
    AgentStatus,
    TaskPriority,
    WorkflowDefinition,
    STANDARD_PA_WORKFLOW,
    APPEAL_WORKFLOW,
    create_task,
    create_context
)


class CoordinatorAgent(BaseAgent):
    """
    Supervisor agent that orchestrates the multi-agent workflow.
    """
    
    def __init__(
        self,
        db_session,  # SQLAlchemy session for state persistence
        logger: Optional[logging.Logger] = None
    ):
        super().__init__(AgentRole.COORDINATOR, logger)
        self.db = db_session
        
        # Registry of available agents
        self.agents: Dict[AgentRole, BaseAgent] = {}
        
        # Active workflows
        self.active_workflows: Dict[str, AgentState] = {}
        
        # Workflow definitions
        self.workflows: Dict[str, WorkflowDefinition] = {
            "standard_pa": STANDARD_PA_WORKFLOW,
            "appeal": APPEAL_WORKFLOW
        }
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the coordinator."""
        self.agents[agent.role] = agent
        self.logger.info(f"Registered agent: {agent.role.value}")
    
    def get_required_tools(self) -> List[str]:
        """Coordinator doesn't directly use tools."""
        return []
    
    async def execute(
        self,
        task: AgentTask,
        context: AgentContext
    ) -> AgentResult:
        """
        Execute coordinator logic.
        This is typically called to start a new workflow.
        """
        self.logger.info(f"Coordinator executing task: {task.task_id}")
        
        # Determine which workflow to use
        workflow_type = task.input_data.get("workflow_type", "standard_pa")
        workflow = self.workflows.get(workflow_type)
        
        if not workflow:
            return AgentResult(
                task_id=task.task_id,
                agent_role=self.role,
                status=AgentStatus.FAILED,
                error_message=f"Unknown workflow type: {workflow_type}"
            )
        
        # Start the workflow
        try:
            workflow_state = await self.start_workflow(
                pa_id=task.pa_id,
                workflow=workflow,
                initial_context=context
            )
            
            return AgentResult(
                task_id=task.task_id,
                agent_role=self.role,
                status=AgentStatus.SUCCESS,
                output_data={
                    "workflow_id": workflow_state.workflow_id,
                    "status": workflow_state.workflow_status.value
                }
            )
            
        except Exception as e:
            self.logger.error(f"Workflow start failed: {e}")
            return AgentResult(
                task_id=task.task_id,
                agent_role=self.role,
                status=AgentStatus.FAILED,
                error_message=str(e)
            )
    
    async def start_workflow(
        self,
        pa_id: str,
        workflow: WorkflowDefinition,
        initial_context: AgentContext
    ) -> AgentState:
        """
        Start a new multi-agent workflow.
        
        Args:
            pa_id: Prior authorization ID
            workflow: Workflow definition
            initial_context: Initial context
            
        Returns:
            AgentState representing the workflow
        """
        workflow_id = str(uuid.uuid4())
        
        self.logger.info(
            f"Starting workflow: {workflow.workflow_name} "
            f"(ID: {workflow_id}, PA: {pa_id})"
        )
        
        # Create workflow state
        state = AgentState(
            workflow_id=workflow_id,
            pa_id=pa_id,
            current_agent=workflow.agent_sequence[0],
            current_task_id="",
            workflow_status=AgentStatus.RUNNING,
            context=initial_context.to_dict()
        )
        
        # Persist initial state
        await self._save_state(state)
        
        # Store in active workflows
        self.active_workflows[workflow_id] = state
        
        # Execute the workflow
        asyncio.create_task(
            self._execute_workflow(workflow_id, workflow, initial_context)
        )
        
        return state
    
    async def _execute_workflow(
        self,
        workflow_id: str,
        workflow: WorkflowDefinition,
        context: AgentContext
    ):
        """
        Execute a complete workflow by routing tasks through agents.
        
        Args:
            workflow_id: Workflow execution ID
            workflow: Workflow definition
            context: Shared context
        """
        state = self.active_workflows[workflow_id]
        
        try:
            for agent_role in workflow.agent_sequence:
                self.logger.info(
                    f"Workflow {workflow_id}: Executing agent {agent_role.value}"
                )
                
                # Check if dependencies are met
                if not await self._check_dependencies(
                    agent_role,
                    workflow,
                    state
                ):
                    raise ValueError(
                        f"Dependencies not met for agent: {agent_role.value}"
                    )
                
                # Get the agent
                agent = self.agents.get(agent_role)
                if not agent:
                    raise ValueError(f"Agent not registered: {agent_role.value}")
                
                # Create task for this agent
                task = create_task(
                    pa_id=state.pa_id,
                    agent_role=agent_role,
                    input_data={},
                    priority=TaskPriority.NORMAL
                )
                
                # Update state
                state.current_agent = agent_role
                state.current_task_id = task.task_id
                await self._save_state(state)
                
                # Execute agent with retries
                result = await self._execute_agent_with_retry(
                    agent=agent,
                    task=task,
                    context=context,
                    workflow=workflow
                )
                
                # Record execution in history
                state.history.append({
                    "agent_role": agent_role.value,
                    "task_id": task.task_id,
                    "status": result.status.value,
                    "timestamp": datetime.utcnow().isoformat(),
                    "execution_time_ms": result.execution_time_ms,
                    "confidence": result.confidence_score
                })
                
                # Handle result
                if result.status == AgentStatus.FAILED:
                    state.failed_agents.append(agent_role)
                    state.workflow_status = AgentStatus.FAILED
                    await self._save_state(state)
                    
                    self.logger.error(
                        f"Workflow {workflow_id}: Agent {agent_role.value} failed"
                    )
                    
                    # Trigger failure handling
                    await self._handle_agent_failure(
                        workflow_id,
                        agent_role,
                        result,
                        context
                    )
                    break
                
                elif result.status == AgentStatus.ESCALATED:
                    self.logger.warning(
                        f"Workflow {workflow_id}: Agent {agent_role.value} "
                        f"escalated - manual intervention required"
                    )
                    state.workflow_status = AgentStatus.WAITING
                    await self._save_state(state)
                    break
                
                else:
                    # Success - mark completed
                    state.completed_agents.append(agent_role)
                    await self._save_state(state)
                    
                    # Check for conditional routing
                    next_agent = await self._determine_next_agent(
                        current_agent=agent_role,
                        result=result,
                        workflow=workflow,
                        context=context
                    )
                    
                    if next_agent and next_agent != agent_role:
                        self.logger.info(
                            f"Workflow {workflow_id}: "
                            f"Conditional routing to {next_agent.value}"
                        )
                        # Handle conditional branching
                        # (Implementation depends on requirements)
            
            # Workflow completed successfully
            if state.workflow_status != AgentStatus.FAILED:
                state.workflow_status = AgentStatus.SUCCESS
                await self._save_state(state)
                
                self.logger.info(
                    f"Workflow {workflow_id} completed successfully"
                )
                
                # Trigger completion notifications
                await self._notify_workflow_complete(workflow_id, state, context)
        
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            state.workflow_status = AgentStatus.FAILED
            await self._save_state(state)
            
            # Trigger error notifications
            await self._notify_workflow_error(workflow_id, str(e), context)
        
        finally:
            # Cleanup
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
    
    async def _execute_agent_with_retry(
        self,
        agent: BaseAgent,
        task: AgentTask,
        context: AgentContext,
        workflow: WorkflowDefinition
    ) -> AgentResult:
        """
        Execute an agent with retry logic based on workflow configuration.
        
        Args:
            agent: The agent to execute
            task: Task to execute
            context: Shared context
            workflow: Workflow definition
            
        Returns:
            AgentResult
        """
        retry_policy = workflow.retry_policies.get(agent.role, {})
        max_retries = retry_policy.get("max_retries", 3)
        base_delay = retry_policy.get("base_delay", 1.0)
        
        timeout = workflow.timeouts.get(agent.role, 600)
        
        last_result = None
        
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Executing {agent.role.value} (attempt {attempt + 1}/{max_retries})"
                )
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    agent.execute(task, context),
                    timeout=timeout
                )
                
                result.retry_count = attempt
                
                # If successful, return immediately
                if result.status in [AgentStatus.SUCCESS, AgentStatus.ESCALATED]:
                    return result
                
                last_result = result
                
                # If failed but retries remain, wait and retry
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Agent {agent.role.value} failed on attempt {attempt + 1}, "
                        f"retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
            
            except asyncio.TimeoutError:
                self.logger.error(
                    f"Agent {agent.role.value} timed out after {timeout}s"
                )
                last_result = AgentResult(
                    task_id=task.task_id,
                    agent_role=agent.role,
                    status=AgentStatus.FAILED,
                    error_message=f"Execution timed out after {timeout}s",
                    retry_count=attempt
                )
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
            
            except Exception as e:
                self.logger.error(
                    f"Agent {agent.role.value} raised exception: {e}"
                )
                last_result = AgentResult(
                    task_id=task.task_id,
                    agent_role=agent.role,
                    status=AgentStatus.FAILED,
                    error_message=str(e),
                    retry_count=attempt
                )
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        return last_result
    
    async def _check_dependencies(
        self,
        agent_role: AgentRole,
        workflow: WorkflowDefinition,
        state: AgentState
    ) -> bool:
        """
        Check if all dependencies for an agent are satisfied.
        
        Args:
            agent_role: Agent to check
            workflow: Workflow definition
            state: Current workflow state
            
        Returns:
            True if dependencies are met
        """
        dependencies = workflow.dependencies.get(agent_role, [])
        
        for dep in dependencies:
            if dep not in state.completed_agents:
                self.logger.warning(
                    f"Dependency not met: {agent_role.value} requires {dep.value}"
                )
                return False
        
        return True
    
    async def _determine_next_agent(
        self,
        current_agent: AgentRole,
        result: AgentResult,
        workflow: WorkflowDefinition,
        context: AgentContext
    ) -> Optional[AgentRole]:
        """
        Determine the next agent based on current result and routing rules.
        
        Args:
            current_agent: Current agent
            result: Result from current agent
            workflow: Workflow definition
            context: Shared context
            
        Returns:
            Next agent role or None
        """
        # Check if agent explicitly specified next agent
        if result.next_agent:
            return result.next_agent
        
        # Apply routing rules from workflow
        routing_rules = workflow.routing_rules
        
        # Example conditional routing logic
        # (Extend based on specific business rules)
        
        if current_agent == AgentRole.TRACKING_RESPONSE:
            # Check if PA was denied
            tracking_info = context.tracking_info or {}
            status = tracking_info.get("status", "")
            
            if status == "denied":
                # Route to appeals agent
                return AgentRole.APPEALS
        
        # Default: no conditional routing
        return None
    
    async def _handle_agent_failure(
        self,
        workflow_id: str,
        agent_role: AgentRole,
        result: AgentResult,
        context: AgentContext
    ):
        """
        Handle agent failure (escalation, notifications, etc.).
        
        Args:
            workflow_id: Workflow ID
            agent_role: Failed agent
            result: Failure result
            context: Shared context
        """
        self.logger.error(
            f"Handling failure for {agent_role.value} in workflow {workflow_id}"
        )
        
        # Send notification to clinic staff
        # (Implementation would call notification_service)
        
        # Create audit log entry
        # (Implementation would call audit_service)
        
        # Potentially trigger manual review queue
        # (Implementation would update PA status in database)
    
    async def _notify_workflow_complete(
        self,
        workflow_id: str,
        state: AgentState,
        context: AgentContext
    ):
        """Notify relevant parties that workflow completed."""
        self.logger.info(f"Workflow {workflow_id} completed successfully")
        
        # Implementation would call notification service
        # to send emails/SMS to clinic staff
    
    async def _notify_workflow_error(
        self,
        workflow_id: str,
        error: str,
        context: AgentContext
    ):
        """Notify relevant parties of workflow error."""
        self.logger.error(f"Workflow {workflow_id} error: {error}")
        
        # Implementation would call notification service
    
    async def _save_state(self, state: AgentState):
        """
        Persist workflow state to database.
        
        Args:
            state: Workflow state to save
        """
        # Implementation would save to PostgreSQL agent_workflow_states table
        state.updated_at = datetime.utcnow()
        
        # Example pseudocode:
        # self.db.merge(state)
        # self.db.commit()
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """
        Resume a workflow from saved state.
        
        Args:
            workflow_id: Workflow to resume
            
        Returns:
            True if resumed successfully
        """
        # Load state from database
        # state = self.db.query(AgentState).filter_by(workflow_id=workflow_id).first()
        
        # Reconstruct context
        # context = AgentContext.from_dict(state.context)
        
        # Determine workflow type
        # workflow = self.workflows[...]
        
        # Resume from current agent
        # (Implementation would continue from state.current_agent)
        
        pass
    
    async def cancel_workflow(self, workflow_id: str, reason: str) -> bool:
        """
        Cancel an active workflow.
        
        Args:
            workflow_id: Workflow to cancel
            reason: Cancellation reason
            
        Returns:
            True if cancelled successfully
        """
        if workflow_id not in self.active_workflows:
            self.logger.warning(f"Workflow {workflow_id} not found")
            return False
        
        state = self.active_workflows[workflow_id]
        state.workflow_status = AgentStatus.FAILED
        state.history.append({
            "event": "cancelled",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await self._save_state(state)
        del self.active_workflows[workflow_id]
        
        self.logger.info(f"Workflow {workflow_id} cancelled: {reason}")
        return True
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[AgentState]:
        """
        Get current status of a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            AgentState or None if not found
        """
        # Check active workflows
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        # Load from database
        # state = self.db.query(AgentState).filter_by(workflow_id=workflow_id).first()
        # return state
        
        return None


# ==================== Coordinator Factory ====================

def create_coordinator(
    db_session,
    agents: Optional[List[BaseAgent]] = None
) -> CoordinatorAgent:
    """
    Factory function to create and initialize a coordinator.
    
    Args:
        db_session: Database session
        agents: List of agents to register
        
    Returns:
        Configured CoordinatorAgent
    """
    coordinator = CoordinatorAgent(db_session)
    
    if agents:
        for agent in agents:
            coordinator.register_agent(agent)
    
    return coordinator


# ==================== Exports ====================

__all__ = [
    "CoordinatorAgent",
    "create_coordinator"
]