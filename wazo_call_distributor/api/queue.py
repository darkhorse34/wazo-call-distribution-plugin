"""Queue API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.queue import QueueService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import QueueNotFound, InvalidQueueStrategy

bp = Blueprint('queues', __name__)

class QueueSchema(Schema):
    """Schema for queue validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    strategy = fields.Str(validate=validate.OneOf([
        'ringall', 'leastrecent', 'fewestcalls', 'random', 'rrmemory', 'linear'
    ]))
    timeout = fields.Int(validate=validate.Range(min=0))
    max_wait = fields.Int(validate=validate.Range(min=0))
    service_level = fields.Int(validate=validate.Range(min=0))
    weight = fields.Int(validate=validate.Range(min=0))
    max_callers = fields.Int(validate=validate.Range(min=0))
    max_members = fields.Int(validate=validate.Range(min=0))
    announce_position = fields.Bool()
    announce_holdtime = fields.Bool()
    periodic_announce = fields.Bool()
    moh_class = fields.Str()
    announce_frequency = fields.Int(validate=validate.Range(min=0))
    overflow_queue_id = fields.Int(allow_none=True)
    overflow_timeout = fields.Int(validate=validate.Range(min=0))

queue_schema = QueueSchema()

@bp.route('/queues', methods=['GET'])
@require_token
def list_queues():
    """List all queues for the tenant."""
    tenant_uuid = get_token_tenant_uuid()
    service = QueueService(request.db_session)
    queues = service.list(tenant_uuid)
    return jsonify([queue.to_dict for queue in queues])

@bp.route('/queues/<int:queue_id>', methods=['GET'])
@require_token
def get_queue(queue_id):
    """Get a specific queue."""
    tenant_uuid = get_token_tenant_uuid()
    service = QueueService(request.db_session)
    try:
        queue = service.get(queue_id, tenant_uuid)
        return jsonify(queue.to_dict)
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues', methods=['POST'])
@require_token
def create_queue():
    """Create a new queue."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = queue_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = QueueService(request.db_session)
    try:
        queue = service.create(tenant_uuid, data)
        return jsonify(queue.to_dict), 201
    except InvalidQueueStrategy as e:
        return {'message': str(e)}, 400

@bp.route('/queues/<int:queue_id>', methods=['PUT'])
@require_token
def update_queue(queue_id):
    """Update an existing queue."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = queue_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = QueueService(request.db_session)
    try:
        queue = service.update(queue_id, tenant_uuid, data)
        return jsonify(queue.to_dict)
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404
    except InvalidQueueStrategy as e:
        return {'message': str(e)}, 400

@bp.route('/queues/<int:queue_id>', methods=['DELETE'])
@require_token
def delete_queue(queue_id):
    """Delete a queue."""
    tenant_uuid = get_token_tenant_uuid()
    service = QueueService(request.db_session)
    try:
        service.delete(queue_id, tenant_uuid)
        return '', 204
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/stats', methods=['GET'])
@require_token
def get_queue_stats(queue_id):
    """Get real-time statistics for a queue."""
    tenant_uuid = get_token_tenant_uuid()
    service = QueueService(request.db_session)
    try:
        stats = service.get_queue_stats(queue_id, tenant_uuid)
        return jsonify(stats)
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/overflow', methods=['PUT'])
@require_token
def update_queue_overflow(queue_id):
    """Update queue overflow settings."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    overflow_schema = Schema.from_dict({
        'overflow_queue_id': fields.Int(allow_none=True),
        'overflow_timeout': fields.Int(validate=validate.Range(min=0))
    })
    
    errors = overflow_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = QueueService(request.db_session)
    try:
        queue = service.update_overflow_settings(
            queue_id,
            tenant_uuid,
            data.get('overflow_queue_id'),
            data.get('overflow_timeout', 0)
        )
        return jsonify(queue.to_dict)
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404
