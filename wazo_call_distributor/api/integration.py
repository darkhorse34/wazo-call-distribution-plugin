"""Integration API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.integration import IntegrationService
from ..auth import get_token_tenant_uuid, require_token

bp = Blueprint('integrations', __name__)

class IntegrationSchema(Schema):
    """Schema for integration validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    type = fields.Str(required=True, validate=validate.OneOf(['crm', 'helpdesk', 'analytics', 'custom']))
    provider = fields.Str(required=True, validate=validate.Length(min=1, max=64))
    auth_type = fields.Str(required=True, validate=validate.OneOf(['oauth2', 'api_key', 'basic']))
    auth_config = fields.Dict(required=True)
    enabled = fields.Bool()
    settings = fields.Dict()
    field_mappings = fields.Dict()

class WebhookSchema(Schema):
    """Schema for webhook validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    url = fields.Url(required=True, schemes=['http', 'https'])
    method = fields.Str(validate=validate.OneOf(['GET', 'POST', 'PUT', 'PATCH']))
    headers = fields.Dict()
    event_types = fields.List(fields.Str(), required=True)
    queue_ids = fields.List(fields.Int())
    agent_ids = fields.List(fields.Int())
    retry_enabled = fields.Bool()
    retry_max_attempts = fields.Int(validate=validate.Range(min=1))
    retry_interval = fields.Int(validate=validate.Range(min=1))
    secret_token = fields.Str(validate=validate.Length(max=128))
    ssl_verify = fields.Bool()
    enabled = fields.Bool()

integration_schema = IntegrationSchema()
webhook_schema = WebhookSchema()

@bp.route('/integrations', methods=['GET'])
@require_token
def list_integrations():
    """List all integrations."""
    tenant_uuid = get_token_tenant_uuid()
    integration_type = request.args.get('type')
    
    service = IntegrationService(request.db_session)
    integrations = service.list_integrations(tenant_uuid, integration_type)
    return jsonify([integration.to_dict for integration in integrations])

@bp.route('/integrations', methods=['POST'])
@require_token
def create_integration():
    """Create a new integration."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = integration_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = IntegrationService(request.db_session)
    integration = service.create_integration(tenant_uuid, data)
    return jsonify(integration.to_dict), 201

@bp.route('/integrations/<int:integration_id>', methods=['PUT'])
@require_token
def update_integration(integration_id):
    """Update an existing integration."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = integration_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = IntegrationService(request.db_session)
    try:
        integration = service.update_integration(integration_id, tenant_uuid, data)
        return jsonify(integration.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/integrations/<int:integration_id>', methods=['DELETE'])
@require_token
def delete_integration(integration_id):
    """Delete an integration."""
    tenant_uuid = get_token_tenant_uuid()
    service = IntegrationService(request.db_session)
    try:
        service.delete_integration(integration_id, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/webhooks', methods=['GET'])
@require_token
def list_webhooks():
    """List all webhooks."""
    tenant_uuid = get_token_tenant_uuid()
    service = IntegrationService(request.db_session)
    webhooks = service.list_webhooks(tenant_uuid)
    return jsonify([webhook.to_dict for webhook in webhooks])

@bp.route('/webhooks', methods=['POST'])
@require_token
def create_webhook():
    """Create a new webhook."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = webhook_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = IntegrationService(request.db_session)
    webhook = service.create_webhook(tenant_uuid, data)
    return jsonify(webhook.to_dict), 201

@bp.route('/webhooks/<int:webhook_id>', methods=['PUT'])
@require_token
def update_webhook(webhook_id):
    """Update an existing webhook."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = webhook_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = IntegrationService(request.db_session)
    try:
        webhook = service.update_webhook(webhook_id, tenant_uuid, data)
        return jsonify(webhook.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/webhooks/<int:webhook_id>', methods=['DELETE'])
@require_token
def delete_webhook(webhook_id):
    """Delete a webhook."""
    tenant_uuid = get_token_tenant_uuid()
    service = IntegrationService(request.db_session)
    try:
        service.delete_webhook(webhook_id, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/webhooks/<int:webhook_id>/deliveries', methods=['GET'])
@require_token
def get_webhook_deliveries(webhook_id):
    """Get delivery history for a webhook."""
    tenant_uuid = get_token_tenant_uuid()
    service = IntegrationService(request.db_session)
    try:
        deliveries = service.get_webhook_deliveries(webhook_id, tenant_uuid)
        return jsonify([delivery.to_dict for delivery in deliveries])
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/webhooks/<int:webhook_id>/trigger', methods=['POST'])
@require_token
def trigger_webhook(webhook_id):
    """Manually trigger a webhook."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    if 'event_type' not in data or 'event_data' not in data:
        return {'message': 'event_type and event_data are required'}, 400
    
    service = IntegrationService(request.db_session)
    try:
        delivery = service.trigger_webhook(
            webhook_id,
            tenant_uuid,
            data['event_type'],
            data['event_data']
        )
        
        if not delivery:
            return {'message': 'Webhook not triggered (disabled or filtered)'}, 400
        
        return jsonify(delivery.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/webhooks/deliveries/<int:delivery_id>/retry', methods=['POST'])
@require_token
def retry_webhook(delivery_id):
    """Retry a failed webhook delivery."""
    service = IntegrationService(request.db_session)
    delivery = service.retry_webhook(delivery_id)
    
    if not delivery:
        return {'message': 'Delivery not found or not eligible for retry'}, 404
    
    return jsonify(delivery.to_dict)

@bp.route('/webhooks/process-retries', methods=['POST'])
@require_token
def process_pending_retries():
    """Process pending webhook retries."""
    service = IntegrationService(request.db_session)
    retry_count = service.process_pending_retries()
    return jsonify({'retries_processed': retry_count})
