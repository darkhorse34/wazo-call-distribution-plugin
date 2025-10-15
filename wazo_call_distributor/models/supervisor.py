"""Supervisor models for call distribution."""

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from . import Base

class SupervisorSettings(Base):
    """Supervisor settings model."""
    
    __tablename__ = 'call_distributor_supervisor_settings'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'), nullable=False)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    
    # Wallboard layout
    wallboard_layout = Column(JSON, default={})
    
    # Alert settings
    alert_settings = Column(JSON, default={
        'sla_threshold': 80.0,  # percentage
        'abandon_threshold': 5.0,  # percentage
        'wait_time_threshold': 300,  # seconds
        'occupancy_threshold': 85.0,  # percentage
        'enable_email_alerts': True,
        'enable_desktop_alerts': True
    })
    
    # Monitoring preferences
    default_view = Column(String(32), default='wallboard')  # wallboard, agents, queues
    refresh_interval = Column(Integer, default=5)  # seconds
    auto_refresh = Column(Boolean, default=True)
    
    # Custom settings
    custom_settings = Column(JSON, default={})
    
    # Relationship
    agent = relationship('Agent')
    
    def __repr__(self):
        return f'<SupervisorSettings(agent_id={self.agent_id})>'
    
    @property
    def to_dict(self):
        """Convert settings to dictionary representation."""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'tenant_uuid': self.tenant_uuid,
            'wallboard_layout': self.wallboard_layout,
            'alert_settings': self.alert_settings,
            'default_view': self.default_view,
            'refresh_interval': self.refresh_interval,
            'auto_refresh': self.auto_refresh,
            'custom_settings': self.custom_settings
        }

class Alert(Base):
    """Alert model for supervisor notifications."""
    
    __tablename__ = 'call_distributor_alerts'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    
    # Alert type and source
    alert_type = Column(Enum('sla', 'abandon', 'wait_time', 'occupancy',
                           name='alert_type'), nullable=False)
    source_type = Column(Enum('queue', 'agent', name='source_type'), nullable=False)
    source_id = Column(Integer, nullable=False)
    
    # Alert details
    threshold = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    message = Column(String(256), nullable=False)
    timestamp = Column(String(32), nullable=False)
    
    # Alert status
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey('call_distributor_agents.id'))
    acknowledged_at = Column(String(32))
    
    # Relationships
    acknowledger = relationship('Agent')
    
    def __repr__(self):
        return f'<Alert(type={self.alert_type}, source={self.source_type}:{self.source_id})>'
    
    @property
    def to_dict(self):
        """Convert alert to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'alert_type': self.alert_type,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'threshold': self.threshold,
            'current_value': self.current_value,
            'message': self.message,
            'timestamp': self.timestamp,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at
        }

class MonitoringProfile(Base):
    """Monitoring profile model for customizable views."""
    
    __tablename__ = 'call_distributor_monitoring_profiles'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'), nullable=False)
    
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Profile settings
    queues = Column(JSON, default=[])  # List of queue IDs to monitor
    agents = Column(JSON, default=[])  # List of agent IDs to monitor
    metrics = Column(JSON, default=[])  # List of metrics to display
    layout = Column(JSON, default={})  # Layout configuration
    filters = Column(JSON, default={})  # Filter settings
    
    # Relationship
    agent = relationship('Agent')
    
    def __repr__(self):
        return f'<MonitoringProfile(name={self.name})>'
    
    @property
    def to_dict(self):
        """Convert profile to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'queues': self.queues,
            'agents': self.agents,
            'metrics': self.metrics,
            'layout': self.layout,
            'filters': self.filters
        }
