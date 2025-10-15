"""Call control API endpoints."""

from flask import request, jsonify, Blueprint, current_app
from marshmallow import Schema, fields, validate
from wazo_calld_client import Client as CalldClient
from ..services.call_control import CallControlService
from ..auth import require_token
from ..exceptions import ServiceUnavailable

bp = Blueprint('call_control', __name__)

class TransferSchema(Schema):
    """Schema for call transfer validation."""
    destination = fields.Str(required=True)
    flow = fields.Str(validate=validate.OneOf(['blind', 'attended']), default='blind')

class WhisperBargeSchema(Schema):
    """Schema for whisper/barge validation."""
    supervisor_id = fields.Str(required=True)

class SoundSchema(Schema):
    """Schema for sound playback validation."""
    sound_file = fields.Str(required=True)

class DtmfSchema(Schema):
    """Schema for DTMF validation."""
    digits = fields.Str(required=True, validate=validate.Regexp(r'^[0-9*#]+$'))

transfer_schema = TransferSchema()
whisper_barge_schema = WhisperBargeSchema()
sound_schema = SoundSchema()
dtmf_schema = DtmfSchema()

def get_call_control_service():
    """Get or create a call control service."""
    calld_client = CalldClient(**current_app.config['calld'])
    return CallControlService(calld_client)

@bp.route('/calls/<call_id>/transfer', methods=['POST'])
@require_token
def transfer_call(call_id):
    """Transfer a call to another destination."""
    data = request.get_json()
    
    errors = transfer_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_call_control_service()
    try:
        result = service.transfer_call(call_id, data['destination'], data.get('flow', 'blind'))
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/hold', methods=['PUT'])
@require_token
def hold_call(call_id):
    """Put a call on hold."""
    service = get_call_control_service()
    try:
        result = service.hold_call(call_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/resume', methods=['PUT'])
@require_token
def resume_call(call_id):
    """Resume a held call."""
    service = get_call_control_service()
    try:
        result = service.resume_call(call_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/mute', methods=['PUT'])
@require_token
def mute_call(call_id):
    """Mute a call."""
    service = get_call_control_service()
    try:
        result = service.mute_call(call_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/unmute', methods=['PUT'])
@require_token
def unmute_call(call_id):
    """Unmute a call."""
    service = get_call_control_service()
    try:
        result = service.unmute_call(call_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/record/start', methods=['POST'])
@require_token
def start_recording(call_id):
    """Start recording a call."""
    service = get_call_control_service()
    try:
        result = service.start_recording(call_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/record/stop', methods=['POST'])
@require_token
def stop_recording(call_id):
    """Stop recording a call."""
    service = get_call_control_service()
    try:
        result = service.stop_recording(call_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/whisper', methods=['POST'])
@require_token
def start_whisper(call_id):
    """Start whisper coaching on a call."""
    data = request.get_json()
    
    errors = whisper_barge_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_call_control_service()
    try:
        result = service.whisper(call_id, data['supervisor_id'])
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/whisper/stop', methods=['POST'])
@require_token
def stop_whisper(call_id):
    """Stop whisper coaching on a call."""
    data = request.get_json()
    
    errors = whisper_barge_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_call_control_service()
    try:
        result = service.stop_whisper(call_id, data['supervisor_id'])
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/barge', methods=['POST'])
@require_token
def start_barge(call_id):
    """Barge into a call."""
    data = request.get_json()
    
    errors = whisper_barge_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_call_control_service()
    try:
        result = service.barge(call_id, data['supervisor_id'])
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/barge/stop', methods=['POST'])
@require_token
def stop_barge(call_id):
    """Stop barging into a call."""
    data = request.get_json()
    
    errors = whisper_barge_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_call_control_service()
    try:
        result = service.stop_barge(call_id, data['supervisor_id'])
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/pickup/<interceptor_id>', methods=['POST'])
@require_token
def pickup_call(call_id, interceptor_id):
    """Pick up a ringing call."""
    service = get_call_control_service()
    try:
        result = service.pickup_call(call_id, interceptor_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>', methods=['GET'])
@require_token
def get_call_status(call_id):
    """Get current status of a call."""
    service = get_call_control_service()
    try:
        result = service.get_call_status(call_id)
        if not result:
            return {'message': 'Call not found'}, 404
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls', methods=['GET'])
@require_token
def list_active_calls():
    """List all active calls."""
    service = get_call_control_service()
    try:
        result = service.list_active_calls()
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>', methods=['DELETE'])
@require_token
def hangup_call(call_id):
    """Hang up a call."""
    service = get_call_control_service()
    try:
        service.hangup_call(call_id)
        return '', 204
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/play', methods=['POST'])
@require_token
def play_sound(call_id):
    """Play a sound file on a call."""
    data = request.get_json()
    
    errors = sound_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_call_control_service()
    try:
        result = service.play_sound(call_id, data['sound_file'])
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/play/stop', methods=['POST'])
@require_token
def stop_sound(call_id):
    """Stop playing sound on a call."""
    service = get_call_control_service()
    try:
        result = service.stop_sound(call_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/dtmf', methods=['POST'])
@require_token
def send_dtmf(call_id):
    """Send DTMF digits on a call."""
    data = request.get_json()
    
    errors = dtmf_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = get_call_control_service()
    try:
        result = service.send_dtmf(call_id, data['digits'])
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/answer', methods=['POST'])
@require_token
def answer_call(call_id):
    """Answer a ringing call."""
    service = get_call_control_service()
    try:
        result = service.answer_call(call_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/calls/<call_id>/reject', methods=['POST'])
@require_token
def reject_call(call_id):
    """Reject a ringing call."""
    service = get_call_control_service()
    try:
        result = service.reject_call(call_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/transfers/<transfer_id>/cancel', methods=['POST'])
@require_token
def cancel_transfer(transfer_id):
    """Cancel an ongoing transfer."""
    service = get_call_control_service()
    try:
        service.cancel_transfer(transfer_id)
        return '', 204
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503

@bp.route('/transfers/<transfer_id>/complete', methods=['POST'])
@require_token
def complete_transfer(transfer_id):
    """Complete an attended transfer."""
    service = get_call_control_service()
    try:
        result = service.complete_transfer(transfer_id)
        return jsonify(result)
    except ServiceUnavailable as e:
        return {'message': str(e)}, 503
