"""Least recent strategy implementation."""

from typing import Optional
from .base import BaseStrategy
from ..models import Agent

class LeastRecentStrategy(BaseStrategy):
    """Ring agent who was least recently called."""
    
    def get_next_agent(self, call_id: str) -> Optional[Agent]:
        """Get the agent who hasn't taken a call for the longest time."""
        members = self.get_available_members()
        
        if not members:
            return None
        
        # Sort by penalty level first
        members.sort(key=lambda x: x.penalty)
        lowest_penalty = members[0].penalty
        
        # Filter members with lowest penalty
        members = [m for m in members if m.penalty == lowest_penalty]
        
        # Get last call time for each member
        member_stats = [(m, self.get_member_stats(m.id)['last_call_time']) for m in members]
        
        # Sort by last call time (None = never called, should be first)
        member_stats.sort(key=lambda x: (x[1] is not None, x[1] or 0))
        
        selected_member = member_stats[0][0]
        self.log_distribution(call_id, selected_member.agent.id)
        
        return selected_member.agent
