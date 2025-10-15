"""RBAC service for multi-tenant support."""

from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session
from ..models import Role, Permission, TenantConfig, Agent
from ..exceptions import AgentNotFound

class RBACService:
    """Service for managing roles and permissions."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_role(self, role_id: int, tenant_uuid: str) -> Role:
        """Get a role by ID."""
        role = self.session.query(Role).filter(
            Role.id == role_id,
            Role.tenant_uuid == tenant_uuid
        ).first()
        
        if not role:
            raise ValueError(f"Role {role_id} not found")
        
        return role
    
    def list_roles(self, tenant_uuid: str) -> List[Role]:
        """List all roles for a tenant."""
        return self.session.query(Role).filter(
            Role.tenant_uuid == tenant_uuid
        ).all()
    
    def create_role(self, tenant_uuid: str, role_data: Dict) -> Role:
        """Create a new role."""
        role = Role(tenant_uuid=tenant_uuid, **role_data)
        
        # Add permissions if provided
        if 'permission_ids' in role_data:
            permissions = self.session.query(Permission).filter(
                Permission.id.in_(role_data['permission_ids'])
            ).all()
            role.permissions = permissions
        
        self.session.add(role)
        self.session.commit()
        return role
    
    def update_role(self, role_id: int, tenant_uuid: str,
                   role_data: Dict) -> Role:
        """Update an existing role."""
        role = self.get_role(role_id, tenant_uuid)
        
        # Update basic fields
        for key in ['name', 'description']:
            if key in role_data:
                setattr(role, key, role_data[key])
        
        # Update permissions if provided
        if 'permission_ids' in role_data:
            permissions = self.session.query(Permission).filter(
                Permission.id.in_(role_data['permission_ids'])
            ).all()
            role.permissions = permissions
        
        self.session.commit()
        return role
    
    def delete_role(self, role_id: int, tenant_uuid: str) -> None:
        """Delete a role."""
        role = self.get_role(role_id, tenant_uuid)
        
        if role.is_system_role:
            raise ValueError("Cannot delete system role")
        
        self.session.delete(role)
        self.session.commit()
    
    def get_permission(self, permission_id: int) -> Permission:
        """Get a permission by ID."""
        permission = self.session.query(Permission).get(permission_id)
        
        if not permission:
            raise ValueError(f"Permission {permission_id} not found")
        
        return permission
    
    def list_permissions(self) -> List[Permission]:
        """List all available permissions."""
        return self.session.query(Permission).all()
    
    def create_permission(self, permission_data: Dict) -> Permission:
        """Create a new permission."""
        permission = Permission(**permission_data)
        self.session.add(permission)
        self.session.commit()
        return permission
    
    def delete_permission(self, permission_id: int) -> None:
        """Delete a permission."""
        permission = self.get_permission(permission_id)
        self.session.delete(permission)
        self.session.commit()
    
    def assign_role_to_agent(self, agent_id: int, role_id: int,
                           tenant_uuid: str) -> Agent:
        """Assign a role to an agent."""
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        role = self.get_role(role_id, tenant_uuid)
        agent.roles.append(role)
        
        self.session.commit()
        return agent
    
    def remove_role_from_agent(self, agent_id: int, role_id: int,
                             tenant_uuid: str) -> Agent:
        """Remove a role from an agent."""
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        role = self.get_role(role_id, tenant_uuid)
        agent.roles.remove(role)
        
        self.session.commit()
        return agent
    
    def get_agent_permissions(self, agent_id: int,
                            tenant_uuid: str) -> Set[Permission]:
        """Get all permissions for an agent."""
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        permissions = set()
        for role in agent.roles:
            permissions.update(role.permissions)
        
        return permissions
    
    def check_permission(self, agent_id: int, tenant_uuid: str,
                        resource: str, action: str) -> bool:
        """Check if an agent has a specific permission."""
        permissions = self.get_agent_permissions(agent_id, tenant_uuid)
        
        return any(
            p.resource == resource and p.action == action
            for p in permissions
        )
    
    def get_tenant_config(self, tenant_uuid: str) -> TenantConfig:
        """Get tenant configuration."""
        config = self.session.query(TenantConfig).filter(
            TenantConfig.tenant_uuid == tenant_uuid
        ).first()
        
        if not config:
            # Create default config
            config = TenantConfig(tenant_uuid=tenant_uuid)
            self.session.add(config)
            self.session.commit()
        
        return config
    
    def update_tenant_config(self, tenant_uuid: str,
                           config_data: Dict) -> TenantConfig:
        """Update tenant configuration."""
        config = self.get_tenant_config(tenant_uuid)
        
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.session.commit()
        return config
    
    def initialize_system_roles(self, tenant_uuid: str) -> List[Role]:
        """Initialize system roles for a new tenant."""
        # Create permissions if they don't exist
        permissions = {
            'queue_read': {'resource': 'queue', 'action': 'read'},
            'queue_write': {'resource': 'queue', 'action': 'write'},
            'agent_read': {'resource': 'agent', 'action': 'read'},
            'agent_write': {'resource': 'agent', 'action': 'write'},
            'callback_read': {'resource': 'callback', 'action': 'read'},
            'callback_write': {'resource': 'callback', 'action': 'write'},
            'monitor_read': {'resource': 'monitor', 'action': 'read'},
            'monitor_write': {'resource': 'monitor', 'action': 'write'},
            'settings_read': {'resource': 'settings', 'action': 'read'},
            'settings_write': {'resource': 'settings', 'action': 'write'}
        }
        
        permission_map = {}
        for name, data in permissions.items():
            permission = self.session.query(Permission).filter(
                Permission.name == name
            ).first()
            
            if not permission:
                permission = Permission(name=name, **data)
                self.session.add(permission)
            
            permission_map[name] = permission
        
        # Create system roles
        roles = []
        
        # Admin role
        admin_role = self.session.query(Role).filter(
            Role.tenant_uuid == tenant_uuid,
            Role.name == 'admin'
        ).first()
        
        if not admin_role:
            admin_role = Role(
                tenant_uuid=tenant_uuid,
                name='admin',
                description='Full access to all features',
                is_system_role=True,
                permissions=list(permission_map.values())
            )
            self.session.add(admin_role)
            roles.append(admin_role)
        
        # Supervisor role
        supervisor_role = self.session.query(Role).filter(
            Role.tenant_uuid == tenant_uuid,
            Role.name == 'supervisor'
        ).first()
        
        if not supervisor_role:
            supervisor_role = Role(
                tenant_uuid=tenant_uuid,
                name='supervisor',
                description='Monitor and manage queues and agents',
                is_system_role=True,
                permissions=[
                    permission_map['queue_read'],
                    permission_map['queue_write'],
                    permission_map['agent_read'],
                    permission_map['agent_write'],
                    permission_map['monitor_read'],
                    permission_map['monitor_write']
                ]
            )
            self.session.add(supervisor_role)
            roles.append(supervisor_role)
        
        # Agent role
        agent_role = self.session.query(Role).filter(
            Role.tenant_uuid == tenant_uuid,
            Role.name == 'agent'
        ).first()
        
        if not agent_role:
            agent_role = Role(
                tenant_uuid=tenant_uuid,
                name='agent',
                description='Basic agent access',
                is_system_role=True,
                permissions=[
                    permission_map['queue_read'],
                    permission_map['agent_read'],
                    permission_map['callback_read'],
                    permission_map['callback_write']
                ]
            )
            self.session.add(agent_role)
            roles.append(agent_role)
        
        self.session.commit()
        return roles
