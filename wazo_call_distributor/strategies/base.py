"""Base strategy for queue distribution."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import Queue, Agent, QueueMember

class BaseStrategy(ABC):
    """Base class for queue distribution strategies."""
    
    def __init__(self, queue: Queue, session):
        """Initialize strategy."""
        self.queue = queue
        self.session = session
    
    @abstractmethod
    def get_next_agent(self, call_id: str) -> Optional[Agent]:
        """Get the next agent to ring based on the strategy."""
        pass
    
    def get_available_members(self) -> List[QueueMember]:
        """Get list of available queue members."""
        return self.session.query(QueueMember).filter(
            QueueMember.queue_id == self.queue.id,
            QueueMember.is_available == True,
            QueueMember.paused == False
        ).all()
    
    def get_member_stats(self, member_id: int) -> dict:
        """Get member statistics."""
        # TODO: Implement stats collection from Redis
        return {
            'last_call_time': None,
            'calls_taken': 0,
            'total_talk_time': 0,
            'average_talk_time': 0
        }
    
    def update_member_stats(self, member_id: int, call_duration: int) -> None:
        """Update member statistics after a call."""
        # TODO: Implement stats update in Redis
        pass
    
    def log_distribution(self, call_id: str, member_id: int) -> None:
        """Log distribution decision for analytics."""
        # TODO: Implement distribution logging
        pass
