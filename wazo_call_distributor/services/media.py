"""Media service for managing announcements and music on hold."""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..models import Announcement, MusicOnHold, Queue
from ..exceptions import QueueNotFound

class MediaService:
    """Service for managing media features."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_announcement(self, announcement_id: int, tenant_uuid: str) -> Announcement:
        """Get an announcement by ID."""
        announcement = self.session.query(Announcement).filter(
            Announcement.id == announcement_id,
            Announcement.tenant_uuid == tenant_uuid
        ).first()
        
        if not announcement:
            raise ValueError(f"Announcement {announcement_id} not found")
        
        return announcement
    
    def list_announcements(self, queue_id: int, tenant_uuid: str) -> List[Announcement]:
        """List all announcements for a queue."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue:
            raise QueueNotFound(queue_id)
        
        return queue.announcements
    
    def create_announcement(self, queue_id: int, tenant_uuid: str,
                          announcement_data: Dict) -> Announcement:
        """Create a new announcement."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue:
            raise QueueNotFound(queue_id)
        
        announcement = Announcement(
            tenant_uuid=tenant_uuid,
            queue_id=queue_id,
            **announcement_data
        )
        
        self.session.add(announcement)
        self.session.commit()
        
        return announcement
    
    def update_announcement(self, announcement_id: int, tenant_uuid: str,
                          announcement_data: Dict) -> Announcement:
        """Update an existing announcement."""
        announcement = self.get_announcement(announcement_id, tenant_uuid)
        
        for key, value in announcement_data.items():
            setattr(announcement, key, value)
        
        self.session.commit()
        return announcement
    
    def delete_announcement(self, announcement_id: int, tenant_uuid: str) -> None:
        """Delete an announcement."""
        announcement = self.get_announcement(announcement_id, tenant_uuid)
        self.session.delete(announcement)
        self.session.commit()
    
    def get_moh(self, moh_id: int, tenant_uuid: str) -> MusicOnHold:
        """Get a music on hold class by ID."""
        moh = self.session.query(MusicOnHold).filter(
            MusicOnHold.id == moh_id,
            MusicOnHold.tenant_uuid == tenant_uuid
        ).first()
        
        if not moh:
            raise ValueError(f"Music on hold class {moh_id} not found")
        
        return moh
    
    def list_moh(self, tenant_uuid: str) -> List[MusicOnHold]:
        """List all music on hold classes for a tenant."""
        return self.session.query(MusicOnHold).filter(
            MusicOnHold.tenant_uuid == tenant_uuid
        ).all()
    
    def create_moh(self, tenant_uuid: str, moh_data: Dict) -> MusicOnHold:
        """Create a new music on hold class."""
        moh = MusicOnHold(tenant_uuid=tenant_uuid, **moh_data)
        self.session.add(moh)
        self.session.commit()
        return moh
    
    def update_moh(self, moh_id: int, tenant_uuid: str, moh_data: Dict) -> MusicOnHold:
        """Update an existing music on hold class."""
        moh = self.get_moh(moh_id, tenant_uuid)
        
        for key, value in moh_data.items():
            setattr(moh, key, value)
        
        self.session.commit()
        return moh
    
    def delete_moh(self, moh_id: int, tenant_uuid: str) -> None:
        """Delete a music on hold class."""
        moh = self.get_moh(moh_id, tenant_uuid)
        self.session.delete(moh)
        self.session.commit()
    
    def get_queue_position(self, queue_id: int, call_id: str) -> Optional[int]:
        """Get position in queue for a call."""
        # TODO: Implement queue position tracking using Redis
        return None
    
    def estimate_wait_time(self, queue_id: int, position: int) -> Optional[int]:
        """Estimate wait time for a position in queue."""
        # TODO: Implement wait time estimation using historical data
        return None
    
    def should_announce_position(self, queue_id: int, tenant_uuid: str,
                               position: int, last_announce: int) -> bool:
        """Check if position should be announced."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue or not queue.announce_position:
            return False
        
        announcement = next(
            (a for a in queue.announcements
             if a.type == 'position' and a.enabled),
            None
        )
        
        if not announcement:
            return False
        
        # Announce if position has changed by the frequency amount
        return abs(position - last_announce) >= announcement.position_frequency
    
    def should_announce_wait_time(self, queue_id: int, tenant_uuid: str,
                                wait_time: int, last_announce: int) -> bool:
        """Check if wait time should be announced."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue or not queue.announce_holdtime:
            return False
        
        announcement = next(
            (a for a in queue.announcements
             if a.type == 'wait_time' and a.enabled),
            None
        )
        
        if not announcement:
            return False
        
        # Announce if wait time has changed by the frequency amount (in minutes)
        wait_time_min = wait_time // 60
        last_announce_min = last_announce // 60
        return abs(wait_time_min - last_announce_min) >= announcement.wait_time_frequency
