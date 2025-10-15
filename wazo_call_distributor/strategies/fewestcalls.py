"""Fewest calls strategy implementation."""

from typing import Optional
from .base import BaseStrategy
from ..models import Agent

class FewestCallsStrategy(BaseStrategy):
    """Ring agent who has taken the fewest calls."""
    
    def get_next_agent(self, call_id: str) -> Optional[Agent]:
        """Get the agent with the lowest number of calls taken."""
        members = self.get_available_members()
        
        if not members:
            return None
        
        # Sort by penalty level first
        members.sort(key=lambda x: x.penalty)
        lowest_penalty = members[0].penalty
        
        # Filter members with lowest penalty
        members = [m for m in members if m.penalty == lowest_penalty]
        
        # Get calls taken for each member
        member_stats = [(m, self.get_member_stats(m.id)['calls_taken']) for m in members]
        
        # Sort by number of calls taken
        member_stats.sort(key=lambda x: x[1])
        
        selected_member = member_stats[0][0]
        self.log_distribution(call_id, selected_member.agent.id)
        
        return selected_member.agent
