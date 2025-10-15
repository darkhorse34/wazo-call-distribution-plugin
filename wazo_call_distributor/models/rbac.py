"""RBAC models for multi-tenant support."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from . import Base

# Association table for role permissions
role_permissions = Table(
    'call_distributor_role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('call_distributor_roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('call_distributor_permissions.id'), primary_key=True)
)

# Association table for agent roles
agent_roles = Table(
    'call_distributor_agent_roles',
    Base.metadata,
    Column('agent_id', Integer, ForeignKey('call_distributor_agents.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('call_distributor_roles.id'), primary_key=True)
)

class Role(Base):
    """Role model for RBAC."""
    
    __tablename__ = 'call_distributor_roles'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Role type
    is_system_role = Column(Boolean, default=False)  # True for built-in roles
    
    # Relationships
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')
    agents = relationship('Agent', secondary=agent_roles, back_populates='roles')
    
    def __repr__(self):
        return f'<Role(name={self.name})>'
    
    @property
    def to_dict(self):
        """Convert role to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'description': self.description,
            'is_system_role': self.is_system_role,
            'permissions': [p.to_dict for p in self.permissions]
        }

class Permission(Base):
    """Permission model for RBAC."""
    
    __tablename__ = 'call_distributor_permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(String(256))
    
    # Permission scope
    resource = Column(String(64), nullable=False)  # e.g., 'queue', 'agent', 'callback'
    action = Column(String(32), nullable=False)  # e.g., 'read', 'write', 'delete'
    
    # Relationships
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')
    
    def __repr__(self):
        return f'<Permission(name={self.name})>'
    
    @property
    def to_dict(self):
        """Convert permission to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action
        }

class TenantConfig(Base):
    """Tenant configuration model."""
    
    __tablename__ = 'call_distributor_tenant_configs'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, unique=True)
    
    # Feature flags
    enable_callbacks = Column(Boolean, default=True)
    enable_skills = Column(Boolean, default=True)
    enable_schedules = Column(Boolean, default=True)
    enable_monitoring = Column(Boolean, default=True)
    
    # Limits
    max_queues = Column(Integer, default=0)  # 0 = unlimited
    max_agents = Column(Integer, default=0)  # 0 = unlimited
    max_concurrent_calls = Column(Integer, default=0)  # 0 = unlimited
    
    # Custom settings
    settings = Column(String(1024), default='{}')  # JSON string
    
    def __repr__(self):
        return f'<TenantConfig(tenant_uuid={self.tenant_uuid})>'
    
    @property
    def to_dict(self):
        """Convert tenant config to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'enable_callbacks': self.enable_callbacks,
            'enable_skills': self.enable_skills,
            'enable_schedules': self.enable_schedules,
            'enable_monitoring': self.enable_monitoring,
            'max_queues': self.max_queues,
            'max_agents': self.max_agents,
            'max_concurrent_calls': self.max_concurrent_calls,
            'settings': self.settings
        }
