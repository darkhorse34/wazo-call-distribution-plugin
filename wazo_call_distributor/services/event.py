"""Event service for handling metrics and monitoring."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import redis
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Event, QueueMetrics, AgentMetrics, Queue, Agent
from ..exceptions import QueueNotFound, AgentNotFound

class EventService:
    """Service for handling events and metrics."""
    
    def __init__(self, session: Session, redis_client: redis.Redis):
        self.session = session
        self.redis = redis_client
    
    def record_event(self, tenant_uuid: str, event_type: str,
                    event_name: str, data: Dict) -> Event:
        """Record a new event."""
        event = Event(
            tenant_uuid=tenant_uuid,
            event_type=event_type,
            event_name=event_name,
            queue_id=data.get('queue_id'),
            agent_id=data.get('agent_id'),
            call_id=data.get('call_id'),
            data=data
        )
        
        self.session.add(event)
        self.session.commit()
        
        # Update real-time metrics
        if event_type == 'call':
            self._update_call_metrics(event)
        elif event_type == 'agent':
            self._update_agent_metrics(event)
        
        # Publish event to Redis for WebSocket subscribers
        self._publish_event(event)
        
        return event
    
    def get_queue_metrics(self, queue_id: int, tenant_uuid: str,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[QueueMetrics]:
        """Get queue metrics for a time range."""
        query = self.session.query(QueueMetrics).filter(
            QueueMetrics.queue_id == queue_id,
            QueueMetrics.tenant_uuid == tenant_uuid
        )
        
        if start_time:
            query = query.filter(QueueMetrics.timestamp >= start_time)
        if end_time:
            query = query.filter(QueueMetrics.timestamp <= end_time)
        
        return query.order_by(QueueMetrics.timestamp.desc()).all()
    
    def get_agent_metrics(self, agent_id: int, tenant_uuid: str,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[AgentMetrics]:
        """Get agent metrics for a time range."""
        query = self.session.query(AgentMetrics).filter(
            AgentMetrics.agent_id == agent_id,
            AgentMetrics.tenant_uuid == tenant_uuid
        )
        
        if start_time:
            query = query.filter(AgentMetrics.timestamp >= start_time)
        if end_time:
            query = query.filter(AgentMetrics.timestamp <= end_time)
        
        return query.order_by(AgentMetrics.timestamp.desc()).all()
    
    def get_realtime_queue_metrics(self, queue_id: int, tenant_uuid: str) -> Dict:
        """Get real-time metrics for a queue."""
        metrics = self.redis.hgetall(f"queue_metrics:{queue_id}")
        if not metrics:
            return self._initialize_queue_metrics(queue_id, tenant_uuid)
        
        return {k.decode(): json.loads(v.decode()) for k, v in metrics.items()}
    
    def get_realtime_agent_metrics(self, agent_id: int, tenant_uuid: str) -> Dict:
        """Get real-time metrics for an agent."""
        metrics = self.redis.hgetall(f"agent_metrics:{agent_id}")
        if not metrics:
            return self._initialize_agent_metrics(agent_id, tenant_uuid)
        
        return {k.decode(): json.loads(v.decode()) for k, v in metrics.items()}
    
    def _update_call_metrics(self, event: Event) -> None:
        """Update metrics based on call events."""
        if not event.queue_id:
            return
        
        metrics_key = f"queue_metrics:{event.queue_id}"
        
        if event.event_name == 'call_entered':
            self.redis.hincrby(metrics_key, 'calls_waiting', 1)
        elif event.event_name == 'call_answered':
            self.redis.hincrby(metrics_key, 'calls_waiting', -1)
            self.redis.hincrby(metrics_key, 'answered_calls', 1)
            
            # Update agent metrics
            if event.agent_id:
                agent_key = f"agent_metrics:{event.agent_id}"
                self.redis.hincrby(agent_key, 'calls_taken', 1)
        elif event.event_name == 'call_abandoned':
            self.redis.hincrby(metrics_key, 'calls_waiting', -1)
            self.redis.hincrby(metrics_key, 'abandoned_calls', 1)
    
    def _update_agent_metrics(self, event: Event) -> None:
        """Update metrics based on agent events."""
        if not event.agent_id:
            return
        
        metrics_key = f"agent_metrics:{event.agent_id}"
        
        if event.event_name == 'agent_login':
            self.redis.hset(metrics_key, 'current_state', 'available')
            self.redis.hset(metrics_key, 'state_duration', 0)
            
            if event.queue_id:
                queue_key = f"queue_metrics:{event.queue_id}"
                self.redis.hincrby(queue_key, 'agents_logged', 1)
                self.redis.hincrby(queue_key, 'agents_available', 1)
        
        elif event.event_name == 'agent_logout':
            if event.queue_id:
                queue_key = f"queue_metrics:{event.queue_id}"
                self.redis.hincrby(queue_key, 'agents_logged', -1)
                
                prev_state = self.redis.hget(metrics_key, 'current_state')
                if prev_state == b'available':
                    self.redis.hincrby(queue_key, 'agents_available', -1)
                elif prev_state == b'on_call':
                    self.redis.hincrby(queue_key, 'agents_on_call', -1)
                elif prev_state == b'paused':
                    self.redis.hincrby(queue_key, 'agents_paused', -1)
    
    def _initialize_queue_metrics(self, queue_id: int, tenant_uuid: str) -> Dict:
        """Initialize metrics for a queue."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue:
            raise QueueNotFound(queue_id)
        
        metrics = {
            'calls_waiting': 0,
            'longest_wait': 0,
            'service_level': 0.0,
            'abandoned_calls': 0,
            'answered_calls': 0,
            'average_wait': 0.0,
            'average_talk': 0.0,
            'agents_logged': 0,
            'agents_available': 0,
            'agents_on_call': 0,
            'agents_paused': 0
        }
        
        metrics_key = f"queue_metrics:{queue_id}"
        for key, value in metrics.items():
            self.redis.hset(metrics_key, key, json.dumps(value))
        
        return metrics
    
    def _initialize_agent_metrics(self, agent_id: int, tenant_uuid: str) -> Dict:
        """Initialize metrics for an agent."""
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        metrics = {
            'calls_taken': 0,
            'total_talk_time': 0,
            'average_talk_time': 0.0,
            'total_wrap_time': 0,
            'average_wrap_time': 0.0,
            'occupancy_rate': 0.0,
            'adherence_rate': 0.0,
            'current_state': 'logged_out',
            'state_duration': 0
        }
        
        metrics_key = f"agent_metrics:{agent_id}"
        for key, value in metrics.items():
            self.redis.hset(metrics_key, key, json.dumps(value))
        
        return metrics
    
    def _publish_event(self, event: Event) -> None:
        """Publish event to Redis channels."""
        event_data = event.to_dict
        
        # Publish to tenant channel
        self.redis.publish(f"events:tenant:{event.tenant_uuid}", json.dumps(event_data))
        
        # Publish to queue channel if applicable
        if event.queue_id:
            self.redis.publish(f"events:queue:{event.queue_id}", json.dumps(event_data))
        
        # Publish to agent channel if applicable
        if event.agent_id:
            self.redis.publish(f"events:agent:{event.agent_id}", json.dumps(event_data))
    
    def get_queue_stats_summary(self, queue_id: int, tenant_uuid: str,
                              interval: str = '1h') -> Dict:
        """Get queue statistics summary for a time interval."""
        end_time = datetime.utcnow()
        
        if interval == '1h':
            start_time = end_time - timedelta(hours=1)
        elif interval == '6h':
            start_time = end_time - timedelta(hours=6)
        elif interval == '24h':
            start_time = end_time - timedelta(days=1)
        else:
            raise ValueError("Invalid interval. Must be '1h', '6h', or '24h'")
        
        metrics = self.session.query(
            func.avg(QueueMetrics.service_level).label('avg_service_level'),
            func.avg(QueueMetrics.average_wait).label('avg_wait_time'),
            func.avg(QueueMetrics.average_talk).label('avg_talk_time'),
            func.sum(QueueMetrics.answered_calls).label('total_answered'),
            func.sum(QueueMetrics.abandoned_calls).label('total_abandoned')
        ).filter(
            QueueMetrics.queue_id == queue_id,
            QueueMetrics.tenant_uuid == tenant_uuid,
            QueueMetrics.timestamp.between(start_time, end_time)
        ).first()
        
        return {
            'interval': interval,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'avg_service_level': float(metrics.avg_service_level or 0),
            'avg_wait_time': float(metrics.avg_wait_time or 0),
            'avg_talk_time': float(metrics.avg_talk_time or 0),
            'total_answered': int(metrics.total_answered or 0),
            'total_abandoned': int(metrics.total_abandoned or 0)
        }
    
    def get_agent_stats_summary(self, agent_id: int, tenant_uuid: str,
                              interval: str = '1h') -> Dict:
        """Get agent statistics summary for a time interval."""
        end_time = datetime.utcnow()
        
        if interval == '1h':
            start_time = end_time - timedelta(hours=1)
        elif interval == '6h':
            start_time = end_time - timedelta(hours=6)
        elif interval == '24h':
            start_time = end_time - timedelta(days=1)
        else:
            raise ValueError("Invalid interval. Must be '1h', '6h', or '24h'")
        
        metrics = self.session.query(
            func.sum(AgentMetrics.calls_taken).label('total_calls'),
            func.avg(AgentMetrics.average_talk_time).label('avg_talk_time'),
            func.avg(AgentMetrics.average_wrap_time).label('avg_wrap_time'),
            func.avg(AgentMetrics.occupancy_rate).label('avg_occupancy'),
            func.avg(AgentMetrics.adherence_rate).label('avg_adherence')
        ).filter(
            AgentMetrics.agent_id == agent_id,
            AgentMetrics.tenant_uuid == tenant_uuid,
            AgentMetrics.timestamp.between(start_time, end_time)
        ).first()
        
        return {
            'interval': interval,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_calls': int(metrics.total_calls or 0),
            'avg_talk_time': float(metrics.avg_talk_time or 0),
            'avg_wrap_time': float(metrics.avg_wrap_time or 0),
            'avg_occupancy': float(metrics.avg_occupancy or 0),
            'avg_adherence': float(metrics.avg_adherence or 0)
        }
