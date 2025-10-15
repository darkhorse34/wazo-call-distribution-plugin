"""Queue member model for call distribution."""

from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from . import Base

class QueueMember(Base):
    """Queue member model for managing agent-queue relationships."""
    
    __tablename__ = 'call_distributor_queue_members'
    
    id = Column(Integer, primary_key=True)
    queue_id = Column(Integer, ForeignKey('call_distributor_queues.id'), nullable=False)
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'), nullable=False)
    
    # Member settings
    penalty = Column(Integer, default=0)  # Lower numbers = higher priority
    is_available = Column(Boolean, default=True)
    paused = Column(Boolean, default=False)
    
    # Relationships
    queue = relationship('Queue', back_populates='members')
    agent = relationship('Agent', back_populates='queue_members')
    
    def __repr__(self):
        return f'<QueueMember(queue_id={self.queue_id}, agent_id={self.agent_id})>'
    
    @property
    def to_dict(self):
        """Convert queue member to dictionary representation."""
        return {
            'id': self.id,
            'queue_id': self.queue_id,
            'agent_id': self.agent_id,
            'penalty': self.penalty,
            'is_available': self.is_available,
            'paused': self.paused
        }
