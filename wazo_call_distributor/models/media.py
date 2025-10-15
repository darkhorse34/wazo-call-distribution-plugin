"""Media models for call distribution."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from . import Base

class Announcement(Base):
    """Announcement model for queue messages."""
    
    __tablename__ = 'call_distributor_announcements'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Announcement type
    type = Column(Enum('entrance', 'periodic', 'position', 'wait_time',
                      name='announcement_type'), nullable=False)
    
    # Media source
    media_type = Column(Enum('sound', 'tts', name='media_type'), nullable=False)
    media_source = Column(String(256), nullable=False)  # Sound file path or TTS text
    
    # Language settings for TTS
    language = Column(String(10))  # e.g., 'en-US', 'fr-FR'
    voice = Column(String(32))  # TTS voice identifier
    
    # Queue settings
    queue_id = Column(Integer, ForeignKey('call_distributor_queues.id'), nullable=False)
    enabled = Column(Boolean, default=True)
    
    # Periodic announcement settings
    interval = Column(Integer)  # Interval in seconds for periodic announcements
    
    # Position announcement settings
    position_frequency = Column(Integer)  # How often to announce position (in positions)
    
    # Wait time announcement settings
    wait_time_frequency = Column(Integer)  # How often to announce wait time (in minutes)
    
    # Relationship
    queue = relationship('Queue', back_populates='announcements')
    
    def __repr__(self):
        return f'<Announcement(name={self.name}, type={self.type})>'
    
    @property
    def to_dict(self):
        """Convert announcement to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'media_type': self.media_type,
            'media_source': self.media_source,
            'language': self.language,
            'voice': self.voice,
            'queue_id': self.queue_id,
            'enabled': self.enabled,
            'interval': self.interval,
            'position_frequency': self.position_frequency,
            'wait_time_frequency': self.wait_time_frequency
        }

class MusicOnHold(Base):
    """Music on hold class model."""
    
    __tablename__ = 'call_distributor_moh'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Playback mode
    mode = Column(Enum('files', 'random', 'linear', name='moh_mode'), default='random')
    
    # Directory containing music files
    directory = Column(String(256), nullable=False)
    
    def __repr__(self):
        return f'<MusicOnHold(name={self.name}, mode={self.mode})>'
    
    @property
    def to_dict(self):
        """Convert MOH class to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'description': self.description,
            'mode': self.mode,
            'directory': self.directory
        }
