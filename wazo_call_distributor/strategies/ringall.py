"""Ring all strategy implementation."""

from typing import Optional, List
from .base import BaseStrategy
from ..models import Agent, QueueMember

class RingAllStrategy(BaseStrategy):
    """Ring all available agents simultaneously."""
    
    def get_next_agent(self, call_id: str) -> Optional[List[Agent]]:
        """Get all available agents to ring simultaneously."""
        members = self.get_available_members()
        
        if not members:
            return None
        
        # Sort by penalty level (lower penalty = higher priority)
        members.sort(key=lambda x: x.penalty)
        
        # Group members by penalty level
        penalty_groups = {}
        for member in members:
            if member.penalty not in penalty_groups:
                penalty_groups[member.penalty] = []
            penalty_groups[member.penalty].append(member.agent)
        
        # Get the group with lowest penalty
        lowest_penalty = min(penalty_groups.keys())
        agents = penalty_groups[lowest_penalty]
        
        # Log distribution decision
        for agent in agents:
            self.log_distribution(call_id, agent.id)
        
        return agents
