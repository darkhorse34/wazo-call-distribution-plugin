"""Policy API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.policy import PolicyService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import QueueNotFound

bp = Blueprint('policies', __name__)

class CallerPrioritySchema(Schema):
    """Schema for caller priority validation."""
    number = fields.Str(required=True, validate=validate.Length(min=1, max=32))
    priority_type = fields.Str(required=True, validate=validate.OneOf(['vip', 'blacklist']))
    priority_level = fields.Int(validate=validate.Range(min=0))
    description = fields.Str(validate=validate.Length(max=256))

class SkillRequirementSchema(Schema):
    """Schema for skill requirement validation."""
    skill_id = fields.Int(required=True)
    min_level = fields.Int(validate=validate.Range(min=0, max=100))

class StickyAgentSchema(Schema):
    """Schema for sticky agent validation."""
    caller_id = fields.Str(required=True)
    agent_id = fields.Int(required=True)

caller_priority_schema = CallerPrioritySchema()
skill_requirement_schema = SkillRequirementSchema(many=True)
sticky_agent_schema = StickyAgentSchema()

@bp.route('/caller-priorities', methods=['POST'])
@require_token
def set_caller_priority():
    """Set priority for a caller (VIP/blacklist)."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = caller_priority_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = PolicyService(request.db_session)
    priority = service.set_caller_priority(tenant_uuid, data)
    return jsonify(priority.to_dict), 201

@bp.route('/caller-priorities/<string:number>', methods=['GET'])
@require_token
def get_caller_priority(number):
    """Get priority settings for a caller."""
    tenant_uuid = get_token_tenant_uuid()
    service = PolicyService(request.db_session)
    
    priority = service.get_caller_priority(tenant_uuid, number)
    if not priority:
        return {'message': f'No priority settings found for {number}'}, 404
    
    return jsonify(priority.to_dict)

@bp.route('/queues/<int:queue_id>/agents/skills', methods=['POST'])
@require_token
def get_agents_by_skills(queue_id):
    """Get agents matching required skills."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = skill_requirement_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = PolicyService(request.db_session)
    try:
        agents = service.get_agents_by_skills(queue_id, tenant_uuid, data)
        return jsonify([agent.to_dict for agent in agents])
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/sticky-agent', methods=['POST'])
@require_token
def set_sticky_agent(queue_id):
    """Set sticky agent for a caller."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = sticky_agent_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = PolicyService(request.db_session)
    try:
        service.set_sticky_agent(queue_id, tenant_uuid, data['caller_id'], data['agent_id'])
        return '', 204
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/sticky-agent/<string:caller_id>', methods=['GET'])
@require_token
def get_sticky_agent(queue_id, caller_id):
    """Get sticky agent for a caller."""
    tenant_uuid = get_token_tenant_uuid()
    service = PolicyService(request.db_session)
    
    try:
        agent = service.get_sticky_agent(queue_id, tenant_uuid, caller_id)
        if not agent:
            return {'message': 'No sticky agent found'}, 404
        return jsonify(agent.to_dict)
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/overflow', methods=['GET'])
@require_token
def get_overflow_target(queue_id):
    """Get overflow target based on wait time."""
    tenant_uuid = get_token_tenant_uuid()
    wait_time = request.args.get('wait_time', type=int)
    
    if wait_time is None:
        return {'message': 'wait_time parameter is required'}, 400
    
    service = PolicyService(request.db_session)
    try:
        target = service.get_overflow_target(queue_id, tenant_uuid, wait_time)
        if not target:
            return {'message': 'No overflow target available'}, 404
        return jsonify({
            'target_type': target[0],
            'target_id': target[1]
        })
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/position', methods=['POST'])
@require_token
def adjust_queue_position(queue_id):
    """Adjust caller's position based on VIP status."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    if 'caller_id' not in data or 'current_position' not in data:
        return {'message': 'caller_id and current_position are required'}, 400
    
    service = PolicyService(request.db_session)
    try:
        new_position = service.adjust_queue_position(
            queue_id,
            tenant_uuid,
            data['caller_id'],
            data['current_position']
        )
        return jsonify({'new_position': new_position})
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404
