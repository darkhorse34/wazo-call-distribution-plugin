"""Supervisor API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.supervisor import SupervisorService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import AgentNotFound

bp = Blueprint('supervisor', __name__)

class SupervisorSettingsSchema(Schema):
    """Schema for supervisor settings validation."""
    wallboard_layout = fields.Dict()
    alert_settings = fields.Dict()
    default_view = fields.Str(validate=validate.OneOf(['wallboard', 'agents', 'queues']))
    refresh_interval = fields.Int(validate=validate.Range(min=1))
    auto_refresh = fields.Bool()
    custom_settings = fields.Dict()

class MonitoringProfileSchema(Schema):
    """Schema for monitoring profile validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    queues = fields.List(fields.Int())
    agents = fields.List(fields.Int())
    metrics = fields.List(fields.Str())
    layout = fields.Dict()
    filters = fields.Dict()

supervisor_settings_schema = SupervisorSettingsSchema()
monitoring_profile_schema = MonitoringProfileSchema()

@bp.route('/supervisors/<int:agent_id>/settings', methods=['GET'])
@require_token
def get_supervisor_settings(agent_id):
    """Get supervisor settings."""
    tenant_uuid = get_token_tenant_uuid()
    service = SupervisorService(request.db_session)
    try:
        settings = service.get_supervisor_settings(agent_id, tenant_uuid)
        return jsonify(settings.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/supervisors/<int:agent_id>/settings', methods=['PUT'])
@require_token
def update_supervisor_settings(agent_id):
    """Update supervisor settings."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = supervisor_settings_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = SupervisorService(request.db_session)
    try:
        settings = service.update_supervisor_settings(agent_id, tenant_uuid, data)
        return jsonify(settings.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/supervisors/<int:agent_id>/wallboard', methods=['GET'])
@require_token
def get_wallboard_data(agent_id):
    """Get wallboard data."""
    tenant_uuid = get_token_tenant_uuid()
    service = SupervisorService(request.db_session)
    try:
        data = service.get_wallboard_data(agent_id, tenant_uuid)
        return jsonify(data)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/supervisors/alerts/check', methods=['POST'])
@require_token
def check_thresholds():
    """Check metrics against thresholds."""
    tenant_uuid = get_token_tenant_uuid()
    service = SupervisorService(request.db_session)
    alerts = service.check_thresholds(tenant_uuid)
    return jsonify([alert.to_dict for alert in alerts])

@bp.route('/supervisors/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@require_token
def acknowledge_alert(alert_id):
    """Acknowledge an alert."""
    tenant_uuid = get_token_tenant_uuid()
    agent_id = request.get_json().get('agent_id')
    
    if not agent_id:
        return {'message': 'agent_id is required'}, 400
    
    service = SupervisorService(request.db_session)
    try:
        alert = service.acknowledge_alert(alert_id, agent_id, tenant_uuid)
        return jsonify(alert.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/supervisors/<int:agent_id>/profiles', methods=['GET'])
@require_token
def get_monitoring_profiles(agent_id):
    """Get monitoring profiles."""
    tenant_uuid = get_token_tenant_uuid()
    service = SupervisorService(request.db_session)
    try:
        profiles = service.get_monitoring_profiles(agent_id, tenant_uuid)
        return jsonify([profile.to_dict for profile in profiles])
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/supervisors/<int:agent_id>/profiles', methods=['POST'])
@require_token
def create_monitoring_profile(agent_id):
    """Create a new monitoring profile."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = monitoring_profile_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = SupervisorService(request.db_session)
    try:
        profile = service.create_monitoring_profile(agent_id, tenant_uuid, data)
        return jsonify(profile.to_dict), 201
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/supervisors/profiles/<int:profile_id>', methods=['PUT'])
@require_token
def update_monitoring_profile(profile_id):
    """Update an existing monitoring profile."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = monitoring_profile_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = SupervisorService(request.db_session)
    try:
        profile = service.update_monitoring_profile(profile_id, tenant_uuid, data)
        return jsonify(profile.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/supervisors/profiles/<int:profile_id>', methods=['DELETE'])
@require_token
def delete_monitoring_profile(profile_id):
    """Delete a monitoring profile."""
    tenant_uuid = get_token_tenant_uuid()
    service = SupervisorService(request.db_session)
    service.delete_monitoring_profile(profile_id, tenant_uuid)
    return '', 204

@bp.route('/supervisors/queues/<int:queue_id>/details', methods=['GET'])
@require_token
def get_queue_details(queue_id):
    """Get detailed queue statistics and information."""
    tenant_uuid = get_token_tenant_uuid()
    service = SupervisorService(request.db_session)
    try:
        details = service.get_queue_details(queue_id, tenant_uuid)
        return jsonify(details)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/supervisors/agents/<int:agent_id>/details', methods=['GET'])
@require_token
def get_agent_details(agent_id):
    """Get detailed agent statistics and information."""
    tenant_uuid = get_token_tenant_uuid()
    service = SupervisorService(request.db_session)
    try:
        details = service.get_agent_details(agent_id, tenant_uuid)
        return jsonify(details)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404
