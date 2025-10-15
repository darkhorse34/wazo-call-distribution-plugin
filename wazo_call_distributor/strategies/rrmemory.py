"""Round Robin with Memory strategy implementation."""

from typing import Optional
import redis
from .base import BaseStrategy
from ..models import Agent

class RoundRobinMemoryStrategy(BaseStrategy):
    """Ring agents in round-robin order, remembering last position."""
    
    def __init__(self, queue, session):
        """Initialize strategy with Redis connection."""
        super().__init__(queue, session)
        self.redis = redis.from_url(session.app.config['call_distributor']['redis_url'])
    
    def get_next_agent(self, call_id: str) -> Optional[Agent]:
        """Get the next agent in round-robin order."""
        members = self.get_available_members()
        
        if not members:
            return None
        
        # Sort by penalty level first
        members.sort(key=lambda x: x.penalty)
        lowest_penalty = members[0].penalty
        
        # Filter members with lowest penalty
        members = [m for m in members if m.penalty == lowest_penalty]
        
        # Get last position from Redis
        redis_key = f"queue:{self.queue.id}:rr_position"
        last_position = int(self.redis.get(redis_key) or -1)
        
        # Find next position
        next_position = (last_position + 1) % len(members)
        self.redis.set(redis_key, next_position)
        
        selected_member = members[next_position]
        self.log_distribution(call_id, selected_member.agent.id)
        
        return selected_member.agent
