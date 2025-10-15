"""Callback API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.callback import CallbackService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import QueueNotFound, AgentNotFound

bp = Blueprint('callbacks', __name__)

class CallbackRequestSchema(Schema):
    """Schema for callback request validation."""
    queue_id = fields.Int(required=True)
    caller_id = fields.Str(required=True)
    callback_number = fields.Str(required=True, validate=validate.Length(min=1, max=32))
    original_position = fields.Int()
    original_wait_time = fields.Int()
    preferred_time = fields.DateTime()
    priority = fields.Int(validate=validate.Range(min=0))

class CallbackScheduleSchema(Schema):
    """Schema for callback schedule validation."""
    queue_id = fields.Int(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    enabled = fields.Bool()
    start_time = fields.Str(required=True, validate=validate.Regexp(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'))
    end_time = fields.Str(required=True, validate=validate.Regexp(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'))
    days_of_week = fields.Str(required=True, validate=validate.Regexp(r'^[01]{7}$'))
    max_concurrent = fields.Int(validate=validate.Range(min=1))
    retry_interval = fields.Int(validate=validate.Range(min=0))
    max_attempts = fields.Int(validate=validate.Range(min=1))
    expiry_hours = fields.Int(validate=validate.Range(min=1))

class CallbackResultSchema(Schema):
    """Schema for callback result validation."""
    result = fields.Str(required=True)
    notes = fields.Str(validate=validate.Length(max=256))

callback_request_schema = CallbackRequestSchema()
callback_schedule_schema = CallbackScheduleSchema()
callback_result_schema = CallbackResultSchema()

@bp.route('/callbacks', methods=['POST'])
@require_token
def create_callback_request():
    """Create a new callback request."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = callback_request_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = CallbackService(request.db_session)
    try:
        callback = service.create_callback_request(tenant_uuid, data)
        return jsonify(callback.to_dict), 201
    except QueueNotFound:
        return {'message': f'Queue {data["queue_id"]} not found'}, 404

@bp.route('/callbacks/<int:callback_id>', methods=['GET'])
@require_token
def get_callback_request(callback_id):
    """Get a callback request."""
    tenant_uuid = get_token_tenant_uuid()
    service = CallbackService(request.db_session)
    try:
        callback = service.get_callback_request(callback_id, tenant_uuid)
        return jsonify(callback.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/callbacks', methods=['GET'])
@require_token
def list_callback_requests():
    """List callback requests."""
    tenant_uuid = get_token_tenant_uuid()
    queue_id = request.args.get('queue_id', type=int)
    status = request.args.get('status')
    agent_id = request.args.get('agent_id', type=int)
    
    service = CallbackService(request.db_session)
    callbacks = service.list_callback_requests(tenant_uuid, queue_id, status, agent_id)
    return jsonify([callback.to_dict for callback in callbacks])

@bp.route('/callbacks/<int:callback_id>/assign/<int:agent_id>', methods=['PUT'])
@require_token
def assign_callback_request(callback_id, agent_id):
    """Assign a callback request to an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = CallbackService(request.db_session)
    try:
        callback = service.assign_callback_request(callback_id, agent_id, tenant_uuid)
        return jsonify(callback.to_dict)
    except (ValueError, AgentNotFound) as e:
        return {'message': str(e)}, 404

@bp.route('/callbacks/<int:callback_id>/start/<int:agent_id>', methods=['PUT'])
@require_token
def start_callback(callback_id, agent_id):
    """Start processing a callback request."""
    tenant_uuid = get_token_tenant_uuid()
    service = CallbackService(request.db_session)
    try:
        callback = service.start_callback(callback_id, agent_id, tenant_uuid)
        return jsonify(callback.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 400

@bp.route('/callbacks/<int:callback_id>/complete/<int:agent_id>', methods=['PUT'])
@require_token
def complete_callback(callback_id, agent_id):
    """Complete a callback request."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = callback_result_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = CallbackService(request.db_session)
    try:
        callback = service.complete_callback(
            callback_id,
            agent_id,
            tenant_uuid,
            data['result'],
            data.get('notes')
        )
        return jsonify(callback.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 400

@bp.route('/callbacks/<int:callback_id>/fail', methods=['PUT'])
@require_token
def fail_callback(callback_id):
    """Mark a callback request as failed."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    retry = request.args.get('retry', 'true').lower() == 'true'
    
    errors = callback_result_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = CallbackService(request.db_session)
    try:
        callback = service.fail_callback(
            callback_id,
            tenant_uuid,
            data['result'],
            data.get('notes'),
            retry
        )
        return jsonify(callback.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 400

@bp.route('/callbacks/<int:callback_id>/cancel', methods=['PUT'])
@require_token
def cancel_callback(callback_id):
    """Cancel a callback request."""
    tenant_uuid = get_token_tenant_uuid()
    notes = request.get_json().get('notes')
    
    service = CallbackService(request.db_session)
    try:
        callback = service.cancel_callback(callback_id, tenant_uuid, notes)
        return jsonify(callback.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 400

@bp.route('/callback-schedules', methods=['GET'])
@require_token
def list_callback_schedules():
    """List callback schedules."""
    tenant_uuid = get_token_tenant_uuid()
    queue_id = request.args.get('queue_id', type=int)
    
    service = CallbackService(request.db_session)
    schedules = service.list_callback_schedules(tenant_uuid, queue_id)
    return jsonify([schedule.to_dict for schedule in schedules])

@bp.route('/callback-schedules', methods=['POST'])
@require_token
def create_callback_schedule():
    """Create a new callback schedule."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = callback_schedule_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = CallbackService(request.db_session)
    try:
        schedule = service.create_callback_schedule(tenant_uuid, data)
        return jsonify(schedule.to_dict), 201
    except QueueNotFound:
        return {'message': f'Queue {data["queue_id"]} not found'}, 404

@bp.route('/callback-schedules/<int:schedule_id>', methods=['PUT'])
@require_token
def update_callback_schedule(schedule_id):
    """Update a callback schedule."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = callback_schedule_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = CallbackService(request.db_session)
    try:
        schedule = service.update_callback_schedule(schedule_id, tenant_uuid, data)
        return jsonify(schedule.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/callback-schedules/<int:schedule_id>', methods=['DELETE'])
@require_token
def delete_callback_schedule(schedule_id):
    """Delete a callback schedule."""
    tenant_uuid = get_token_tenant_uuid()
    service = CallbackService(request.db_session)
    try:
        service.delete_callback_schedule(schedule_id, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/callbacks/process-expired', methods=['POST'])
@require_token
def process_expired_callbacks():
    """Process expired callback requests."""
    tenant_uuid = get_token_tenant_uuid()
    service = CallbackService(request.db_session)
    count = service.process_expired_callbacks(tenant_uuid)
    return jsonify({'expired_count': count})

@bp.route('/callbacks/next/<int:agent_id>', methods=['GET'])
@require_token
def get_next_callback(agent_id):
    """Get the next callback request for an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = CallbackService(request.db_session)
    try:
        callback = service.get_next_callback(agent_id, tenant_uuid)
        if not callback:
            return {'message': 'No callbacks available'}, 404
        return jsonify(callback.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404
