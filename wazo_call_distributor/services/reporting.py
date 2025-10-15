"""Reporting service for analytics and data aggregation."""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from ..models import (
    Report, QueueStats, AgentStats, CallStats,
    Queue, Agent, QueueMetrics, AgentMetrics
)
from ..exceptions import QueueNotFound, AgentNotFound

class ReportingService:
    """Service for managing reports and analytics."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_report(self, report_id: int, tenant_uuid: str) -> Report:
        """Get a report by ID."""
        report = self.session.query(Report).filter(
            Report.id == report_id,
            Report.tenant_uuid == tenant_uuid
        ).first()
        
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        return report
    
    def list_reports(self, tenant_uuid: str,
                    report_type: Optional[str] = None) -> List[Report]:
        """List all reports for a tenant."""
        query = self.session.query(Report).filter(
            Report.tenant_uuid == tenant_uuid
        )
        
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        return query.all()
    
    def create_report(self, tenant_uuid: str, report_data: Dict) -> Report:
        """Create a new report."""
        report = Report(tenant_uuid=tenant_uuid, **report_data)
        self.session.add(report)
        self.session.commit()
        return report
    
    def update_report(self, report_id: int, tenant_uuid: str,
                     report_data: Dict) -> Report:
        """Update an existing report."""
        report = self.get_report(report_id, tenant_uuid)
        
        for key, value in report_data.items():
            setattr(report, key, value)
        
        self.session.commit()
        return report
    
    def delete_report(self, report_id: int, tenant_uuid: str) -> None:
        """Delete a report."""
        report = self.get_report(report_id, tenant_uuid)
        self.session.delete(report)
        self.session.commit()
    
    def generate_report(self, report_id: int, tenant_uuid: str,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> Dict:
        """Generate a report based on configuration."""
        report = self.get_report(report_id, tenant_uuid)
        
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=1)
        if not end_time:
            end_time = datetime.utcnow()
        
        if report.report_type == 'queue':
            data = self.get_queue_report(
                tenant_uuid,
                report.config,
                start_time,
                end_time
            )
        elif report.report_type == 'agent':
            data = self.get_agent_report(
                tenant_uuid,
                report.config,
                start_time,
                end_time
            )
        elif report.report_type == 'call':
            data = self.get_call_report(
                tenant_uuid,
                report.config,
                start_time,
                end_time
            )
        else:
            raise ValueError(f"Unsupported report type: {report.report_type}")
        
        # Update report status
        report.last_run = datetime.utcnow()
        report.last_status = 'completed'
        self.session.commit()
        
        return data
    
    def get_queue_report(self, tenant_uuid: str, config: Dict,
                        start_time: datetime, end_time: datetime) -> Dict:
        """Generate queue statistics report."""
        queue_ids = config.get('queue_ids')
        interval = config.get('interval', '1hour')
        metrics = config.get('metrics', [])
        
        query = self.session.query(QueueStats).filter(
            QueueStats.tenant_uuid == tenant_uuid,
            QueueStats.timestamp.between(start_time, end_time),
            QueueStats.interval == interval
        )
        
        if queue_ids:
            query = query.filter(QueueStats.queue_id.in_(queue_ids))
        
        stats = query.all()
        
        # Group stats by queue
        result = {}
        for stat in stats:
            if stat.queue_id not in result:
                result[stat.queue_id] = {
                    'queue_id': stat.queue_id,
                    'queue_name': stat.queue.name,
                    'data': []
                }
            
            # Filter metrics if specified
            stat_data = stat.to_dict
            if metrics:
                stat_data = {k: v for k, v in stat_data.items() if k in metrics}
            
            result[stat.queue_id]['data'].append(stat_data)
        
        return list(result.values())
    
    def get_agent_report(self, tenant_uuid: str, config: Dict,
                        start_time: datetime, end_time: datetime) -> Dict:
        """Generate agent statistics report."""
        agent_ids = config.get('agent_ids')
        interval = config.get('interval', '1hour')
        metrics = config.get('metrics', [])
        
        query = self.session.query(AgentStats).filter(
            AgentStats.tenant_uuid == tenant_uuid,
            AgentStats.timestamp.between(start_time, end_time),
            AgentStats.interval == interval
        )
        
        if agent_ids:
            query = query.filter(AgentStats.agent_id.in_(agent_ids))
        
        stats = query.all()
        
        # Group stats by agent
        result = {}
        for stat in stats:
            if stat.agent_id not in result:
                result[stat.agent_id] = {
                    'agent_id': stat.agent_id,
                    'agent_name': stat.agent.name,
                    'data': []
                }
            
            # Filter metrics if specified
            stat_data = stat.to_dict
            if metrics:
                stat_data = {k: v for k, v in stat_data.items() if k in metrics}
            
            result[stat.agent_id]['data'].append(stat_data)
        
        return list(result.values())
    
    def get_call_report(self, tenant_uuid: str, config: Dict,
                       start_time: datetime, end_time: datetime) -> Dict:
        """Generate call statistics report."""
        queue_ids = config.get('queue_ids')
        agent_ids = config.get('agent_ids')
        dispositions = config.get('dispositions')
        include_tags = config.get('include_tags', False)
        include_custom_data = config.get('include_custom_data', False)
        
        query = self.session.query(CallStats).filter(
            CallStats.tenant_uuid == tenant_uuid,
            CallStats.timestamp.between(start_time, end_time)
        )
        
        if queue_ids:
            query = query.filter(CallStats.queue_id.in_(queue_ids))
        if agent_ids:
            query = query.filter(CallStats.agent_id.in_(agent_ids))
        if dispositions:
            query = query.filter(CallStats.disposition.in_(dispositions))
        
        stats = query.all()
        result = []
        
        for stat in stats:
            stat_data = stat.to_dict
            
            # Remove tags and custom data if not requested
            if not include_tags:
                del stat_data['tags']
            if not include_custom_data:
                del stat_data['custom_data']
            
            result.append(stat_data)
        
        return result
    
    def aggregate_queue_stats(self, tenant_uuid: str,
                            interval: str = '1hour') -> None:
        """Aggregate queue metrics into statistics."""
        now = datetime.utcnow()
        
        if interval == '1hour':
            start_time = now - timedelta(hours=1)
            truncate = func.date_trunc('hour', QueueMetrics.timestamp)
        elif interval == '1day':
            start_time = now - timedelta(days=1)
            truncate = func.date_trunc('day', QueueMetrics.timestamp)
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        # Get all queues
        queues = self.session.query(Queue).filter(
            Queue.tenant_uuid == tenant_uuid
        ).all()
        
        for queue in queues:
            # Aggregate metrics
            metrics = self.session.query(
                func.count().label('total_calls'),
                func.sum(QueueMetrics.answered_calls).label('answered_calls'),
                func.sum(QueueMetrics.abandoned_calls).label('abandoned_calls'),
                func.avg(QueueMetrics.average_wait).label('average_wait_time'),
                func.avg(QueueMetrics.average_talk).label('average_talk_time'),
                func.max(QueueMetrics.longest_wait).label('max_wait_time'),
                func.avg(QueueMetrics.service_level).label('service_level_ratio')
            ).filter(
                QueueMetrics.queue_id == queue.id,
                QueueMetrics.tenant_uuid == tenant_uuid,
                QueueMetrics.timestamp >= start_time
            ).group_by(
                truncate
            ).all()
            
            # Create stats records
            for metric in metrics:
                stats = QueueStats(
                    tenant_uuid=tenant_uuid,
                    queue_id=queue.id,
                    interval=interval,
                    total_calls=metric.total_calls,
                    answered_calls=metric.answered_calls,
                    abandoned_calls=metric.abandoned_calls,
                    average_wait_time=metric.average_wait_time,
                    average_talk_time=metric.average_talk_time,
                    max_wait_time=metric.max_wait_time,
                    service_level_ratio=metric.service_level_ratio
                )
                self.session.add(stats)
        
        self.session.commit()
    
    def aggregate_agent_stats(self, tenant_uuid: str,
                            interval: str = '1hour') -> None:
        """Aggregate agent metrics into statistics."""
        now = datetime.utcnow()
        
        if interval == '1hour':
            start_time = now - timedelta(hours=1)
            truncate = func.date_trunc('hour', AgentMetrics.timestamp)
        elif interval == '1day':
            start_time = now - timedelta(days=1)
            truncate = func.date_trunc('day', AgentMetrics.timestamp)
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        # Get all agents
        agents = self.session.query(Agent).filter(
            Agent.tenant_uuid == tenant_uuid
        ).all()
        
        for agent in agents:
            # Aggregate metrics
            metrics = self.session.query(
                func.count().label('total_calls'),
                func.sum(AgentMetrics.calls_taken).label('answered_calls'),
                func.avg(AgentMetrics.average_talk_time).label('average_talk_time'),
                func.avg(AgentMetrics.average_wrap_time).label('average_wrap_up_time'),
                func.avg(AgentMetrics.occupancy_rate).label('occupancy_rate')
            ).filter(
                AgentMetrics.agent_id == agent.id,
                AgentMetrics.tenant_uuid == tenant_uuid,
                AgentMetrics.timestamp >= start_time
            ).group_by(
                truncate
            ).all()
            
            # Create stats records
            for metric in metrics:
                stats = AgentStats(
                    tenant_uuid=tenant_uuid,
                    agent_id=agent.id,
                    interval=interval,
                    total_calls=metric.total_calls,
                    answered_calls=metric.answered_calls,
                    average_talk_time=metric.average_talk_time,
                    average_wrap_up_time=metric.average_wrap_up_time,
                    occupancy_rate=metric.occupancy_rate
                )
                self.session.add(stats)
        
        self.session.commit()
    
    def record_call_stats(self, tenant_uuid: str, call_data: Dict) -> CallStats:
        """Record statistics for a completed call."""
        stats = CallStats(tenant_uuid=tenant_uuid, **call_data)
        self.session.add(stats)
        self.session.commit()
        return stats
