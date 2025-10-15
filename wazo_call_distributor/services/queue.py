"""Queue service for managing call queues."""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from ..models import Queue
from ..exceptions import QueueNotFound, InvalidQueueStrategy

class QueueService:
    """Service for managing call queues."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, queue_id: int, tenant_uuid: str) -> Queue:
        """Get a queue by ID and tenant."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue:
            raise QueueNotFound(queue_id)
        
        return queue
    
    def list(self, tenant_uuid: str) -> List[Queue]:
        """List all queues for a tenant."""
        return self.session.query(Queue).filter(
            Queue.tenant_uuid == tenant_uuid
        ).all()
    
    def create(self, tenant_uuid: str, queue_data: Dict) -> Queue:
        """Create a new queue."""
        self._validate_strategy(queue_data.get('strategy', 'ringall'))
        
        queue = Queue(tenant_uuid=tenant_uuid, **queue_data)
        self.session.add(queue)
        self.session.commit()
        
        return queue
    
    def update(self, queue_id: int, tenant_uuid: str, queue_data: Dict) -> Queue:
        """Update an existing queue."""
        queue = self.get(queue_id, tenant_uuid)
        
        if 'strategy' in queue_data:
            self._validate_strategy(queue_data['strategy'])
        
        for key, value in queue_data.items():
            setattr(queue, key, value)
        
        self.session.commit()
        return queue
    
    def delete(self, queue_id: int, tenant_uuid: str) -> None:
        """Delete a queue."""
        queue = self.get(queue_id, tenant_uuid)
        self.session.delete(queue)
        self.session.commit()
    
    def _validate_strategy(self, strategy: str) -> None:
        """Validate queue strategy."""
        valid_strategies = ['ringall', 'leastrecent', 'fewestcalls', 'random', 'rrmemory', 'linear']
        if strategy not in valid_strategies:
            raise InvalidQueueStrategy(f"Invalid strategy: {strategy}. Must be one of: {', '.join(valid_strategies)}")
    
    def get_queue_stats(self, queue_id: int, tenant_uuid: str) -> Dict:
        """Get real-time statistics for a queue."""
        queue = self.get(queue_id, tenant_uuid)
        # TODO: Implement real-time stats collection
        return {
            'queue_id': queue.id,
            'name': queue.name,
            'calls_waiting': 0,
            'longest_wait': 0,
            'agents_logged': 0,
            'agents_available': 0,
            'service_level': 0,
            'abandoned_calls': 0
        }
    
    def update_overflow_settings(self, queue_id: int, tenant_uuid: str,
                               overflow_queue_id: Optional[int] = None,
                               overflow_timeout: int = 0) -> Queue:
        """Update queue overflow settings."""
        queue = self.get(queue_id, tenant_uuid)
        
        if overflow_queue_id:
            overflow_queue = self.get(overflow_queue_id, tenant_uuid)
            queue.overflow_queue_id = overflow_queue.id
        else:
            queue.overflow_queue_id = None
        
        queue.overflow_timeout = overflow_timeout
        self.session.commit()
        return queue
