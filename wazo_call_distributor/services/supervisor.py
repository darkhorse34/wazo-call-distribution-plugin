"""Supervisor service for monitoring and control."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from ..models import (
    SupervisorSettings, Alert, MonitoringProfile,
    Queue, Agent, QueueMetrics, AgentMetrics
)
from ..exceptions import AgentNotFound

class SupervisorService:
    """Service for supervisor features."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_supervisor_settings(self, agent_id: int,
                              tenant_uuid: str) -> SupervisorSettings:
        """Get supervisor settings."""
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        settings = self.session.query(SupervisorSettings).filter(
            SupervisorSettings.agent_id == agent_id,
            SupervisorSettings.tenant_uuid == tenant_uuid
        ).first()
        
        if not settings:
            # Create default settings
            settings = SupervisorSettings(
                agent_id=agent_id,
                tenant_uuid=tenant_uuid
            )
            self.session.add(settings)
            self.session.commit()
        
        return settings
    
    def update_supervisor_settings(self, agent_id: int, tenant_uuid: str,
                                 settings_data: Dict) -> SupervisorSettings:
        """Update supervisor settings."""
        settings = self.get_supervisor_settings(agent_id, tenant_uuid)
        
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        self.session.commit()
        return settings
    
    def get_wallboard_data(self, agent_id: int, tenant_uuid: str) -> Dict:
        """Get wallboard data for queues and agents."""
        settings = self.get_supervisor_settings(agent_id, tenant_uuid)
        
        # Get real-time queue metrics
        queue_metrics = self.session.query(QueueMetrics).filter(
            QueueMetrics.tenant_uuid == tenant_uuid
        ).order_by(QueueMetrics.timestamp.desc()).limit(10).all()
        
        # Get real-time agent metrics
        agent_metrics = self.session.query(AgentMetrics).filter(
            AgentMetrics.tenant_uuid == tenant_uuid
        ).order_by(AgentMetrics.timestamp.desc()).limit(10).all()
        
        # Get active alerts
        alerts = self.session.query(Alert).filter(
            Alert.tenant_uuid == tenant_uuid,
            Alert.acknowledged == False
        ).order_by(Alert.timestamp.desc()).all()
        
        return {
            'queues': [metric.to_dict for metric in queue_metrics],
            'agents': [metric.to_dict for metric in agent_metrics],
            'alerts': [alert.to_dict for alert in alerts],
            'layout': settings.wallboard_layout
        }
    
    def check_thresholds(self, tenant_uuid: str) -> List[Alert]:
        """Check metrics against thresholds and generate alerts."""
        new_alerts = []
        
        # Get all supervisor settings to check thresholds
        settings_list = self.session.query(SupervisorSettings).filter(
            SupervisorSettings.tenant_uuid == tenant_uuid
        ).all()
        
        for settings in settings_list:
            thresholds = settings.alert_settings
            
            # Check queue metrics
            queue_metrics = self.session.query(QueueMetrics).filter(
                QueueMetrics.tenant_uuid == tenant_uuid,
                QueueMetrics.timestamp >= datetime.utcnow() - timedelta(minutes=5)
            ).all()
            
            for metric in queue_metrics:
                # Check SLA threshold
                if metric.service_level < thresholds['sla_threshold']:
                    alert = Alert(
                        tenant_uuid=tenant_uuid,
                        alert_type='sla',
                        source_type='queue',
                        source_id=metric.queue_id,
                        threshold=thresholds['sla_threshold'],
                        current_value=metric.service_level,
                        message=f"Queue {metric.queue_id} SLA below threshold: {metric.service_level}%",
                        timestamp=datetime.utcnow().isoformat()
                    )
                    new_alerts.append(alert)
                
                # Check abandon rate
                total_calls = metric.answered_calls + metric.abandoned_calls
                if total_calls > 0:
                    abandon_rate = (metric.abandoned_calls / total_calls) * 100
                    if abandon_rate > thresholds['abandon_threshold']:
                        alert = Alert(
                            tenant_uuid=tenant_uuid,
                            alert_type='abandon',
                            source_type='queue',
                            source_id=metric.queue_id,
                            threshold=thresholds['abandon_threshold'],
                            current_value=abandon_rate,
                            message=f"Queue {metric.queue_id} abandon rate above threshold: {abandon_rate}%",
                            timestamp=datetime.utcnow().isoformat()
                        )
                        new_alerts.append(alert)
                
                # Check wait time
                if metric.longest_wait > thresholds['wait_time_threshold']:
                    alert = Alert(
                        tenant_uuid=tenant_uuid,
                        alert_type='wait_time',
                        source_type='queue',
                        source_id=metric.queue_id,
                        threshold=thresholds['wait_time_threshold'],
                        current_value=metric.longest_wait,
                        message=f"Queue {metric.queue_id} wait time above threshold: {metric.longest_wait}s",
                        timestamp=datetime.utcnow().isoformat()
                    )
                    new_alerts.append(alert)
        
        # Save new alerts
        for alert in new_alerts:
            self.session.add(alert)
        self.session.commit()
        
        return new_alerts
    
    def acknowledge_alert(self, alert_id: int, agent_id: int,
                        tenant_uuid: str) -> Alert:
        """Acknowledge an alert."""
        alert = self.session.query(Alert).filter(
            Alert.id == alert_id,
            Alert.tenant_uuid == tenant_uuid,
            Alert.acknowledged == False
        ).first()
        
        if not alert:
            raise ValueError(f"Alert {alert_id} not found or already acknowledged")
        
        alert.acknowledged = True
        alert.acknowledged_by = agent_id
        alert.acknowledged_at = datetime.utcnow().isoformat()
        
        self.session.commit()
        return alert
    
    def get_monitoring_profiles(self, agent_id: int,
                              tenant_uuid: str) -> List[MonitoringProfile]:
        """Get monitoring profiles for a supervisor."""
        return self.session.query(MonitoringProfile).filter(
            MonitoringProfile.agent_id == agent_id,
            MonitoringProfile.tenant_uuid == tenant_uuid
        ).all()
    
    def create_monitoring_profile(self, agent_id: int, tenant_uuid: str,
                                profile_data: Dict) -> MonitoringProfile:
        """Create a new monitoring profile."""
        profile = MonitoringProfile(
            agent_id=agent_id,
            tenant_uuid=tenant_uuid,
            **profile_data
        )
        
        self.session.add(profile)
        self.session.commit()
        return profile
    
    def update_monitoring_profile(self, profile_id: int, tenant_uuid: str,
                                profile_data: Dict) -> MonitoringProfile:
        """Update an existing monitoring profile."""
        profile = self.session.query(MonitoringProfile).filter(
            MonitoringProfile.id == profile_id,
            MonitoringProfile.tenant_uuid == tenant_uuid
        ).first()
        
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
        
        for key, value in profile_data.items():
            setattr(profile, key, value)
        
        self.session.commit()
        return profile
    
    def delete_monitoring_profile(self, profile_id: int,
                                tenant_uuid: str) -> None:
        """Delete a monitoring profile."""
        profile = self.session.query(MonitoringProfile).filter(
            MonitoringProfile.id == profile_id,
            MonitoringProfile.tenant_uuid == tenant_uuid
        ).first()
        
        if profile:
            self.session.delete(profile)
            self.session.commit()
    
    def get_queue_details(self, queue_id: int, tenant_uuid: str) -> Dict:
        """Get detailed queue statistics and information."""
        queue = self.session.query(Queue).filter(
            Queue.id == queue_id,
            Queue.tenant_uuid == tenant_uuid
        ).first()
        
        if not queue:
            raise ValueError(f"Queue {queue_id} not found")
        
        # Get latest metrics
        metrics = self.session.query(QueueMetrics).filter(
            QueueMetrics.queue_id == queue_id,
            QueueMetrics.tenant_uuid == tenant_uuid
        ).order_by(QueueMetrics.timestamp.desc()).first()
        
        # Get agents in queue
        agents = []
        for member in queue.members:
            agent = member.agent
            agent_metrics = self.session.query(AgentMetrics).filter(
                AgentMetrics.agent_id == agent.id,
                AgentMetrics.tenant_uuid == tenant_uuid
            ).order_by(AgentMetrics.timestamp.desc()).first()
            
            agents.append({
                'agent': agent.to_dict,
                'metrics': agent_metrics.to_dict if agent_metrics else None,
                'member_data': member.to_dict
            })
        
        return {
            'queue': queue.to_dict,
            'metrics': metrics.to_dict if metrics else None,
            'agents': agents
        }
    
    def get_agent_details(self, agent_id: int, tenant_uuid: str) -> Dict:
        """Get detailed agent statistics and information."""
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        # Get latest metrics
        metrics = self.session.query(AgentMetrics).filter(
            AgentMetrics.agent_id == agent_id,
            AgentMetrics.tenant_uuid == tenant_uuid
        ).order_by(AgentMetrics.timestamp.desc()).first()
        
        # Get queue memberships
        queues = []
        for member in agent.queue_members:
            queue = member.queue
            queue_metrics = self.session.query(QueueMetrics).filter(
                QueueMetrics.queue_id == queue.id,
                QueueMetrics.tenant_uuid == tenant_uuid
            ).order_by(QueueMetrics.timestamp.desc()).first()
            
            queues.append({
                'queue': queue.to_dict,
                'metrics': queue_metrics.to_dict if queue_metrics else None,
                'member_data': member.to_dict
            })
        
        return {
            'agent': agent.to_dict,
            'metrics': metrics.to_dict if metrics else None,
            'queues': queues
        }
