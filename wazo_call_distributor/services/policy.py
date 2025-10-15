"""Policy service for call distribution."""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from ..models import Queue, Agent, AgentSkill, CallerPriority, QueueMember
from ..exceptions import QueueNotFound

class PolicyService:
    """Service for handling call distribution policies."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_caller_priority(self, tenant_uuid: str, number: str) -> Optional[CallerPriority]:
        """Get caller priority settings."""
        return self.session.query(CallerPriority).filter(
            CallerPriority.tenant_uuid == tenant_uuid,
            CallerPriority.number == number
        ).first()
    
    def set_caller_priority(self, tenant_uuid: str, priority_data: Dict) -> CallerPriority:
        """Set caller priority settings."""
        priority = CallerPriority(tenant_uuid=tenant_uuid, **priority_data)
        self.session.add(priority)
        self.session.commit()
        return priority
    
    def get_agents_by_skills(self, queue_id: int, tenant_uuid: str,
                           required_skills: List[Dict[str, int]]) -> List[Agent]:
        """Get agents matching required skills."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue:
            raise QueueNotFound(queue_id)
        
        # Get all available agents in the queue
        available_members = self.session.query(QueueMember).filter(
            QueueMember.queue_id == queue.id,
            QueueMember.is_available == True,
            QueueMember.paused == False
        ).all()
        
        if not available_members:
            return []
        
        # Filter agents by required skills
        qualified_agents = []
        for member in available_members:
            agent = member.agent
            agent_skills = {
                skill.skill_id: skill.level
                for skill in agent.skills
            }
            
            # Check if agent has all required skills at sufficient levels
            meets_requirements = True
            for skill_req in required_skills:
                skill_id = skill_req['skill_id']
                min_level = skill_req.get('min_level', 0)
                
                if skill_id not in agent_skills or agent_skills[skill_id] < min_level:
                    meets_requirements = False
                    break
            
            if meets_requirements:
                qualified_agents.append(agent)
        
        return qualified_agents
    
    def get_sticky_agent(self, queue_id: int, tenant_uuid: str, caller_id: str) -> Optional[Agent]:
        """Get the sticky agent for a caller if one exists."""
        # TODO: Implement sticky agent logic using Redis to store caller-agent mappings
        return None
    
    def set_sticky_agent(self, queue_id: int, tenant_uuid: str,
                        caller_id: str, agent_id: int) -> None:
        """Set the sticky agent for a caller."""
        # TODO: Implement sticky agent assignment in Redis
        pass
    
    def get_overflow_target(self, queue_id: int, tenant_uuid: str,
                          wait_time: int) -> Optional[Tuple[str, str]]:
        """Get overflow target based on wait time."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue or not queue.overflow_timeout:
            return None
        
        if wait_time >= queue.overflow_timeout:
            if queue.overflow_queue_id:
                return ('queue', str(queue.overflow_queue_id))
            # TODO: Implement other overflow targets (voicemail, external DNIS)
        
        return None
    
    def handle_blacklisted_caller(self, tenant_uuid: str, number: str) -> Optional[str]:
        """Handle blacklisted caller and return rejection message if applicable."""
        priority = self.get_caller_priority(tenant_uuid, number)
        
        if priority and priority.priority_type == 'blacklist':
            return f"Caller {number} is blacklisted (level {priority.priority_level})"
        
        return None
    
    def adjust_queue_position(self, queue_id: int, tenant_uuid: str,
                            caller_id: str, current_position: int) -> int:
        """Adjust caller's position based on VIP status."""
        priority = self.get_caller_priority(tenant_uuid, caller_id)
        
        if priority and priority.priority_type == 'vip':
            # VIP callers move up in the queue based on their priority level
            new_position = max(0, current_position - priority.priority_level)
            return new_position
        
        return current_position
