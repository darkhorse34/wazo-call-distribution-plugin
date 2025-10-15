"""Schedule models for call distribution."""

from sqlalchemy import Column, Integer, String, Boolean, Time, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import time, date
from . import Base

# Association table for queue schedules
queue_schedules = Table(
    'call_distributor_queue_schedules',
    Base.metadata,
    Column('queue_id', Integer, ForeignKey('call_distributor_queues.id'), primary_key=True),
    Column('schedule_id', Integer, ForeignKey('call_distributor_schedules.id'), primary_key=True)
)

class Schedule(Base):
    """Schedule model for managing business hours and holidays."""
    
    __tablename__ = 'call_distributor_schedules'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Fallback destination when closed
    fallback_type = Column(String(32))  # 'voicemail', 'ivr', 'queue', etc.
    fallback_destination = Column(String(128))  # destination ID or extension
    
    # Relationships
    time_ranges = relationship('TimeRange', back_populates='schedule', cascade='all, delete-orphan')
    holidays = relationship('Holiday', back_populates='schedule', cascade='all, delete-orphan')
    queues = relationship('Queue', secondary=queue_schedules, back_populates='schedules')
    
    def __repr__(self):
        return f'<Schedule(name={self.name})>'
    
    @property
    def to_dict(self):
        """Convert schedule to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'description': self.description,
            'fallback_type': self.fallback_type,
            'fallback_destination': self.fallback_destination,
            'time_ranges': [tr.to_dict for tr in self.time_ranges],
            'holidays': [h.to_dict for h in self.holidays]
        }

class TimeRange(Base):
    """Time range model for defining business hours."""
    
    __tablename__ = 'call_distributor_time_ranges'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('call_distributor_schedules.id'), nullable=False)
    
    # Days of week (0 = Monday, 6 = Sunday)
    day_start = Column(Integer, nullable=False)
    day_end = Column(Integer, nullable=False)
    
    # Time range
    time_start = Column(Time, nullable=False, default=time(9, 0))  # 9:00 AM
    time_end = Column(Time, nullable=False, default=time(17, 0))  # 5:00 PM
    
    # Relationship
    schedule = relationship('Schedule', back_populates='time_ranges')
    
    def __repr__(self):
        return f'<TimeRange(days={self.day_start}-{self.day_end}, times={self.time_start}-{self.time_end})>'
    
    @property
    def to_dict(self):
        """Convert time range to dictionary representation."""
        return {
            'id': self.id,
            'day_start': self.day_start,
            'day_end': self.day_end,
            'time_start': self.time_start.strftime('%H:%M'),
            'time_end': self.time_end.strftime('%H:%M')
        }

class Holiday(Base):
    """Holiday model for defining non-working days."""
    
    __tablename__ = 'call_distributor_holidays'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('call_distributor_schedules.id'), nullable=False)
    
    name = Column(String(128), nullable=False)
    date = Column(Date, nullable=False)
    recurring = Column(Boolean, default=False)  # True for annual holidays
    
    # Optional time range (if None, whole day is considered holiday)
    time_start = Column(Time)
    time_end = Column(Time)
    
    # Relationship
    schedule = relationship('Schedule', back_populates='holidays')
    
    def __repr__(self):
        return f'<Holiday(name={self.name}, date={self.date})>'
    
    @property
    def to_dict(self):
        """Convert holiday to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date.isoformat(),
            'recurring': self.recurring,
            'time_start': self.time_start.strftime('%H:%M') if self.time_start else None,
            'time_end': self.time_end.strftime('%H:%M') if self.time_end else None
        }
