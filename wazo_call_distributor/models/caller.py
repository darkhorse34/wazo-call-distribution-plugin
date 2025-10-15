"""Caller models for call distribution."""

from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from . import Base

class CallerPriority(Base):
    """Caller priority model for VIP and blacklist handling."""
    
    __tablename__ = 'call_distributor_caller_priorities'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    number = Column(String(32), nullable=False, index=True)
    priority_type = Column(Enum('vip', 'blacklist', name='priority_type'), nullable=False)
    priority_level = Column(Integer, default=0)  # Higher = more priority for VIP, more restricted for blacklist
    description = Column(String(256))
    
    def __repr__(self):
        return f'<CallerPriority(number={self.number}, type={self.priority_type})>'
    
    @property
    def to_dict(self):
        """Convert caller priority to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'number': self.number,
            'priority_type': self.priority_type,
            'priority_level': self.priority_level,
            'description': self.description
        }
