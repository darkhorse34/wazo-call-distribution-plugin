"""Skill models for call distribution."""

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from . import Base

# Association table for queue skills
queue_skills = Table(
    'call_distributor_queue_skills',
    Base.metadata,
    Column('queue_id', Integer, ForeignKey('call_distributor_queues.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('call_distributor_skills.id'), primary_key=True)
)

class Skill(Base):
    """Skill model for defining agent capabilities."""
    
    __tablename__ = 'call_distributor_skills'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Relationships
    agents = relationship('AgentSkill', back_populates='skill')
    queues = relationship('Queue', secondary=queue_skills, back_populates='skills')
    
    def __repr__(self):
        return f'<Skill(name={self.name})>'
    
    @property
    def to_dict(self):
        """Convert skill to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'description': self.description
        }

class AgentSkill(Base):
    """Association model for agent skills with proficiency levels."""
    
    __tablename__ = 'call_distributor_agent_skills'
    
    agent_id = Column(Integer, ForeignKey('call_distributor_agents.id'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('call_distributor_skills.id'), primary_key=True)
    level = Column(Integer, nullable=False, default=0)  # 0-100 proficiency level
    
    # Relationships
    agent = relationship('Agent', back_populates='skills')
    skill = relationship('Skill', back_populates='agents')
    
    def __repr__(self):
        return f'<AgentSkill(agent_id={self.agent_id}, skill_id={self.skill_id}, level={self.level})>'
    
    @property
    def to_dict(self):
        """Convert agent skill to dictionary representation."""
        return {
            'agent_id': self.agent_id,
            'skill_id': self.skill_id,
            'level': self.level
        }
