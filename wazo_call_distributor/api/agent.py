"""Agent API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.agent import AgentService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import AgentNotFound, InvalidSkillLevel

bp = Blueprint('agents', __name__)

class AgentSchema(Schema):
    """Schema for agent validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    number = fields.Str(required=True, validate=validate.Length(min=1, max=32))
    agent_type = fields.Str(validate=validate.OneOf(['static', 'dynamic']))

class AgentSkillSchema(Schema):
    """Schema for agent skill validation."""
    skill_id = fields.Int(required=True)
    level = fields.Int(required=True, validate=validate.Range(min=0, max=100))

class PauseSchema(Schema):
    """Schema for agent pause validation."""
    reason = fields.Str(validate=validate.Length(max=128))

agent_schema = AgentSchema()
agent_skill_schema = AgentSkillSchema()
pause_schema = PauseSchema()

@bp.route('/agents', methods=['GET'])
@require_token
def list_agents():
    """List all agents for the tenant."""
    tenant_uuid = get_token_tenant_uuid()
    service = AgentService(request.db_session)
    agents = service.list(tenant_uuid)
    return jsonify([agent.to_dict for agent in agents])

@bp.route('/agents/<int:agent_id>', methods=['GET'])
@require_token
def get_agent(agent_id):
    """Get a specific agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = AgentService(request.db_session)
    try:
        agent = service.get(agent_id, tenant_uuid)
        return jsonify(agent.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents', methods=['POST'])
@require_token
def create_agent():
    """Create a new agent."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = agent_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = AgentService(request.db_session)
    agent = service.create(tenant_uuid, data)
    return jsonify(agent.to_dict), 201

@bp.route('/agents/<int:agent_id>', methods=['PUT'])
@require_token
def update_agent(agent_id):
    """Update an existing agent."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = agent_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = AgentService(request.db_session)
    try:
        agent = service.update(agent_id, tenant_uuid, data)
        return jsonify(agent.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>', methods=['DELETE'])
@require_token
def delete_agent(agent_id):
    """Delete an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = AgentService(request.db_session)
    try:
        service.delete(agent_id, tenant_uuid)
        return '', 204
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/login', methods=['POST'])
@require_token
def login_agent(agent_id):
    """Log in an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = AgentService(request.db_session)
    try:
        agent = service.login(agent_id, tenant_uuid)
        return jsonify(agent.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/logout', methods=['POST'])
@require_token
def logout_agent(agent_id):
    """Log out an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = AgentService(request.db_session)
    try:
        agent = service.logout(agent_id, tenant_uuid)
        return jsonify(agent.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/pause', methods=['POST'])
@require_token
def pause_agent(agent_id):
    """Pause an agent."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json() or {}
    
    errors = pause_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = AgentService(request.db_session)
    try:
        agent = service.pause(agent_id, tenant_uuid, data.get('reason'))
        return jsonify(agent.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/unpause', methods=['POST'])
@require_token
def unpause_agent(agent_id):
    """Unpause an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = AgentService(request.db_session)
    try:
        agent = service.unpause(agent_id, tenant_uuid)
        return jsonify(agent.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/skills', methods=['GET'])
@require_token
def get_agent_skills(agent_id):
    """Get all skills for an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = AgentService(request.db_session)
    try:
        skills = service.get_skills(agent_id, tenant_uuid)
        return jsonify(skills)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/skills', methods=['POST'])
@require_token
def add_agent_skill(agent_id):
    """Add a skill to an agent."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = agent_skill_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = AgentService(request.db_session)
    try:
        skill = service.add_skill(agent_id, tenant_uuid, data['skill_id'], data['level'])
        return jsonify(skill.to_dict), 201
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404
    except InvalidSkillLevel as e:
        return {'message': str(e)}, 400

@bp.route('/agents/<int:agent_id>/skills/<int:skill_id>', methods=['DELETE'])
@require_token
def remove_agent_skill(agent_id, skill_id):
    """Remove a skill from an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = AgentService(request.db_session)
    try:
        service.remove_skill(agent_id, tenant_uuid, skill_id)
        return '', 204
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/queues', methods=['GET'])
@require_token
def get_agent_queues(agent_id):
    """Get all queues for an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = AgentService(request.db_session)
    try:
        queues = service.get_queues(agent_id, tenant_uuid)
        return jsonify(queues)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404
