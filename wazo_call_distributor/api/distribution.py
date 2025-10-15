"""Distribution API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields
from ..services.distribution import DistributionService
from ..auth import require_token, get_token_tenant_uuid
from ..exceptions import QueueNotFound, InvalidQueueStrategy

bp = Blueprint('distribution', __name__)

class CallSchema(Schema):
    """Schema for call information."""
    call_id = fields.Str(required=True)

class StatsSchema(Schema):
    """Schema for call statistics."""
    call_duration = fields.Int(required=True, validate=lambda n: n >= 0)

@bp.route('/queues/<int:queue_id>/next', methods=['POST'])
@require_token
def get_next_agents(queue_id):
    """Get next agent(s) for a call based on queue strategy."""
    tenant_uuid = get_token_tenant_uuid()
    
    schema = CallSchema()
    errors = schema.validate(request.get_json())
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    data = schema.load(request.get_json())
    service = DistributionService(request.db_session)
    
    try:
        agents = service.get_next_agents(queue_id, tenant_uuid, data['call_id'])
        if not agents:
            return {'message': 'No available agents'}, 404
        
        # Handle both single agent and list of agents
        if isinstance(agents, list):
            return jsonify([{
                'id': agent.id,
                'name': agent.name,
                'number': agent.number
            } for agent in agents])
        else:
            return jsonify({
                'id': agents.id,
                'name': agents.name,
                'number': agents.number
            })
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404
    except InvalidQueueStrategy as e:
        return {'message': str(e)}, 400

@bp.route('/queues/<int:queue_id>/agents/<int:agent_id>/stats', methods=['GET'])
@require_token
def get_agent_stats(queue_id, agent_id):
    """Get agent statistics for a queue."""
    tenant_uuid = get_token_tenant_uuid()
    service = DistributionService(request.db_session)
    
    try:
        stats = service.get_agent_stats(queue_id, agent_id)
        return jsonify(stats)
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404
    except InvalidQueueStrategy as e:
        return {'message': str(e)}, 400

@bp.route('/queues/<int:queue_id>/agents/<int:agent_id>/stats', methods=['PUT'])
@require_token
def update_agent_stats(queue_id, agent_id):
    """Update agent statistics after call completion."""
    tenant_uuid = get_token_tenant_uuid()
    
    schema = StatsSchema()
    errors = schema.validate(request.get_json())
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    data = schema.load(request.get_json())
    service = DistributionService(request.db_session)
    
    try:
        service.update_agent_stats(queue_id, agent_id, data['call_duration'])
        return '', 204
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404
    except InvalidQueueStrategy as e:
        return {'message': str(e)}, 400
