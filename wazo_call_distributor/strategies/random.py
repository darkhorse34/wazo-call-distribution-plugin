"""Random strategy implementation."""

import random
from typing import Optional
from .base import BaseStrategy
from ..models import Agent

class RandomStrategy(BaseStrategy):
    """Ring a random available agent."""
    
    def get_next_agent(self, call_id: str) -> Optional[Agent]:
        """Get a random available agent."""
        members = self.get_available_members()
        
        if not members:
            return None
        
        # Sort by penalty level first
        members.sort(key=lambda x: x.penalty)
        lowest_penalty = members[0].penalty
        
        # Filter members with lowest penalty
        members = [m for m in members if m.penalty == lowest_penalty]
        
        # Select random member
        selected_member = random.choice(members)
        self.log_distribution(call_id, selected_member.agent.id)
        
        return selected_member.agent
