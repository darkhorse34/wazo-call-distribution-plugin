"""Distribution service for handling queue strategies."""

from typing import Optional, List, Union
from ..models import Queue, Agent
from ..strategies import STRATEGY_MAPPING
from ..exceptions import QueueNotFound, InvalidQueueStrategy

class DistributionService:
    """Service for handling queue distribution strategies."""
    
    def __init__(self, session):
        self.session = session
    
    def get_next_agents(self, queue_id: int, tenant_uuid: str, call_id: str) -> Union[Optional[Agent], List[Agent]]:
        """Get next agent(s) based on queue strategy."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue:
            raise QueueNotFound(queue_id)
        
        strategy_class = STRATEGY_MAPPING.get(queue.strategy)
        if not strategy_class:
            raise InvalidQueueStrategy(f"Strategy {queue.strategy} not implemented")
        
        strategy = strategy_class(queue, self.session)
        return strategy.get_next_agent(call_id)
    
    def update_agent_stats(self, queue_id: int, agent_id: int, call_duration: int) -> None:
        """Update agent statistics after call completion."""
        queue = self.session.query(Queue).get(queue_id)
        if not queue:
            raise QueueNotFound(queue_id)
        
        strategy_class = STRATEGY_MAPPING.get(queue.strategy)
        if not strategy_class:
            raise InvalidQueueStrategy(f"Strategy {queue.strategy} not implemented")
        
        strategy = strategy_class(queue, self.session)
        strategy.update_member_stats(agent_id, call_duration)
    
    def get_agent_stats(self, queue_id: int, agent_id: int) -> dict:
        """Get agent statistics for a queue."""
        queue = self.session.query(Queue).get(queue_id)
        if not queue:
            raise QueueNotFound(queue_id)
        
        strategy_class = STRATEGY_MAPPING.get(queue.strategy)
        if not strategy_class:
            raise InvalidQueueStrategy(f"Strategy {queue.strategy} not implemented")
        
        strategy = strategy_class(queue, self.session)
        return strategy.get_member_stats(agent_id)
