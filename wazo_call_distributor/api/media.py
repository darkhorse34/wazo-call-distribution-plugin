"""Media API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.media import MediaService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import QueueNotFound

bp = Blueprint('media', __name__)

class AnnouncementSchema(Schema):
    """Schema for announcement validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    type = fields.Str(required=True, validate=validate.OneOf([
        'entrance', 'periodic', 'position', 'wait_time'
    ]))
    media_type = fields.Str(required=True, validate=validate.OneOf(['sound', 'tts']))
    media_source = fields.Str(required=True, validate=validate.Length(max=256))
    language = fields.Str(validate=validate.Length(max=10))
    voice = fields.Str(validate=validate.Length(max=32))
    enabled = fields.Bool()
    interval = fields.Int(validate=validate.Range(min=0))
    position_frequency = fields.Int(validate=validate.Range(min=0))
    wait_time_frequency = fields.Int(validate=validate.Range(min=0))

class MohSchema(Schema):
    """Schema for music on hold validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    mode = fields.Str(validate=validate.OneOf(['files', 'random', 'linear']))
    directory = fields.Str(required=True, validate=validate.Length(max=256))

announcement_schema = AnnouncementSchema()
moh_schema = MohSchema()

@bp.route('/queues/<int:queue_id>/announcements', methods=['GET'])
@require_token
def list_announcements(queue_id):
    """List all announcements for a queue."""
    tenant_uuid = get_token_tenant_uuid()
    service = MediaService(request.db_session)
    try:
        announcements = service.list_announcements(queue_id, tenant_uuid)
        return jsonify([announcement.to_dict for announcement in announcements])
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/announcements', methods=['POST'])
@require_token
def create_announcement(queue_id):
    """Create a new announcement."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = announcement_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = MediaService(request.db_session)
    try:
        announcement = service.create_announcement(queue_id, tenant_uuid, data)
        return jsonify(announcement.to_dict), 201
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/announcements/<int:announcement_id>', methods=['PUT'])
@require_token
def update_announcement(announcement_id):
    """Update an existing announcement."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = announcement_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = MediaService(request.db_session)
    try:
        announcement = service.update_announcement(announcement_id, tenant_uuid, data)
        return jsonify(announcement.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/announcements/<int:announcement_id>', methods=['DELETE'])
@require_token
def delete_announcement(announcement_id):
    """Delete an announcement."""
    tenant_uuid = get_token_tenant_uuid()
    service = MediaService(request.db_session)
    try:
        service.delete_announcement(announcement_id, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/moh', methods=['GET'])
@require_token
def list_moh():
    """List all music on hold classes."""
    tenant_uuid = get_token_tenant_uuid()
    service = MediaService(request.db_session)
    moh_classes = service.list_moh(tenant_uuid)
    return jsonify([moh.to_dict for moh in moh_classes])

@bp.route('/moh', methods=['POST'])
@require_token
def create_moh():
    """Create a new music on hold class."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = moh_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = MediaService(request.db_session)
    moh = service.create_moh(tenant_uuid, data)
    return jsonify(moh.to_dict), 201

@bp.route('/moh/<int:moh_id>', methods=['PUT'])
@require_token
def update_moh(moh_id):
    """Update an existing music on hold class."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = moh_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = MediaService(request.db_session)
    try:
        moh = service.update_moh(moh_id, tenant_uuid, data)
        return jsonify(moh.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/moh/<int:moh_id>', methods=['DELETE'])
@require_token
def delete_moh(moh_id):
    """Delete a music on hold class."""
    tenant_uuid = get_token_tenant_uuid()
    service = MediaService(request.db_session)
    try:
        service.delete_moh(moh_id, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/queues/<int:queue_id>/position/<string:call_id>', methods=['GET'])
@require_token
def get_queue_position(queue_id, call_id):
    """Get position in queue for a call."""
    tenant_uuid = get_token_tenant_uuid()
    service = MediaService(request.db_session)
    
    try:
        position = service.get_queue_position(queue_id, call_id)
        if position is None:
            return {'message': 'Call not found in queue'}, 404
        
        wait_time = service.estimate_wait_time(queue_id, position)
        return jsonify({
            'position': position,
            'estimated_wait_time': wait_time
        })
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/announce/position', methods=['POST'])
@require_token
def should_announce_position(queue_id):
    """Check if position should be announced."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    if 'position' not in data or 'last_announce' not in data:
        return {'message': 'position and last_announce are required'}, 400
    
    service = MediaService(request.db_session)
    try:
        should_announce = service.should_announce_position(
            queue_id,
            tenant_uuid,
            data['position'],
            data['last_announce']
        )
        return jsonify({'should_announce': should_announce})
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/announce/wait-time', methods=['POST'])
@require_token
def should_announce_wait_time(queue_id):
    """Check if wait time should be announced."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    if 'wait_time' not in data or 'last_announce' not in data:
        return {'message': 'wait_time and last_announce are required'}, 400
    
    service = MediaService(request.db_session)
    try:
        should_announce = service.should_announce_wait_time(
            queue_id,
            tenant_uuid,
            data['wait_time'],
            data['last_announce']
        )
        return jsonify({'should_announce': should_announce})
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404
