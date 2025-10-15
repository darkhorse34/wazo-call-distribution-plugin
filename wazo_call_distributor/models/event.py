"""Event models for call distribution."""

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class QueueMetrics(Base):
    """Queue metrics model for real-time and historical stats."""
    
    __tablename__ = 'call_distributor_queue_metrics'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    queue_id = Column(Integer, ForeignKey('call_distributor_queues.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Queue stats
    calls_waiting = Column(Integer, default=0)
    longest_wait = Column(Integer, default=0)  # seconds
    service_level = Column(Float, default=0.0)  # percentage
    abandoned_calls = Column(Integer, default=0)
    answered_calls = Column(Integer, default=0)
    average_wait = Column(Float, default=0.0)  # seconds
    average_talk = Column(Float, default=0.0)  # seconds
    
    # Agent stats
    agents_logged = Column(Integer, default=0)
    agents_available = Column(Integer, default=0)
    agents_on_call = Column(Integer, default=0)
    agents_paused = Column(Integer, default=0)
    
    # Relationship
    queue = relationship('Queue')
    
    def __repr__(self):
        return f'<QueueMetrics(queue_id={self.queue_id}, timestamp={self.timestamp})>'
    
    @property
    def to_dict(self):
        """Convert metrics to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'queue_id': self.queue_id,
            'timestamp': self.timestamp.isoformat(),
            'calls_waiting': self.calls_waiting,
            'longest_wait': self.longest_wait,
            'service_level': self.service_level,
            'abandoned_calls': self.abandoned_calls,
            'answered_calls': self.answered_calls,
            'average_wait': self.average_wait,
            'average_talk': self.average_talk,
            'agents_logged': self.agents_logged,
            'agents_available': self.agents_available,
            'agents_on_call': self.agents_on_call,
            'agents_paused': self.agents_paused
        }

class AgentMetrics(Base):
    """Agent metrics model for real-time and historical stats."""
    
    __tablename__ = 'call_distributor_agent_metrics'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Agent stats
    calls_taken = Column(Integer, default=0)
    total_talk_time = Column(Integer, default=0)  # seconds
    average_talk_time = Column(Float, default=0.0)  # seconds
    total_wrap_time = Column(Integer, default=0)  # seconds
    average_wrap_time = Column(Float, default=0.0)  # seconds
    occupancy_rate = Column(Float, default=0.0)  # percentage
    adherence_rate = Column(Float, default=0.0)  # percentage
    
    # Current state
    current_state = Column(String(32))  # 'available', 'on_call', 'paused', etc.
    state_duration = Column(Integer, default=0)  # seconds in current state
    
    # Relationship
    agent = relationship('Agent')
    
    def __repr__(self):
        return f'<AgentMetrics(agent_id={self.agent_id}, timestamp={self.timestamp})>'
    
    @property
    def to_dict(self):
        """Convert metrics to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'calls_taken': self.calls_taken,
            'total_talk_time': self.total_talk_time,
            'average_talk_time': self.average_talk_time,
            'total_wrap_time': self.total_wrap_time,
            'average_wrap_time': self.average_wrap_time,
            'occupancy_rate': self.occupancy_rate,
            'adherence_rate': self.adherence_rate,
            'current_state': self.current_state,
            'state_duration': self.state_duration
        }

class Event(Base):
    """Event model for tracking call lifecycle and system events."""
    
    __tablename__ = 'call_distributor_events'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Event type and source
    event_type = Column(Enum('call', 'agent', 'queue', 'system',
                           name='event_type'), nullable=False)
    event_name = Column(String(64), nullable=False)
    
    # Related entities
    queue_id = Column(Integer, ForeignKey('call_distributor_queues.id'))
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'))
    call_id = Column(String(64))
    
    # Event data
    data = Column(JSON)
    
    # Relationships
    queue = relationship('Queue')
    agent = relationship('Agent')
    
    def __repr__(self):
        return f'<Event(type={self.event_type}, name={self.event_name})>'
    
    @property
    def to_dict(self):
        """Convert event to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'event_name': self.event_name,
            'queue_id': self.queue_id,
            'agent_id': self.agent_id,
            'call_id': self.call_id,
            'data': self.data
        }
