"""Desktop models for agent interface."""

from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from . import Base

class AgentDesktopSettings(Base):
    """Agent desktop settings model."""
    
    __tablename__ = 'call_distributor_agent_desktop_settings'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'), nullable=False)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    
    # Layout settings
    layout_config = Column(JSON, default={})
    theme = Column(String(32), default='light')
    
    # Notification settings
    notifications_enabled = Column(Boolean, default=True)
    sound_enabled = Column(Boolean, default=True)
    desktop_notifications = Column(Boolean, default=True)
    
    # Widget visibility
    show_queue_stats = Column(Boolean, default=True)
    show_personal_kpis = Column(Boolean, default=True)
    show_wrap_up_timer = Column(Boolean, default=True)
    show_call_history = Column(Boolean, default=True)
    
    # Wrap-up settings
    default_wrap_up_time = Column(Integer, default=30)  # seconds
    auto_wrap_up = Column(Boolean, default=False)
    
    # Custom settings
    custom_settings = Column(JSON, default={})
    
    # Relationship
    agent = relationship('Agent', back_populates='desktop_settings')
    
    def __repr__(self):
        return f'<AgentDesktopSettings(agent_id={self.agent_id})>'
    
    @property
    def to_dict(self):
        """Convert settings to dictionary representation."""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'tenant_uuid': self.tenant_uuid,
            'layout_config': self.layout_config,
            'theme': self.theme,
            'notifications_enabled': self.notifications_enabled,
            'sound_enabled': self.sound_enabled,
            'desktop_notifications': self.desktop_notifications,
            'show_queue_stats': self.show_queue_stats,
            'show_personal_kpis': self.show_personal_kpis,
            'show_wrap_up_timer': self.show_wrap_up_timer,
            'show_call_history': self.show_call_history,
            'default_wrap_up_time': self.default_wrap_up_time,
            'auto_wrap_up': self.auto_wrap_up,
            'custom_settings': self.custom_settings
        }

class WrapUpCode(Base):
    """Wrap-up code model for call disposition."""
    
    __tablename__ = 'call_distributor_wrap_up_codes'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    code = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Optional category for grouping
    category = Column(String(64))
    
    # Optional additional fields
    requires_comment = Column(Boolean, default=False)
    requires_callback = Column(Boolean, default=False)
    
    def __repr__(self):
        return f'<WrapUpCode(code={self.code}, name={self.name})>'
    
    @property
    def to_dict(self):
        """Convert wrap-up code to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'requires_comment': self.requires_comment,
            'requires_callback': self.requires_callback
        }

class CallNote(Base):
    """Call note model for agent comments."""
    
    __tablename__ = 'call_distributor_call_notes'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'), nullable=False)
    call_id = Column(String(64), nullable=False)
    
    # Note content
    note = Column(String(1024), nullable=False)
    timestamp = Column(String(32), nullable=False)
    
    # Optional wrap-up code
    wrap_up_code_id = Column(Integer, ForeignKey('call_distributor_wrap_up_codes.id'))
    
    # Optional callback info
    callback_requested = Column(Boolean, default=False)
    callback_number = Column(String(32))
    callback_time = Column(String(32))
    
    # Relationships
    agent = relationship('Agent')
    wrap_up_code = relationship('WrapUpCode')
    
    def __repr__(self):
        return f'<CallNote(agent_id={self.agent_id}, call_id={self.call_id})>'
    
    @property
    def to_dict(self):
        """Convert call note to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'agent_id': self.agent_id,
            'call_id': self.call_id,
            'note': self.note,
            'timestamp': self.timestamp,
            'wrap_up_code_id': self.wrap_up_code_id,
            'callback_requested': self.callback_requested,
            'callback_number': self.callback_number,
            'callback_time': self.callback_time,
            'wrap_up_code': self.wrap_up_code.to_dict if self.wrap_up_code else None
        }
