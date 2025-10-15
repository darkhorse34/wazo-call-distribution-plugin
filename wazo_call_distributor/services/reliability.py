"""Reliability service for health checks and circuit breakers."""

import requests
import socket
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from ..models import (
    ServiceHealth, RateLimitConfig, BackupConfig, FailoverConfig,
    Queue, QueueMetrics
)

class ReliabilityService:
    """Service for managing reliability features."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_service_health(self, service_name: str, tenant_uuid: str) -> ServiceHealth:
        """Get health status for a service."""
        health = self.session.query(ServiceHealth).filter(
            ServiceHealth.service_name == service_name,
            ServiceHealth.tenant_uuid == tenant_uuid
        ).first()
        
        if not health:
            raise ValueError(f"Service health not found: {service_name}")
        
        return health
    
    def list_service_health(self, tenant_uuid: str) -> List[ServiceHealth]:
        """List health status for all services."""
        return self.session.query(ServiceHealth).filter(
            ServiceHealth.tenant_uuid == tenant_uuid
        ).all()
    
    def check_service_health(self, service_name: str,
                           tenant_uuid: str) -> ServiceHealth:
        """Perform health check for a service."""
        health = self.get_service_health(service_name, tenant_uuid)
        
        # Skip check if circuit breaker is open
        if health.circuit_open:
            if health.circuit_open_until and datetime.utcnow() < health.circuit_open_until:
                return health
            else:
                health.circuit_open = False
        
        try:
            if health.check_type == 'http':
                self._check_http_health(health)
            elif health.check_type == 'tcp':
                self._check_tcp_health(health)
            elif health.check_type == 'custom':
                self._check_custom_health(health)
            
            # Update success metrics
            health.status = 'healthy'
            health.last_check = datetime.utcnow()
            health.last_success = datetime.utcnow()
            health.consecutive_failures = 0
            health.last_error = None
            
        except Exception as e:
            # Update failure metrics
            health.status = 'unhealthy'
            health.last_check = datetime.utcnow()
            health.consecutive_failures += 1
            health.last_error = str(e)
            health.error_count += 1
            
            # Check circuit breaker conditions
            if health.consecutive_failures >= health.check_config.get('max_failures', 3):
                health.circuit_open = True
                health.circuit_open_until = datetime.utcnow() + timedelta(
                    seconds=health.check_config.get('reset_timeout', 300)
                )
        
        self.session.commit()
        return health
    
    def _check_http_health(self, health: ServiceHealth) -> None:
        """Perform HTTP health check."""
        config = health.check_config
        response = requests.request(
            method=config.get('method', 'GET'),
            url=config['url'],
            headers=config.get('headers', {}),
            timeout=config.get('timeout', 5),
            verify=config.get('ssl_verify', True)
        )
        
        if not response.ok:
            raise ValueError(f"HTTP check failed: {response.status_code}")
    
    def _check_tcp_health(self, health: ServiceHealth) -> None:
        """Perform TCP health check."""
        config = health.check_config
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(config.get('timeout', 5))
        
        try:
            sock.connect((config['host'], config['port']))
        finally:
            sock.close()
    
    def _check_custom_health(self, health: ServiceHealth) -> None:
        """Perform custom health check."""
        # TODO: Implement custom health check logic
        pass
    
    def get_rate_limit(self, endpoint: str, tenant_uuid: str) -> RateLimitConfig:
        """Get rate limit configuration."""
        limit = self.session.query(RateLimitConfig).filter(
            RateLimitConfig.endpoint == endpoint,
            RateLimitConfig.tenant_uuid == tenant_uuid
        ).first()
        
        if not limit:
            raise ValueError(f"Rate limit not found: {endpoint}")
        
        return limit
    
    def list_rate_limits(self, tenant_uuid: str) -> List[RateLimitConfig]:
        """List all rate limit configurations."""
        return self.session.query(RateLimitConfig).filter(
            RateLimitConfig.tenant_uuid == tenant_uuid
        ).all()
    
    def create_rate_limit(self, tenant_uuid: str,
                         limit_data: Dict) -> RateLimitConfig:
        """Create a new rate limit configuration."""
        limit = RateLimitConfig(tenant_uuid=tenant_uuid, **limit_data)
        self.session.add(limit)
        self.session.commit()
        return limit
    
    def update_rate_limit(self, endpoint: str, tenant_uuid: str,
                         limit_data: Dict) -> RateLimitConfig:
        """Update a rate limit configuration."""
        limit = self.get_rate_limit(endpoint, tenant_uuid)
        
        for key, value in limit_data.items():
            setattr(limit, key, value)
        
        self.session.commit()
        return limit
    
    def delete_rate_limit(self, endpoint: str, tenant_uuid: str) -> None:
        """Delete a rate limit configuration."""
        limit = self.get_rate_limit(endpoint, tenant_uuid)
        self.session.delete(limit)
        self.session.commit()
    
    def get_backup_config(self, config_id: int, tenant_uuid: str) -> BackupConfig:
        """Get backup configuration."""
        config = self.session.query(BackupConfig).filter(
            BackupConfig.id == config_id,
            BackupConfig.tenant_uuid == tenant_uuid
        ).first()
        
        if not config:
            raise ValueError(f"Backup config {config_id} not found")
        
        return config
    
    def list_backup_configs(self, tenant_uuid: str) -> List[BackupConfig]:
        """List all backup configurations."""
        return self.session.query(BackupConfig).filter(
            BackupConfig.tenant_uuid == tenant_uuid
        ).all()
    
    def create_backup_config(self, tenant_uuid: str,
                           config_data: Dict) -> BackupConfig:
        """Create a new backup configuration."""
        config = BackupConfig(tenant_uuid=tenant_uuid, **config_data)
        self.session.add(config)
        self.session.commit()
        return config
    
    def update_backup_config(self, config_id: int, tenant_uuid: str,
                           config_data: Dict) -> BackupConfig:
        """Update a backup configuration."""
        config = self.get_backup_config(config_id, tenant_uuid)
        
        for key, value in config_data.items():
            setattr(config, key, value)
        
        self.session.commit()
        return config
    
    def delete_backup_config(self, config_id: int, tenant_uuid: str) -> None:
        """Delete a backup configuration."""
        config = self.get_backup_config(config_id, tenant_uuid)
        self.session.delete(config)
        self.session.commit()
    
    def get_failover_config(self, config_id: int, tenant_uuid: str) -> FailoverConfig:
        """Get failover configuration."""
        config = self.session.query(FailoverConfig).filter(
            FailoverConfig.id == config_id,
            FailoverConfig.tenant_uuid == tenant_uuid
        ).first()
        
        if not config:
            raise ValueError(f"Failover config {config_id} not found")
        
        return config
    
    def list_failover_configs(self, tenant_uuid: str,
                            queue_id: Optional[int] = None) -> List[FailoverConfig]:
        """List all failover configurations."""
        query = self.session.query(FailoverConfig).filter(
            FailoverConfig.tenant_uuid == tenant_uuid
        )
        
        if queue_id:
            query = query.filter(FailoverConfig.queue_id == queue_id)
        
        return query.all()
    
    def create_failover_config(self, tenant_uuid: str,
                             config_data: Dict) -> FailoverConfig:
        """Create a new failover configuration."""
        config = FailoverConfig(tenant_uuid=tenant_uuid, **config_data)
        self.session.add(config)
        self.session.commit()
        return config
    
    def update_failover_config(self, config_id: int, tenant_uuid: str,
                             config_data: Dict) -> FailoverConfig:
        """Update a failover configuration."""
        config = self.get_failover_config(config_id, tenant_uuid)
        
        for key, value in config_data.items():
            setattr(config, key, value)
        
        self.session.commit()
        return config
    
    def delete_failover_config(self, config_id: int, tenant_uuid: str) -> None:
        """Delete a failover configuration."""
        config = self.get_failover_config(config_id, tenant_uuid)
        self.session.delete(config)
        self.session.commit()
    
    def check_failover_conditions(self, queue_id: int,
                                tenant_uuid: str) -> List[Tuple[FailoverConfig, str]]:
        """Check failover conditions for a queue."""
        configs = self.list_failover_configs(tenant_uuid, queue_id)
        triggered = []
        
        for config in configs:
            if not config.enabled:
                continue
            
            # Get current queue metrics
            metrics = self.session.query(QueueMetrics).filter(
                QueueMetrics.queue_id == queue_id,
                QueueMetrics.tenant_uuid == tenant_uuid
            ).order_by(QueueMetrics.timestamp.desc()).first()
            
            if not metrics:
                continue
            
            # Check conditions
            reason = None
            
            if config.max_queue_size and metrics.calls_waiting >= config.max_queue_size:
                reason = f"Queue size ({metrics.calls_waiting}) exceeds maximum ({config.max_queue_size})"
            
            elif config.max_wait_time and metrics.longest_wait >= config.max_wait_time:
                reason = f"Wait time ({metrics.longest_wait}s) exceeds maximum ({config.max_wait_time}s)"
            
            elif config.service_level_threshold and metrics.service_level < config.service_level_threshold:
                reason = f"Service level ({metrics.service_level}%) below threshold ({config.service_level_threshold}%)"
            
            elif config.agent_availability_threshold and metrics.agents_available < config.agent_availability_threshold:
                reason = f"Available agents ({metrics.agents_available}) below threshold ({config.agent_availability_threshold})"
            
            if reason:
                triggered.append((config, reason))
        
        return triggered
    
    def activate_failover(self, config_id: int, tenant_uuid: str) -> FailoverConfig:
        """Activate failover for a configuration."""
        config = self.get_failover_config(config_id, tenant_uuid)
        
        if not config.enabled:
            raise ValueError("Failover config is disabled")
        
        config.active = True
        config.last_activation = datetime.utcnow()
        
        self.session.commit()
        return config
    
    def deactivate_failover(self, config_id: int, tenant_uuid: str) -> FailoverConfig:
        """Deactivate failover for a configuration."""
        config = self.get_failover_config(config_id, tenant_uuid)
        
        config.active = False
        config.last_recovery = datetime.utcnow()
        
        self.session.commit()
        return config
