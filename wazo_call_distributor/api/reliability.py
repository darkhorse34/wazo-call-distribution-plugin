"""Reliability API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.reliability import ReliabilityService
from ..auth import get_token_tenant_uuid, require_token

bp = Blueprint('reliability', __name__)

class RateLimitSchema(Schema):
    """Schema for rate limit validation."""
    endpoint = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    method = fields.Str(validate=validate.OneOf(['GET', 'POST', 'PUT', 'DELETE']))
    requests_per_second = fields.Int(required=True, validate=validate.Range(min=1))
    burst_size = fields.Int(validate=validate.Range(min=1))
    enabled = fields.Bool()
    custom_settings = fields.Dict()

class BackupConfigSchema(Schema):
    """Schema for backup configuration validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    enabled = fields.Bool()
    schedule_interval = fields.Str(validate=validate.OneOf(['daily', 'weekly', 'monthly']))
    schedule_time = fields.Str(validate=validate.Regexp(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'))
    schedule_day = fields.Int()
    storage_type = fields.Str(required=True)
    storage_config = fields.Dict(required=True)
    retention_days = fields.Int(validate=validate.Range(min=1))
    max_backups = fields.Int(validate=validate.Range(min=1))

class FailoverConfigSchema(Schema):
    """Schema for failover configuration validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    enabled = fields.Bool()
    queue_id = fields.Int(required=True)
    max_queue_size = fields.Int(validate=validate.Range(min=1))
    max_wait_time = fields.Int(validate=validate.Range(min=1))
    service_level_threshold = fields.Int(validate=validate.Range(min=1, max=100))
    agent_availability_threshold = fields.Int(validate=validate.Range(min=1))
    failover_type = fields.Str(required=True, validate=validate.OneOf(['queue', 'ivr', 'voicemail']))
    failover_destination = fields.Str(required=True)
    auto_recovery = fields.Bool()
    recovery_threshold = fields.Int(validate=validate.Range(min=1))

rate_limit_schema = RateLimitSchema()
backup_config_schema = BackupConfigSchema()
failover_config_schema = FailoverConfigSchema()

@bp.route('/health', methods=['GET'])
@require_token
def list_service_health():
    """List health status for all services."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    health_checks = service.list_service_health(tenant_uuid)
    return jsonify([check.to_dict for check in health_checks])

@bp.route('/health/<service_name>', methods=['GET'])
@require_token
def get_service_health(service_name):
    """Get health status for a service."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    try:
        health = service.get_service_health(service_name, tenant_uuid)
        return jsonify(health.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/health/<service_name>/check', methods=['POST'])
@require_token
def check_service_health(service_name):
    """Perform health check for a service."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    try:
        health = service.check_service_health(service_name, tenant_uuid)
        return jsonify(health.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/rate-limits', methods=['GET'])
@require_token
def list_rate_limits():
    """List all rate limit configurations."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    limits = service.list_rate_limits(tenant_uuid)
    return jsonify([limit.to_dict for limit in limits])

@bp.route('/rate-limits', methods=['POST'])
@require_token
def create_rate_limit():
    """Create a new rate limit configuration."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = rate_limit_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReliabilityService(request.db_session)
    limit = service.create_rate_limit(tenant_uuid, data)
    return jsonify(limit.to_dict), 201

@bp.route('/rate-limits/<path:endpoint>', methods=['PUT'])
@require_token
def update_rate_limit(endpoint):
    """Update a rate limit configuration."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = rate_limit_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReliabilityService(request.db_session)
    try:
        limit = service.update_rate_limit(endpoint, tenant_uuid, data)
        return jsonify(limit.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/rate-limits/<path:endpoint>', methods=['DELETE'])
@require_token
def delete_rate_limit(endpoint):
    """Delete a rate limit configuration."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    try:
        service.delete_rate_limit(endpoint, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/backups', methods=['GET'])
@require_token
def list_backup_configs():
    """List all backup configurations."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    configs = service.list_backup_configs(tenant_uuid)
    return jsonify([config.to_dict for config in configs])

@bp.route('/backups', methods=['POST'])
@require_token
def create_backup_config():
    """Create a new backup configuration."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = backup_config_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReliabilityService(request.db_session)
    config = service.create_backup_config(tenant_uuid, data)
    return jsonify(config.to_dict), 201

@bp.route('/backups/<int:config_id>', methods=['PUT'])
@require_token
def update_backup_config(config_id):
    """Update a backup configuration."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = backup_config_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReliabilityService(request.db_session)
    try:
        config = service.update_backup_config(config_id, tenant_uuid, data)
        return jsonify(config.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/backups/<int:config_id>', methods=['DELETE'])
@require_token
def delete_backup_config(config_id):
    """Delete a backup configuration."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    try:
        service.delete_backup_config(config_id, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/failovers', methods=['GET'])
@require_token
def list_failover_configs():
    """List all failover configurations."""
    tenant_uuid = get_token_tenant_uuid()
    queue_id = request.args.get('queue_id', type=int)
    
    service = ReliabilityService(request.db_session)
    configs = service.list_failover_configs(tenant_uuid, queue_id)
    return jsonify([config.to_dict for config in configs])

@bp.route('/failovers', methods=['POST'])
@require_token
def create_failover_config():
    """Create a new failover configuration."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = failover_config_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReliabilityService(request.db_session)
    config = service.create_failover_config(tenant_uuid, data)
    return jsonify(config.to_dict), 201

@bp.route('/failovers/<int:config_id>', methods=['PUT'])
@require_token
def update_failover_config(config_id):
    """Update a failover configuration."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = failover_config_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReliabilityService(request.db_session)
    try:
        config = service.update_failover_config(config_id, tenant_uuid, data)
        return jsonify(config.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/failovers/<int:config_id>', methods=['DELETE'])
@require_token
def delete_failover_config(config_id):
    """Delete a failover configuration."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    try:
        service.delete_failover_config(config_id, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/failovers/check/<int:queue_id>', methods=['GET'])
@require_token
def check_failover_conditions(queue_id):
    """Check failover conditions for a queue."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    triggered = service.check_failover_conditions(queue_id, tenant_uuid)
    
    return jsonify([{
        'config': config.to_dict,
        'reason': reason
    } for config, reason in triggered])

@bp.route('/failovers/<int:config_id>/activate', methods=['POST'])
@require_token
def activate_failover(config_id):
    """Activate failover for a configuration."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    try:
        config = service.activate_failover(config_id, tenant_uuid)
        return jsonify(config.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 400

@bp.route('/failovers/<int:config_id>/deactivate', methods=['POST'])
@require_token
def deactivate_failover(config_id):
    """Deactivate failover for a configuration."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReliabilityService(request.db_session)
    try:
        config = service.deactivate_failover(config_id, tenant_uuid)
        return jsonify(config.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404
