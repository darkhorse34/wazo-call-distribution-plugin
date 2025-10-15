"""Reporting API endpoints."""

from datetime import datetime
from flask import request, jsonify, Blueprint
from marshmallow import Schema, fields, validate
from ..services.reporting import ReportingService
from ..auth import get_token_tenant_uuid, require_token

bp = Blueprint('reporting', __name__)

class ReportSchema(Schema):
    """Schema for report validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=256))
    report_type = fields.Str(required=True, validate=validate.OneOf(['queue', 'agent', 'call']))
    config = fields.Dict(required=True)
    schedule_enabled = fields.Bool()
    schedule_interval = fields.Str(validate=validate.OneOf(['daily', 'weekly', 'monthly']))
    schedule_time = fields.Str(validate=validate.Regexp(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'))
    schedule_day = fields.Int()
    export_format = fields.Str(validate=validate.OneOf(['csv', 'json', 'xlsx']))
    export_recipients = fields.List(fields.Email())

class DateRangeSchema(Schema):
    """Schema for date range validation."""
    start_time = fields.DateTime()
    end_time = fields.DateTime()

class CallStatsSchema(Schema):
    """Schema for call statistics validation."""
    call_id = fields.Str(required=True)
    queue_id = fields.Int()
    agent_id = fields.Int()
    caller_id = fields.Str()
    direction = fields.Str(validate=validate.OneOf(['inbound', 'outbound']))
    timestamp = fields.DateTime(required=True)
    queue_wait_time = fields.Int()
    position_on_entry = fields.Int()
    attempts = fields.Int()
    disposition = fields.Str()
    disconnect_reason = fields.Str()
    talk_time = fields.Int()
    wrap_up_time = fields.Int()
    satisfaction_score = fields.Int(validate=validate.Range(min=1, max=5))
    recording_url = fields.Str()
    tags = fields.List(fields.Str())
    custom_data = fields.Dict()

report_schema = ReportSchema()
date_range_schema = DateRangeSchema()
call_stats_schema = CallStatsSchema()

@bp.route('/reports', methods=['GET'])
@require_token
def list_reports():
    """List all reports."""
    tenant_uuid = get_token_tenant_uuid()
    report_type = request.args.get('type')
    
    service = ReportingService(request.db_session)
    reports = service.list_reports(tenant_uuid, report_type)
    return jsonify([report.to_dict for report in reports])

@bp.route('/reports', methods=['POST'])
@require_token
def create_report():
    """Create a new report."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = report_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReportingService(request.db_session)
    report = service.create_report(tenant_uuid, data)
    return jsonify(report.to_dict), 201

@bp.route('/reports/<int:report_id>', methods=['PUT'])
@require_token
def update_report(report_id):
    """Update an existing report."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = report_schema.validate(data, partial=True)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReportingService(request.db_session)
    try:
        report = service.update_report(report_id, tenant_uuid, data)
        return jsonify(report.to_dict)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/reports/<int:report_id>', methods=['DELETE'])
@require_token
def delete_report(report_id):
    """Delete a report."""
    tenant_uuid = get_token_tenant_uuid()
    service = ReportingService(request.db_session)
    try:
        service.delete_report(report_id, tenant_uuid)
        return '', 204
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/reports/<int:report_id>/generate', methods=['POST'])
@require_token
def generate_report(report_id):
    """Generate a report."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json() or {}
    
    errors = date_range_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReportingService(request.db_session)
    try:
        start_time = datetime.fromisoformat(data['start_time']) if 'start_time' in data else None
        end_time = datetime.fromisoformat(data['end_time']) if 'end_time' in data else None
        
        report_data = service.generate_report(report_id, tenant_uuid, start_time, end_time)
        return jsonify(report_data)
    except ValueError as e:
        return {'message': str(e)}, 404

@bp.route('/stats/queue/aggregate', methods=['POST'])
@require_token
def aggregate_queue_stats():
    """Aggregate queue statistics."""
    tenant_uuid = get_token_tenant_uuid()
    interval = request.args.get('interval', '1hour')
    
    if interval not in ['1hour', '1day']:
        return {'message': "Invalid interval. Must be '1hour' or '1day'"}, 400
    
    service = ReportingService(request.db_session)
    service.aggregate_queue_stats(tenant_uuid, interval)
    return '', 204

@bp.route('/stats/agent/aggregate', methods=['POST'])
@require_token
def aggregate_agent_stats():
    """Aggregate agent statistics."""
    tenant_uuid = get_token_tenant_uuid()
    interval = request.args.get('interval', '1hour')
    
    if interval not in ['1hour', '1day']:
        return {'message': "Invalid interval. Must be '1hour' or '1day'"}, 400
    
    service = ReportingService(request.db_session)
    service.aggregate_agent_stats(tenant_uuid, interval)
    return '', 204

@bp.route('/stats/call', methods=['POST'])
@require_token
def record_call_stats():
    """Record call statistics."""
    tenant_uuid = get_token_tenant_uuid()
    data = request.get_json()
    
    errors = call_stats_schema.validate(data)
    if errors:
        return {'message': 'Validation error', 'errors': errors}, 400
    
    service = ReportingService(request.db_session)
    stats = service.record_call_stats(tenant_uuid, data)
    return jsonify(stats.to_dict), 201
