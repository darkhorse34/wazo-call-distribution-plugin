"""Queue model for call distribution."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from . import Base

class Queue(Base):
    """Queue model for managing call queues."""
    
    __tablename__ = 'call_distributor_queues'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    strategy = Column(Enum('ringall', 'leastrecent', 'fewestcalls', 'random', 'rrmemory', 'linear',
                         name='queue_strategy'), nullable=False, default='ringall')
    
    # Queue settings
    timeout = Column(Integer, default=30)  # Ring timeout in seconds
    max_wait = Column(Integer, default=3600)  # Max wait time in queue
    service_level = Column(Integer, default=20)  # Service level threshold in seconds
    weight = Column(Integer, default=0)  # Queue priority weight
    
    # Capacity settings
    max_callers = Column(Integer, default=0)  # 0 = unlimited
    max_members = Column(Integer, default=0)  # 0 = unlimited
    
    # Behavior flags
    announce_position = Column(Boolean, default=True)
    announce_holdtime = Column(Boolean, default=True)
    periodic_announce = Column(Boolean, default=True)
    
    # Media settings
    moh_class = Column(String(128), default='default')
    announce_frequency = Column(Integer, default=60)
    announce_position = Column(Boolean, default=True)
    announce_holdtime = Column(Boolean, default=True)
    announce_periodic = Column(Boolean, default=True)
    
    # Relationships for media
    announcements = relationship('Announcement', back_populates='queue', cascade='all, delete-orphan')
    
    # Overflow settings
    overflow_queue_id = Column(Integer, ForeignKey('call_distributor_queues.id'), nullable=True)
    overflow_timeout = Column(Integer, default=0)  # 0 = disabled
    
    # Relationships
    members = relationship('QueueMember', back_populates='queue')
    skills = relationship('Skill', secondary='queue_skills')
    schedules = relationship('Schedule', secondary='queue_schedules')
    
    def __repr__(self):
        return f'<Queue(name={self.name}, strategy={self.strategy})>'
    
    @property
    def to_dict(self):
        """Convert queue to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'strategy': self.strategy,
            'timeout': self.timeout,
            'max_wait': self.max_wait,
            'service_level': self.service_level,
            'weight': self.weight,
            'max_callers': self.max_callers,
            'max_members': self.max_members,
            'announce_position': self.announce_position,
            'announce_holdtime': self.announce_holdtime,
            'periodic_announce': self.periodic_announce,
            'moh_class': self.moh_class,
            'announce_frequency': self.announce_frequency,
            'overflow_queue_id': self.overflow_queue_id,
            'overflow_timeout': self.overflow_timeout
        }
