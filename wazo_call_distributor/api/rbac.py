"""RBAC API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.rbac import RBACService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import AgentNotFound

bp = Blueprint('rbac', __name__)

class RoleSchema(Schema):
    """Schema for role validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    permission_ids = fields.List(fields.Int())

class PermissionSchema(Schema):
    """Schema for permission validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    resource = fields.Str(required=True, validate=validate.Length(min=1, max=64))
    action = fields.Str(required=True, validate=validate.Length(min=1, max=32))

class TenantConfigSchema(Schema):
    """Schema for tenant configuration validation."""
    enable_callbacks = fields.Bool()
    enable_skills = fields.Bool()
    enable_schedules = fields.Bool()
    enable_monitoring = fields.Bool()
    max_queues = fields.Int(validate=validate.Range(min=0))
    max_agents = fields.Int(validate=validate.Range(min=0))
    max_concurrent_calls = fields.Int(validate=validate.Range(min=0))
    settings = fields.Str(validate=validate.Length(max=1024))

role_schema = RoleSchema()
permission_schema = PermissionSchema()
tenant_config_schema = TenantConfigSchema()

@bp.route('/roles', methods=['GET'])
@require_token
def list_roles():
    """List all roles for the tenant."""
    tenant_uuid = get_token_tenant_uuid()
    service = RBACService(request.db_session)
    roles = service.list_roles(tenant_uuid)
    return jsonify([role.to_dict for role in roles])

@bp.route('/roles', methods=['POST'])
@require_token
def create_role():
    """Create a new role."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = role_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = RBACService(request.db_session)
    role = service.create_role(tenant_uuid, data)
    return jsonify(role.to_dict), 201

@bp.route('/roles/<int:role_id>', methods=['PUT'])
@require_token
def update_role(role_id):
    """Update an existing role."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = role_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = RBACService(request.db_session)
    try:
        role = service.update_role(role_id, tenant_uuid, data)
        return jsonify(role.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/roles/<int:role_id>', methods=['DELETE'])
@require_token
def delete_role(role_id):
    """Delete a role."""
    tenant_uuid = get_token_tenant_uuid()
    service = RBACService(request.db_session)
    try:
        service.delete_role(role_id, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 400

@bp.route('/permissions', methods=['GET'])
@require_token
def list_permissions():
    """List all available permissions."""
    service = RBACService(request.db_session)
    permissions = service.list_permissions()
    return jsonify([permission.to_dict for permission in permissions])

@bp.route('/permissions', methods=['POST'])
@require_token
def create_permission():
    """Create a new permission."""
    data = request.get_json()
    
    errors = permission_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = RBACService(request.db_session)
    permission = service.create_permission(data)
    return jsonify(permission.to_dict), 201

@bp.route('/permissions/<int:permission_id>', methods=['DELETE'])
@require_token
def delete_permission(permission_id):
    """Delete a permission."""
    service = RBACService(request.db_session)
    try:
        service.delete_permission(permission_id)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/agents/<int:agent_id>/roles/<int:role_id>', methods=['PUT'])
@require_token
def assign_role_to_agent(agent_id, role_id):
    """Assign a role to an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = RBACService(request.db_session)
    try:
        agent = service.assign_role_to_agent(agent_id, role_id, tenant_uuid)
        return jsonify({
            'agent_id': agent.id,
            'roles': [role.to_dict for role in agent.roles]
        })
    except (AgentNotFound, ValueError) as e:
        return {'message': str(e)}, 404

@bp.route('/agents/<int:agent_id>/roles/<int:role_id>', methods=['DELETE'])
@require_token
def remove_role_from_agent(agent_id, role_id):
    """Remove a role from an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = RBACService(request.db_session)
    try:
        agent = service.remove_role_from_agent(agent_id, role_id, tenant_uuid)
        return jsonify({
            'agent_id': agent.id,
            'roles': [role.to_dict for role in agent.roles]
        })
    except (AgentNotFound, ValueError) as e:
        return {'message': str(e)}, 404

@bp.route('/agents/<int:agent_id>/permissions', methods=['GET'])
@require_token
def get_agent_permissions(agent_id):
    """Get all permissions for an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = RBACService(request.db_session)
    try:
        permissions = service.get_agent_permissions(agent_id, tenant_uuid)
        return jsonify([permission.to_dict for permission in permissions])
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/permissions/check', methods=['POST'])
@require_token
def check_permission(agent_id):
    """Check if an agent has a specific permission."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    if 'resource' not in data or 'action' not in data:
        return {'message': 'resource and action are required'}, 400
    
    service = RBACService(request.db_session)
    try:
        has_permission = service.check_permission(
            agent_id,
            tenant_uuid,
            data['resource'],
            data['action']
        )
        return jsonify({'has_permission': has_permission})
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/tenant/config', methods=['GET'])
@require_token
def get_tenant_config():
    """Get tenant configuration."""
    tenant_uuid = get_token_tenant_uuid()
    service = RBACService(request.db_session)
    config = service.get_tenant_config(tenant_uuid)
    return jsonify(config.to_dict)

@bp.route('/tenant/config', methods=['PUT'])
@require_token
def update_tenant_config():
    """Update tenant configuration."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = tenant_config_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = RBACService(request.db_session)
    config = service.update_tenant_config(tenant_uuid, data)
    return jsonify(config.to_dict)

@bp.route('/tenant/initialize', methods=['POST'])
@require_token
def initialize_tenant():
    """Initialize system roles for a tenant."""
    tenant_uuid = get_token_tenant_uuid()
    service = RBACService(request.db_session)
    roles = service.initialize_system_roles(tenant_uuid)
    return jsonify([role.to_dict for role in roles])
