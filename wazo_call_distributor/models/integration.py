"""Integration models for third-party services."""

from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from . import Base

class Integration(Base):
    """Integration model for third-party services."""
    
    __tablename__ = 'call_distributor_integrations'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Integration type
    type = Column(Enum('crm', 'helpdesk', 'analytics', 'custom',
                      name='integration_type'), nullable=False)
    provider = Column(String(64), nullable=False)  # e.g., 'salesforce', 'zendesk'
    
    # Authentication
    auth_type = Column(String(32), nullable=False)  # 'oauth2', 'api_key', 'basic'
    auth_config = Column(JSON, nullable=False)  # Authentication details
    
    # Integration settings
    enabled = Column(Boolean, default=True)
    settings = Column(JSON, default={})
    
    # Field mappings
    field_mappings = Column(JSON, default={})
    
    def __repr__(self):
        return f'<Integration(name={self.name}, type={self.type})>'
    
    @property
    def to_dict(self):
        """Convert integration to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'provider': self.provider,
            'auth_type': self.auth_type,
            'enabled': self.enabled,
            'settings': self.settings,
            'field_mappings': self.field_mappings
        }

class Webhook(Base):
    """Webhook model for event notifications."""
    
    __tablename__ = 'call_distributor_webhooks'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256))
    
    # Webhook configuration
    url = Column(String(512), nullable=False)
    method = Column(String(16), default='POST')  # HTTP method
    headers = Column(JSON, default={})
    
    # Event settings
    event_types = Column(JSON, nullable=False)  # List of event types to trigger on
    queue_ids = Column(JSON)  # Optional list of queue IDs to filter on
    agent_ids = Column(JSON)  # Optional list of agent IDs to filter on
    
    # Retry settings
    retry_enabled = Column(Boolean, default=True)
    retry_max_attempts = Column(Integer, default=3)
    retry_interval = Column(Integer, default=60)  # seconds
    
    # Security settings
    secret_token = Column(String(128))  # For webhook signature
    ssl_verify = Column(Boolean, default=True)
    
    # Status tracking
    enabled = Column(Boolean, default=True)
    last_status = Column(String(32))
    last_status_time = Column(String(32))
    
    def __repr__(self):
        return f'<Webhook(name={self.name})>'
    
    @property
    def to_dict(self):
        """Convert webhook to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'method': self.method,
            'headers': self.headers,
            'event_types': self.event_types,
            'queue_ids': self.queue_ids,
            'agent_ids': self.agent_ids,
            'retry_enabled': self.retry_enabled,
            'retry_max_attempts': self.retry_max_attempts,
            'retry_interval': self.retry_interval,
            'ssl_verify': self.ssl_verify,
            'enabled': self.enabled,
            'last_status': self.last_status,
            'last_status_time': self.last_status_time
        }

class WebhookDelivery(Base):
    """Webhook delivery model for tracking webhook attempts."""
    
    __tablename__ = 'call_distributor_webhook_deliveries'
    
    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey('call_distributor_webhooks.id'), nullable=False)
    
    # Event data
    event_type = Column(String(64), nullable=False)
    event_id = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    
    # Delivery attempt
    timestamp = Column(String(32), nullable=False)
    status_code = Column(Integer)
    status = Column(String(32), nullable=False)  # 'success', 'failed', 'pending'
    response = Column(String(1024))
    error = Column(String(1024))
    
    # Retry tracking
    attempt = Column(Integer, default=1)
    next_retry = Column(String(32))
    
    # Relationship
    webhook = relationship('Webhook')
    
    def __repr__(self):
        return f'<WebhookDelivery(webhook_id={self.webhook_id}, status={self.status})>'
    
    @property
    def to_dict(self):
        """Convert delivery to dictionary representation."""
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'event_type': self.event_type,
            'event_id': self.event_id,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'status_code': self.status_code,
            'status': self.status,
            'response': self.response,
            'error': self.error,
            'attempt': self.attempt,
            'next_retry': self.next_retry
        }
