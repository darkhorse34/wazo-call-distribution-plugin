"""Linear strategy implementation."""

from typing import Optional
from .base import BaseStrategy
from ..models import Agent

class LinearStrategy(BaseStrategy):
    """Ring agents in the order they were added to the queue."""
    
    def get_next_agent(self, call_id: str) -> Optional[Agent]:
        """Get the next agent in linear order."""
        members = self.get_available_members()
        
        if not members:
            return None
        
        # Sort by penalty level first
        members.sort(key=lambda x: x.penalty)
        lowest_penalty = members[0].penalty
        
        # Filter members with lowest penalty
        members = [m for m in members if m.penalty == lowest_penalty]
        
        # Sort by join time (members are ordered by id which corresponds to join order)
        members.sort(key=lambda x: x.id)
        
        selected_member = members[0]
        self.log_distribution(call_id, selected_member.agent.id)
        
        return selected_member.agent
