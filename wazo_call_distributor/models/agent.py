"""Agent model for call distribution."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class Agent(Base):
    """Agent model for managing call center agents."""
    
    __tablename__ = 'call_distributor_agents'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    number = Column(String(32), nullable=False)
    
    # Login state
    logged_in = Column(Boolean, default=False)
    last_login = Column(DateTime)
    last_logout = Column(DateTime)
    
    # Pause state
    paused = Column(Boolean, default=False)
    pause_reason = Column(String(128))
    pause_start = Column(DateTime)
    
    # Agent type
    agent_type = Column(Enum('static', 'dynamic', name='agent_type'), default='static')
    
    # Relationships
    queue_members = relationship('QueueMember', back_populates='agent')
    skills = relationship('AgentSkill', back_populates='agent')
    desktop_settings = relationship('AgentDesktopSettings', back_populates='agent', uselist=False)
    roles = relationship('Role', secondary='call_distributor_agent_roles', back_populates='agents')
    
    def __repr__(self):
        return f'<Agent(name={self.name}, number={self.number})>'
    
    @property
    def to_dict(self):
        """Convert agent to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'number': self.number,
            'logged_in': self.logged_in,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_logout': self.last_logout.isoformat() if self.last_logout else None,
            'paused': self.paused,
            'pause_reason': self.pause_reason,
            'pause_start': self.pause_start.isoformat() if self.pause_start else None,
            'agent_type': self.agent_type
        }
    
    def login(self):
        """Log in the agent."""
        self.logged_in = True
        self.last_login = datetime.utcnow()
    
    def logout(self):
        """Log out the agent."""
        self.logged_in = False
        self.last_logout = datetime.utcnow()
        if self.paused:
            self.unpause()
    
    def pause(self, reason: str = None):
        """Pause the agent."""
        self.paused = True
        self.pause_reason = reason
        self.pause_start = datetime.utcnow()
    
    def unpause(self):
        """Unpause the agent."""
        self.paused = False
        self.pause_reason = None
        self.pause_start = None
