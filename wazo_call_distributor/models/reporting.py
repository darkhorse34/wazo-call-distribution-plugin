"""Reporting models for analytics and data aggregation."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class Report(Base):
    """Report model for saved report configurations."""
    
    __tablename__ = 'call_distributor_reports'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Report type and configuration
    report_type = Column(String(32), nullable=False)  # 'queue', 'agent', 'callback', etc.
    config = Column(JSON, nullable=False)  # Report configuration
    
    # Schedule settings
    schedule_enabled = Column(Boolean, default=False)
    schedule_interval = Column(String(32))  # 'daily', 'weekly', 'monthly'
    schedule_time = Column(String(5))  # HH:MM format
    schedule_day = Column(Integer)  # Day of week/month
    
    # Export settings
    export_format = Column(String(16))  # 'csv', 'json', 'xlsx'
    export_recipients = Column(JSON)  # List of email recipients
    
    # Last run information
    last_run = Column(DateTime)
    last_status = Column(String(32))
    
    def __repr__(self):
        return f'<Report(name={self.name}, type={self.report_type})>'
    
    @property
    def to_dict(self):
        """Convert report to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'description': self.description,
            'report_type': self.report_type,
            'config': self.config,
            'schedule_enabled': self.schedule_enabled,
            'schedule_interval': self.schedule_interval,
            'schedule_time': self.schedule_time,
            'schedule_day': self.schedule_day,
            'export_format': self.export_format,
            'export_recipients': self.export_recipients,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_status': self.last_status
        }

class QueueStats(Base):
    """Queue statistics model for historical data."""
    
    __tablename__ = 'call_distributor_queue_stats'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    queue_id = Column(Integer, ForeignKey('call_distributor_queues.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    interval = Column(String(16), nullable=False)  # '1min', '5min', '1hour', '1day'
    
    # Call volume metrics
    total_calls = Column(Integer, default=0)
    answered_calls = Column(Integer, default=0)
    abandoned_calls = Column(Integer, default=0)
    transferred_calls = Column(Integer, default=0)
    
    # Time metrics (in seconds)
    total_wait_time = Column(Integer, default=0)
    total_talk_time = Column(Integer, default=0)
    max_wait_time = Column(Integer, default=0)
    
    # Service level metrics
    service_level_calls = Column(Integer, default=0)  # Calls answered within SLA
    service_level_target = Column(Integer)  # SLA target in seconds
    
    # Agent metrics
    total_agents = Column(Integer, default=0)
    available_agents = Column(Integer, default=0)
    busy_agents = Column(Integer, default=0)
    
    # Calculated metrics
    average_wait_time = Column(Float, default=0.0)
    average_talk_time = Column(Float, default=0.0)
    service_level_ratio = Column(Float, default=0.0)
    abandon_rate = Column(Float, default=0.0)
    
    # Relationship
    queue = relationship('Queue')
    
    def __repr__(self):
        return f'<QueueStats(queue_id={self.queue_id}, interval={self.interval})>'
    
    @property
    def to_dict(self):
        """Convert stats to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'queue_id': self.queue_id,
            'timestamp': self.timestamp.isoformat(),
            'interval': self.interval,
            'total_calls': self.total_calls,
            'answered_calls': self.answered_calls,
            'abandoned_calls': self.abandoned_calls,
            'transferred_calls': self.transferred_calls,
            'total_wait_time': self.total_wait_time,
            'total_talk_time': self.total_talk_time,
            'max_wait_time': self.max_wait_time,
            'service_level_calls': self.service_level_calls,
            'service_level_target': self.service_level_target,
            'total_agents': self.total_agents,
            'available_agents': self.available_agents,
            'busy_agents': self.busy_agents,
            'average_wait_time': self.average_wait_time,
            'average_talk_time': self.average_talk_time,
            'service_level_ratio': self.service_level_ratio,
            'abandon_rate': self.abandon_rate
        }

class AgentStats(Base):
    """Agent statistics model for historical data."""
    
    __tablename__ = 'call_distributor_agent_stats'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    interval = Column(String(16), nullable=False)  # '1min', '5min', '1hour', '1day'
    
    # Call metrics
    total_calls = Column(Integer, default=0)
    answered_calls = Column(Integer, default=0)
    missed_calls = Column(Integer, default=0)
    outbound_calls = Column(Integer, default=0)
    
    # Time metrics (in seconds)
    total_login_time = Column(Integer, default=0)
    total_talk_time = Column(Integer, default=0)
    total_pause_time = Column(Integer, default=0)
    total_wrap_up_time = Column(Integer, default=0)
    total_idle_time = Column(Integer, default=0)
    
    # Status durations (in seconds)
    available_time = Column(Integer, default=0)
    busy_time = Column(Integer, default=0)
    dnd_time = Column(Integer, default=0)
    
    # Calculated metrics
    average_talk_time = Column(Float, default=0.0)
    average_wrap_up_time = Column(Float, default=0.0)
    occupancy_rate = Column(Float, default=0.0)
    utilization_rate = Column(Float, default=0.0)
    
    # Relationship
    agent = relationship('Agent')
    
    def __repr__(self):
        return f'<AgentStats(agent_id={self.agent_id}, interval={self.interval})>'
    
    @property
    def to_dict(self):
        """Convert stats to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'interval': self.interval,
            'total_calls': self.total_calls,
            'answered_calls': self.answered_calls,
            'missed_calls': self.missed_calls,
            'outbound_calls': self.outbound_calls,
            'total_login_time': self.total_login_time,
            'total_talk_time': self.total_talk_time,
            'total_pause_time': self.total_pause_time,
            'total_wrap_up_time': self.total_wrap_up_time,
            'total_idle_time': self.total_idle_time,
            'available_time': self.available_time,
            'busy_time': self.busy_time,
            'dnd_time': self.dnd_time,
            'average_talk_time': self.average_talk_time,
            'average_wrap_up_time': self.average_wrap_up_time,
            'occupancy_rate': self.occupancy_rate,
            'utilization_rate': self.utilization_rate
        }

class CallStats(Base):
    """Call statistics model for detailed call data."""
    
    __tablename__ = 'call_distributor_call_stats'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    call_id = Column(String(64), nullable=False, unique=True)
    queue_id = Column(Integer, ForeignKey('call_distributor_queues.id'))
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'))
    
    # Call details
    caller_id = Column(String(64))
    direction = Column(String(16))  # 'inbound', 'outbound'
    timestamp = Column(DateTime, nullable=False)
    
    # Queue metrics
    queue_wait_time = Column(Integer)  # seconds
    position_on_entry = Column(Integer)
    attempts = Column(Integer, default=1)
    
    # Outcome
    disposition = Column(String(32))  # 'answered', 'abandoned', 'transferred', etc.
    disconnect_reason = Column(String(32))
    talk_time = Column(Integer)  # seconds
    wrap_up_time = Column(Integer)  # seconds
    
    # Quality metrics
    satisfaction_score = Column(Integer)
    recording_url = Column(String(256))
    
    # Additional data
    tags = Column(JSON)
    custom_data = Column(JSON)
    
    # Relationships
    queue = relationship('Queue')
    agent = relationship('Agent')
    
    def __repr__(self):
        return f'<CallStats(call_id={self.call_id})>'
    
    @property
    def to_dict(self):
        """Convert call stats to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'call_id': self.call_id,
            'queue_id': self.queue_id,
            'agent_id': self.agent_id,
            'caller_id': self.caller_id,
            'direction': self.direction,
            'timestamp': self.timestamp.isoformat(),
            'queue_wait_time': self.queue_wait_time,
            'position_on_entry': self.position_on_entry,
            'attempts': self.attempts,
            'disposition': self.disposition,
            'disconnect_reason': self.disconnect_reason,
            'talk_time': self.talk_time,
            'wrap_up_time': self.wrap_up_time,
            'satisfaction_score': self.satisfaction_score,
            'recording_url': self.recording_url,
            'tags': self.tags,
            'custom_data': self.custom_data
        }
