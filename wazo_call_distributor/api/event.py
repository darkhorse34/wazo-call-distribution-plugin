"""Event API endpoints."""

from datetime import datetime
from flask import request, jsonify, Blueprint, current_app
from marshmallow import Schema, fields, validate
import redis
from ..services.event import EventService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import QueueNotFound, AgentNotFound

bp = Blueprint('events', __name__)

class EventSchema(Schema):
    """Schema for event validation."""
    event_type = fields.Str(required=True, validate=validate.OneOf(['call', 'agent', 'queue', 'system']))
    event_name = fields.Str(required=True)
    queue_id = fields.Int()
    agent_id = fields.Int()
    call_id = fields.Str()
    data = fields.Dict()

class TimeRangeSchema(Schema):
    """Schema for time range validation."""
    start_time = fields.DateTime()
    end_time = fields.DateTime()

event_schema = EventSchema()
time_range_schema = TimeRangeSchema()

def get_event_service():
    """Get or create an event service."""
    redis_client = redis.from_url(current_app.config['call_distributor']['redis_url'])
    return EventService(request.db_session, redis_client)

@bp.route('/events', methods=['POST'])
@require_token
def record_event():
    """Record a new event."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = event_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_event_service()
    event = service.record_event(
        tenant_uuid,
        data['event_type'],
        data['event_name'],
        data.get('data', {})
    )
    
    return jsonify(event.to_dict), 201

@bp.route('/queues/<int:queue_id>/metrics', methods=['GET'])
@require_token
def get_queue_metrics(queue_id):
    """Get queue metrics."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.args
    
    errors = time_range_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_event_service()
    try:
        if 'start_time' in data or 'end_time' in data:
            # Historical metrics
            start_time = datetime.fromisoformat(data['start_time']) if 'start_time' in data else None
            end_time = datetime.fromisoformat(data['end_time']) if 'end_time' in data else None
            metrics = service.get_queue_metrics(queue_id, tenant_uuid, start_time, end_time)
            return jsonify([m.to_dict for m in metrics])
        else:
            # Real-time metrics
            metrics = service.get_realtime_queue_metrics(queue_id, tenant_uuid)
            return jsonify(metrics)
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/metrics', methods=['GET'])
@require_token
def get_agent_metrics(agent_id):
    """Get agent metrics."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.args
    
    errors = time_range_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_event_service()
    try:
        if 'start_time' in data or 'end_time' in data:
            # Historical metrics
            start_time = datetime.fromisoformat(data['start_time']) if 'start_time' in data else None
            end_time = datetime.fromisoformat(data['end_time']) if 'end_time' in data else None
            metrics = service.get_agent_metrics(agent_id, tenant_uuid, start_time, end_time)
            return jsonify([m.to_dict for m in metrics])
        else:
            # Real-time metrics
            metrics = service.get_realtime_agent_metrics(agent_id, tenant_uuid)
            return jsonify(metrics)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/queues/<int:queue_id>/stats/summary', methods=['GET'])
@require_token
def get_queue_stats_summary(queue_id):
    """Get queue statistics summary."""
    tenant_uuid = get_token_tenant_uuid()
    interval = request.args.get('interval', '1h')
    
    if interval not in ['1h', '6h', '24h']:
        return {'message': "Invalid interval. Must be '1h', '6h', or '24h'"}, 400
    
    service = get_event_service()
    try:
        summary = service.get_queue_stats_summary(queue_id, tenant_uuid, interval)
        return jsonify(summary)
    except QueueNotFound:
        return {'message': f'Queue {queue_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/stats/summary', methods=['GET'])
@require_token
def get_agent_stats_summary(agent_id):
    """Get agent statistics summary."""
    tenant_uuid = get_token_tenant_uuid()
    interval = request.args.get('interval', '1h')
    
    if interval not in ['1h', '6h', '24h']:
        return {'message': "Invalid interval. Must be '1h', '6h', or '24h'"}, 400
    
    service = get_event_service()
    try:
        summary = service.get_agent_stats_summary(agent_id, tenant_uuid, interval)
        return jsonify(summary)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404
