"""Reliability models for health checks and circuit breakers."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum
from datetime import datetime
from . import Base

class ServiceHealth(Base):
    """Service health model for tracking service status."""
    
    __tablename__ = 'call_distributor_service_health'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    service_name = Column(String(64), nullable=False)
    
    # Health status
    status = Column(Enum('healthy', 'degraded', 'unhealthy',
                        name='health_status'), nullable=False)
    last_check = Column(DateTime, nullable=False)
    last_success = Column(DateTime)
    
    # Check details
    check_type = Column(String(32), nullable=False)  # 'http', 'tcp', 'custom'
    check_config = Column(JSON, nullable=False)  # Check configuration
    
    # Failure tracking
    consecutive_failures = Column(Integer, default=0)
    last_error = Column(String(1024))
    error_count = Column(Integer, default=0)
    
    # Circuit breaker settings
    circuit_open = Column(Boolean, default=False)
    circuit_open_until = Column(DateTime)
    
    def __repr__(self):
        return f'<ServiceHealth(service={self.service_name}, status={self.status})>'
    
    @property
    def to_dict(self):
        """Convert service health to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'service_name': self.service_name,
            'status': self.status,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'check_type': self.check_type,
            'check_config': self.check_config,
            'consecutive_failures': self.consecutive_failures,
            'last_error': self.last_error,
            'error_count': self.error_count,
            'circuit_open': self.circuit_open,
            'circuit_open_until': self.circuit_open_until.isoformat() if self.circuit_open_until else None
        }

class RateLimitConfig(Base):
    """Rate limit configuration model."""
    
    __tablename__ = 'call_distributor_rate_limits'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    
    # Rate limit scope
    endpoint = Column(String(128), nullable=False)  # API endpoint or operation
    method = Column(String(16))  # HTTP method
    
    # Limit settings
    requests_per_second = Column(Integer, nullable=False)
    burst_size = Column(Integer, default=1)
    
    # Additional settings
    enabled = Column(Boolean, default=True)
    custom_settings = Column(JSON, default={})
    
    def __repr__(self):
        return f'<RateLimitConfig(endpoint={self.endpoint})>'
    
    @property
    def to_dict(self):
        """Convert rate limit config to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'endpoint': self.endpoint,
            'method': self.method,
            'requests_per_second': self.requests_per_second,
            'burst_size': self.burst_size,
            'enabled': self.enabled,
            'custom_settings': self.custom_settings
        }

class BackupConfig(Base):
    """Backup configuration model."""
    
    __tablename__ = 'call_distributor_backup_configs'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    
    # Backup settings
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    enabled = Column(Boolean, default=True)
    
    # Schedule settings
    schedule_interval = Column(String(32))  # 'daily', 'weekly', 'monthly'
    schedule_time = Column(String(5))  # HH:MM format
    schedule_day = Column(Integer)  # Day of week/month
    
    # Storage settings
    storage_type = Column(String(32), nullable=False)  # 's3', 'local', etc.
    storage_config = Column(JSON, nullable=False)
    
    # Retention settings
    retention_days = Column(Integer, default=30)
    max_backups = Column(Integer, default=10)
    
    # Last backup info
    last_backup = Column(DateTime)
    last_status = Column(String(32))
    last_error = Column(String(1024))
    
    def __repr__(self):
        return f'<BackupConfig(name={self.name})>'
    
    @property
    def to_dict(self):
        """Convert backup config to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'schedule_interval': self.schedule_interval,
            'schedule_time': self.schedule_time,
            'schedule_day': self.schedule_day,
            'storage_type': self.storage_type,
            'storage_config': self.storage_config,
            'retention_days': self.retention_days,
            'max_backups': self.max_backups,
            'last_backup': self.last_backup.isoformat() if self.last_backup else None,
            'last_status': self.last_status,
            'last_error': self.last_error
        }

class FailoverConfig(Base):
    """Failover configuration model."""
    
    __tablename__ = 'call_distributor_failover_configs'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    queue_id = Column(Integer, nullable=False)
    
    # Failover settings
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    enabled = Column(Boolean, default=True)
    
    # Trigger conditions
    max_queue_size = Column(Integer)  # Maximum callers in queue
    max_wait_time = Column(Integer)  # Maximum wait time in seconds
    service_level_threshold = Column(Integer)  # Service level percentage
    agent_availability_threshold = Column(Integer)  # Minimum available agents
    
    # Failover targets
    failover_type = Column(String(32), nullable=False)  # 'queue', 'ivr', 'voicemail'
    failover_destination = Column(String(128), nullable=False)
    
    # Recovery settings
    auto_recovery = Column(Boolean, default=True)
    recovery_threshold = Column(Integer)  # Time in seconds before recovery
    
    # Status tracking
    active = Column(Boolean, default=False)
    last_activation = Column(DateTime)
    last_recovery = Column(DateTime)
    
    def __repr__(self):
        return f'<FailoverConfig(name={self.name}, queue_id={self.queue_id})>'
    
    @property
    def to_dict(self):
        """Convert failover config to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'queue_id': self.queue_id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'max_queue_size': self.max_queue_size,
            'max_wait_time': self.max_wait_time,
            'service_level_threshold': self.service_level_threshold,
            'agent_availability_threshold': self.agent_availability_threshold,
            'failover_type': self.failover_type,
            'failover_destination': self.failover_destination,
            'auto_recovery': self.auto_recovery,
            'recovery_threshold': self.recovery_threshold,
            'active': self.active,
            'last_activation': self.last_activation.isoformat() if self.last_activation else None,
            'last_recovery': self.last_recovery.isoformat() if self.last_recovery else None
        }
