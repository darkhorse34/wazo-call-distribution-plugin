"""Callback models for call distribution."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class CallbackRequest(Base):
    """Callback request model."""
    
    __tablename__ = 'call_distributor_callback_requests'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    queue_id = Column(Integer, ForeignKey('call_distributor_queues.id'), nullable=False)
    
    # Caller information
    caller_id = Column(String(64), nullable=False)
    callback_number = Column(String(32), nullable=False)
    original_position = Column(Integer)  # Position in queue when callback was requested
    original_wait_time = Column(Integer)  # Wait time in seconds when callback was requested
    
    # Callback scheduling
    requested_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    preferred_time = Column(DateTime)  # Optional preferred callback time
    expiry_time = Column(DateTime)  # When the callback request expires
    
    # Status tracking
    status = Column(Enum('pending', 'scheduled', 'in_progress', 'completed',
                        'failed', 'expired', 'cancelled',
                        name='callback_status'), nullable=False, default='pending')
    priority = Column(Integer, default=0)  # Higher number = higher priority
    attempts = Column(Integer, default=0)  # Number of callback attempts made
    last_attempt = Column(DateTime)  # Time of last callback attempt
    
    # Result information
    result = Column(String(32))  # 'success', 'no_answer', 'busy', etc.
    notes = Column(String(256))  # Additional notes about the callback
    
    # Agent assignment
    assigned_agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'))
    completed_by_agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'))
    
    # Relationships
    queue = relationship('Queue')
    assigned_agent = relationship('Agent', foreign_keys=[assigned_agent_id])
    completed_by_agent = relationship('Agent', foreign_keys=[completed_by_agent_id])
    
    def __repr__(self):
        return f'<CallbackRequest(caller_id={self.caller_id}, status={self.status})>'
    
    @property
    def to_dict(self):
        """Convert callback request to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'queue_id': self.queue_id,
            'caller_id': self.caller_id,
            'callback_number': self.callback_number,
            'original_position': self.original_position,
            'original_wait_time': self.original_wait_time,
            'requested_time': self.requested_time.isoformat() if self.requested_time else None,
            'preferred_time': self.preferred_time.isoformat() if self.preferred_time else None,
            'expiry_time': self.expiry_time.isoformat() if self.expiry_time else None,
            'status': self.status,
            'priority': self.priority,
            'attempts': self.attempts,
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None,
            'result': self.result,
            'notes': self.notes,
            'assigned_agent_id': self.assigned_agent_id,
            'completed_by_agent_id': self.completed_by_agent_id
        }

class CallbackSchedule(Base):
    """Callback schedule model for managing callback windows."""
    
    __tablename__ = 'call_distributor_callback_schedules'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    queue_id = Column(Integer, ForeignKey('call_distributor_queues.id'), nullable=False)
    
    # Schedule settings
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    enabled = Column(Boolean, default=True)
    
    # Time window settings
    start_time = Column(String(5), nullable=False)  # HH:MM format
    end_time = Column(String(5), nullable=False)  # HH:MM format
    days_of_week = Column(String(7), nullable=False)  # e.g., "1111100" for Mon-Fri
    
    # Callback settings
    max_concurrent = Column(Integer, default=5)  # Maximum concurrent callbacks
    retry_interval = Column(Integer, default=300)  # Seconds between retry attempts
    max_attempts = Column(Integer, default=3)  # Maximum number of retry attempts
    expiry_hours = Column(Integer, default=24)  # Hours until callback request expires
    
    # Relationship
    queue = relationship('Queue')
    
    def __repr__(self):
        return f'<CallbackSchedule(name={self.name}, queue_id={self.queue_id})>'
    
    @property
    def to_dict(self):
        """Convert callback schedule to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'queue_id': self.queue_id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'days_of_week': self.days_of_week,
            'max_concurrent': self.max_concurrent,
            'retry_interval': self.retry_interval,
            'max_attempts': self.max_attempts,
            'expiry_hours': self.expiry_hours
        }
