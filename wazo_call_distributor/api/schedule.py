"""Schedule API endpoints."""

from datetime import datetime
from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from ..services.schedule import ScheduleService
from ..auth import get_token_tenant_uuid, require_token
from ..exceptions import ScheduleNotFound

bp = Blueprint('schedules', __name__)

class TimeRangeSchema(Schema):
    """Schema for time range validation."""
    day_start = fields.Int(required=True, validate=validate.Range(min=0, max=6))
    day_end = fields.Int(required=True, validate=validate.Range(min=0, max=6))
    time_start = fields.Str(required=True, validate=validate.Regexp(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'))
    time_end = fields.Str(required=True, validate=validate.Regexp(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'))
    
    @validates_schema
    def validate_days(self, data, **kwargs):
        """Validate day range."""
        if data['day_start'] > data['day_end']:
            raise ValidationError('day_start must be less than or equal to day_end')

class HolidaySchema(Schema):
    """Schema for holiday validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    date = fields.Date(required=True)
    recurring = fields.Bool()
    time_start = fields.Str(validate=validate.Regexp(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'))
    time_end = fields.Str(validate=validate.Regexp(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'))
    
    @validates_schema
    def validate_times(self, data, **kwargs):
        """Validate time range if provided."""
        if ('time_start' in data and 'time_end' not in data) or \
           ('time_end' in data and 'time_start' not in data):
            raise ValidationError('Both time_start and time_end must be provided if one is specified')

class ScheduleSchema(Schema):
    """Schema for schedule validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    fallback_type = fields.Str(validate=validate.OneOf(['voicemail', 'ivr', 'queue']))
    fallback_destination = fields.Str(validate=validate.Length(max=128))
    time_ranges = fields.Nested(TimeRangeSchema, many=True)
    holidays = fields.Nested(HolidaySchema, many=True)

schedule_schema = ScheduleSchema()

@bp.route('/schedules', methods=['GET'])
@require_token
def list_schedules():
    """List all schedules for the tenant."""
    tenant_uuid = get_token_tenant_uuid()
    service = ScheduleService(request.db_session)
    schedules = service.list(tenant_uuid)
    return jsonify([schedule.to_dict for schedule in schedules])

@bp.route('/schedules/<int:schedule_id>', methods=['GET'])
@require_token
def get_schedule(schedule_id):
    """Get a specific schedule."""
    tenant_uuid = get_token_tenant_uuid()
    service = ScheduleService(request.db_session)
    try:
        schedule = service.get(schedule_id, tenant_uuid)
        return jsonify(schedule.to_dict)
    except ScheduleNotFound:
        return {'message': f'Schedule {schedule_id} not found'}, 404

@bp.route('/schedules', methods=['POST'])
@require_token
def create_schedule():
    """Create a new schedule."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = schedule_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ScheduleService(request.db_session)
    schedule = service.create(tenant_uuid, data)
    return jsonify(schedule.to_dict), 201

@bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
@require_token
def update_schedule(schedule_id):
    """Update an existing schedule."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = schedule_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ScheduleService(request.db_session)
    try:
        schedule = service.update(schedule_id, tenant_uuid, data)
        return jsonify(schedule.to_dict)
    except ScheduleNotFound:
        return {'message': f'Schedule {schedule_id} not found'}, 404

@bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@require_token
def delete_schedule(schedule_id):
    """Delete a schedule."""
    tenant_uuid = get_token_tenant_uuid()
    service = ScheduleService(request.db_session)
    try:
        service.delete(schedule_id, tenant_uuid)
        return '', 204
    except ScheduleNotFound:
        return {'message': f'Schedule {schedule_id} not found'}, 404

@bp.route('/schedules/<int:schedule_id>/status', methods=['GET'])
@require_token
def check_schedule_status(schedule_id):
    """Check if schedule is currently open."""
    tenant_uuid = get_token_tenant_uuid()
    check_time = request.args.get('check_time')
    
    if check_time:
        try:
            check_time = datetime.fromisoformat(check_time)
        except ValueError:
            return {'message': 'Invalid check_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}, 400
    
    service = ScheduleService(request.db_session)
    try:
        is_open, fallback = service.check_schedule_status(schedule_id, tenant_uuid, check_time)
        return jsonify({
            'is_open': is_open,
            'fallback_destination': fallback
        })
    except ScheduleNotFound:
        return {'message': f'Schedule {schedule_id} not found'}, 404
