"""Callback service for managing callback requests."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models import CallbackRequest, CallbackSchedule, Queue, Agent
from ..exceptions import QueueNotFound, AgentNotFound

class CallbackService:
    """Service for managing callback requests."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_callback_request(self, tenant_uuid: str,
                              request_data: Dict) -> CallbackRequest:
        """Create a new callback request."""
        queue = self.session.query(Queue).filter(
            Queue.id == request_data['queue_id'],
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue:
            raise QueueNotFound(request_data['queue_id'])
        
        # Get callback schedule for expiry calculation
        schedule = self.session.query(CallbackSchedule).filter(
            CallbackSchedule.queue_id == queue.id,
            CallbackSchedule.tenant_uuid == tenant_uuid,
            CallbackSchedule.enabled == True
        ).first()
        
        expiry_hours = schedule.expiry_hours if schedule else 24
        expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        request = CallbackRequest(
            tenant_uuid=tenant_uuid,
            expiry_time=expiry_time,
            **request_data
        )
        
        self.session.add(request)
        self.session.commit()
        return request
    
    def get_callback_request(self, request_id: int,
                           tenant_uuid: str) -> CallbackRequest:
        """Get a callback request by ID."""
        request = self.session.query(CallbackRequest).filter(
            CallbackRequest.id == request_id,
            CallbackRequest.tenant_uuid == tenant_uuid
        ).first()
        
        if not request:
            raise ValueError(f"Callback request {request_id} not found")
        
        return request
    
    def list_callback_requests(self, tenant_uuid: str,
                             queue_id: Optional[int] = None,
                             status: Optional[str] = None,
                             agent_id: Optional[int] = None) -> List[CallbackRequest]:
        """List callback requests with optional filters."""
        query = self.session.query(CallbackRequest).filter(
            CallbackRequest.tenant_uuid == tenant_uuid
        )
        
        if queue_id:
            query = query.filter(CallbackRequest.queue_id == queue_id)
        
        if status:
            query = query.filter(CallbackRequest.status == status)
        
        if agent_id:
            query = query.filter(
                or_(
                    CallbackRequest.assigned_agent_id == agent_id,
                    CallbackRequest.completed_by_agent_id == agent_id
                )
            )
        
        return query.order_by(CallbackRequest.priority.desc(),
                            CallbackRequest.requested_time.asc()).all()
    
    def update_callback_request(self, request_id: int, tenant_uuid: str,
                              request_data: Dict) -> CallbackRequest:
        """Update a callback request."""
        request = self.get_callback_request(request_id, tenant_uuid)
        
        for key, value in request_data.items():
            setattr(request, key, value)
        
        self.session.commit()
        return request
    
    def assign_callback_request(self, request_id: int, agent_id: int,
                              tenant_uuid: str) -> CallbackRequest:
        """Assign a callback request to an agent."""
        request = self.get_callback_request(request_id, tenant_uuid)
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        request.assigned_agent_id = agent_id
        request.status = 'scheduled'
        
        self.session.commit()
        return request
    
    def start_callback(self, request_id: int, agent_id: int,
                      tenant_uuid: str) -> CallbackRequest:
        """Start processing a callback request."""
        request = self.get_callback_request(request_id, tenant_uuid)
        
        if request.status not in ['pending', 'scheduled']:
            raise ValueError(f"Cannot start callback in status: {request.status}")
        
        request.status = 'in_progress'
        request.assigned_agent_id = agent_id
        request.attempts += 1
        request.last_attempt = datetime.utcnow()
        
        self.session.commit()
        return request
    
    def complete_callback(self, request_id: int, agent_id: int,
                         tenant_uuid: str, result: str,
                         notes: Optional[str] = None) -> CallbackRequest:
        """Complete a callback request."""
        request = self.get_callback_request(request_id, tenant_uuid)
        
        if request.status != 'in_progress':
            raise ValueError(f"Cannot complete callback in status: {request.status}")
        
        request.status = 'completed'
        request.completed_by_agent_id = agent_id
        request.result = result
        request.notes = notes
        
        self.session.commit()
        return request
    
    def fail_callback(self, request_id: int, tenant_uuid: str,
                     result: str, notes: Optional[str] = None,
                     retry: bool = True) -> CallbackRequest:
        """Mark a callback request as failed."""
        request = self.get_callback_request(request_id, tenant_uuid)
        schedule = self.session.query(CallbackSchedule).filter(
            CallbackSchedule.queue_id == request.queue_id,
            CallbackSchedule.tenant_uuid == tenant_uuid,
            CallbackSchedule.enabled == True
        ).first()
        
        if retry and request.attempts < (schedule.max_attempts if schedule else 3):
            request.status = 'pending'
            request.assigned_agent_id = None
        else:
            request.status = 'failed'
        
        request.result = result
        request.notes = notes
        
        self.session.commit()
        return request
    
    def cancel_callback(self, request_id: int, tenant_uuid: str,
                       notes: Optional[str] = None) -> CallbackRequest:
        """Cancel a callback request."""
        request = self.get_callback_request(request_id, tenant_uuid)
        
        if request.status in ['completed', 'failed', 'expired', 'cancelled']:
            raise ValueError(f"Cannot cancel callback in status: {request.status}")
        
        request.status = 'cancelled'
        request.notes = notes
        
        self.session.commit()
        return request
    
    def get_callback_schedule(self, schedule_id: int,
                            tenant_uuid: str) -> CallbackSchedule:
        """Get a callback schedule by ID."""
        schedule = self.session.query(CallbackSchedule).filter(
            CallbackSchedule.id == schedule_id,
            CallbackSchedule.tenant_uuid == tenant_uuid
        ).first()
        
        if not schedule:
            raise ValueError(f"Callback schedule {schedule_id} not found")
        
        return schedule
    
    def list_callback_schedules(self, tenant_uuid: str,
                              queue_id: Optional[int] = None) -> List[CallbackSchedule]:
        """List callback schedules."""
        query = self.session.query(CallbackSchedule).filter(
            CallbackSchedule.tenant_uuid == tenant_uuid
        )
        
        if queue_id:
            query = query.filter(CallbackSchedule.queue_id == queue_id)
        
        return query.all()
    
    def create_callback_schedule(self, tenant_uuid: str,
                               schedule_data: Dict) -> CallbackSchedule:
        """Create a new callback schedule."""
        queue = self.session.query(Queue).filter(
            Queue.id == schedule_data['queue_id'],
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue:
            raise QueueNotFound(schedule_data['queue_id'])
        
        schedule = CallbackSchedule(
            tenant_uuid=tenant_uuid,
            **schedule_data
        )
        
        self.session.add(schedule)
        self.session.commit()
        return schedule
    
    def update_callback_schedule(self, schedule_id: int, tenant_uuid: str,
                               schedule_data: Dict) -> CallbackSchedule:
        """Update a callback schedule."""
        schedule = self.get_callback_schedule(schedule_id, tenant_uuid)
        
        for key, value in schedule_data.items():
            setattr(schedule, key, value)
        
        self.session.commit()
        return schedule
    
    def delete_callback_schedule(self, schedule_id: int,
                               tenant_uuid: str) -> None:
        """Delete a callback schedule."""
        schedule = self.get_callback_schedule(schedule_id, tenant_uuid)
        self.session.delete(schedule)
        self.session.commit()
    
    def process_expired_callbacks(self, tenant_uuid: str) -> int:
        """Process expired callback requests."""
        now = datetime.utcnow()
        expired = self.session.query(CallbackRequest).filter(
            CallbackRequest.tenant_uuid == tenant_uuid,
            CallbackRequest.status.in_(['pending', 'scheduled']),
            CallbackRequest.expiry_time <= now
        ).all()
        
        count = 0
        for request in expired:
            request.status = 'expired'
            request.notes = 'Callback request expired'
            count += 1
        
        self.session.commit()
        return count
    
    def get_next_callback(self, agent_id: int,
                         tenant_uuid: str) -> Optional[CallbackRequest]:
        """Get the next callback request for an agent."""
        now = datetime.utcnow()
        
        # Get agent's queues
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        queue_ids = [member.queue_id for member in agent.queue_members]
        
        # Find the next available callback request
        request = self.session.query(CallbackRequest).filter(
            CallbackRequest.tenant_uuid == tenant_uuid,
            CallbackRequest.queue_id.in_(queue_ids),
            CallbackRequest.status.in_(['pending', 'scheduled']),
            or_(
                CallbackRequest.preferred_time == None,
                CallbackRequest.preferred_time <= now
            ),
            CallbackRequest.expiry_time > now
        ).order_by(
            CallbackRequest.priority.desc(),
            CallbackRequest.requested_time.asc()
        ).first()
        
        return request
