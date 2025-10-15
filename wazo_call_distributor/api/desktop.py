"""Desktop API endpoints."""

from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.desktop import DesktopService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import AgentNotFound

bp = Blueprint('desktop', __name__)

class DesktopSettingsSchema(Schema):
    """Schema for desktop settings validation."""
    layout_config = fields.Dict()
    theme = fields.Str(validate=validate.OneOf(['light', 'dark']))
    notifications_enabled = fields.Bool()
    sound_enabled = fields.Bool()
    desktop_notifications = fields.Bool()
    show_queue_stats = fields.Bool()
    show_personal_kpis = fields.Bool()
    show_wrap_up_timer = fields.Bool()
    show_call_history = fields.Bool()
    default_wrap_up_time = fields.Int(validate=validate.Range(min=0))
    auto_wrap_up = fields.Bool()
    custom_settings = fields.Dict()

class WrapUpCodeSchema(Schema):
    """Schema for wrap-up code validation."""
    code = fields.Str(required=True, validate=validate.Length(min=1, max=32))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    category = fields.Str(validate=validate.Length(max=64))
    requires_comment = fields.Bool()
    requires_callback = fields.Bool()

class CallNoteSchema(Schema):
    """Schema for call note validation."""
    call_id = fields.Str(required=True)
    note = fields.Str(required=True, validate=validate.Length(min=1, max=1024))
    wrap_up_code_id = fields.Int()
    callback_requested = fields.Bool()
    callback_number = fields.Str(validate=validate.Length(max=32))
    callback_time = fields.Str(validate=validate.Length(max=32))

desktop_settings_schema = DesktopSettingsSchema()
wrap_up_code_schema = WrapUpCodeSchema()
call_note_schema = CallNoteSchema()

@bp.route('/agents/<int:agent_id>/desktop/settings', methods=['GET'])
@require_token
def get_agent_settings(agent_id):
    """Get agent desktop settings."""
    tenant_uuid = get_token_tenant_uuid()
    service = DesktopService(request.db_session)
    try:
        settings = service.get_agent_settings(agent_id, tenant_uuid)
        return jsonify(settings.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/agents/<int:agent_id>/desktop/settings', methods=['PUT'])
@require_token
def update_agent_settings(agent_id):
    """Update agent desktop settings."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = desktop_settings_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = DesktopService(request.db_session)
    try:
        settings = service.update_agent_settings(agent_id, tenant_uuid, data)
        return jsonify(settings.to_dict)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/wrap-up-codes', methods=['GET'])
@require_token
def list_wrap_up_codes():
    """List all wrap-up codes."""
    tenant_uuid = get_token_tenant_uuid()
    category = request.args.get('category')
    
    service = DesktopService(request.db_session)
    codes = service.get_wrap_up_codes(tenant_uuid, category)
    return jsonify([code.to_dict for code in codes])

@bp.route('/wrap-up-codes', methods=['POST'])
@require_token
def create_wrap_up_code():
    """Create a new wrap-up code."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = wrap_up_code_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = DesktopService(request.db_session)
    code = service.create_wrap_up_code(tenant_uuid, data)
    return jsonify(code.to_dict), 201

@bp.route('/wrap-up-codes/<int:code_id>', methods=['PUT'])
@require_token
def update_wrap_up_code(code_id):
    """Update an existing wrap-up code."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = wrap_up_code_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = DesktopService(request.db_session)
    try:
        code = service.update_wrap_up_code(code_id, tenant_uuid, data)
        return jsonify(code.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/wrap-up-codes/<int:code_id>', methods=['DELETE'])
@require_token
def delete_wrap_up_code(code_id):
    """Delete a wrap-up code."""
    tenant_uuid = get_token_tenant_uuid()
    service = DesktopService(request.db_session)
    service.delete_wrap_up_code(code_id, tenant_uuid)
    return '', 204

@bp.route('/agents/<int:agent_id>/calls/notes', methods=['POST'])
@require_token
def add_call_note(agent_id):
    """Add a note to a call."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = call_note_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = DesktopService(request.db_session)
    try:
        note = service.add_call_note(agent_id, tenant_uuid, data)
        return jsonify(note.to_dict), 201
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/calls/<call_id>/notes', methods=['GET'])
@require_token
def get_call_notes(call_id):
    """Get all notes for a call."""
    tenant_uuid = get_token_tenant_uuid()
    service = DesktopService(request.db_session)
    notes = service.get_call_notes(call_id, tenant_uuid)
    return jsonify([note.to_dict for note in notes])

@bp.route('/agents/<int:agent_id>/calls/history', methods=['GET'])
@require_token
def get_agent_call_history(agent_id):
    """Get call history for an agent."""
    tenant_uuid = get_token_tenant_uuid()
    limit = request.args.get('limit', 50, type=int)
    
    service = DesktopService(request.db_session)
    try:
        history = service.get_agent_call_history(agent_id, tenant_uuid, limit)
        return jsonify(history)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404

@bp.route('/calls/notes/<int:note_id>', methods=['PUT'])
@require_token
def update_call_note(note_id):
    """Update an existing call note."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = call_note_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = DesktopService(request.db_session)
    try:
        note = service.update_call_note(note_id, tenant_uuid, data)
        return jsonify(note.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/calls/notes/<int:note_id>', methods=['DELETE'])
@require_token
def delete_call_note(note_id):
    """Delete a call note."""
    tenant_uuid = get_token_tenant_uuid()
    service = DesktopService(request.db_session)
    service.delete_call_note(note_id, tenant_uuid)
    return '', 204

@bp.route('/agents/<int:agent_id>/kpis', methods=['GET'])
@require_token
def get_agent_kpis(agent_id):
    """Get personal KPIs for an agent."""
    tenant_uuid = get_token_tenant_uuid()
    service = DesktopService(request.db_session)
    try:
        kpis = service.get_agent_kpis(agent_id, tenant_uuid)
        return jsonify(kpis)
    except AgentNotFound:
        return {'message': f'Agent {agent_id} not found'}, 404
