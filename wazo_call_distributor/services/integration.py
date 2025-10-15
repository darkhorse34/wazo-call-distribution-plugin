"""Integration service for third-party services and webhooks."""

import hmac
import hashlib
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Integration, Webhook, WebhookDelivery

class IntegrationService:
    """Service for managing third-party integrations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_integration(self, integration_id: int, tenant_uuid: str) -> Integration:
        """Get an integration by ID."""
        integration = self.session.query(Integration).filter(
            Integration.id == integration_id,
            Integration.tenant_uuid == tenant_uuid
        ).first()
        
        if not integration:
            raise ValueError(f"Integration {integration_id} not found")
        
        return integration
    
    def list_integrations(self, tenant_uuid: str,
                         integration_type: Optional[str] = None) -> List[Integration]:
        """List all integrations for a tenant."""
        query = self.session.query(Integration).filter(
            Integration.tenant_uuid == tenant_uuid
        )
        
        if integration_type:
            query = query.filter(Integration.type == integration_type)
        
        return query.all()
    
    def create_integration(self, tenant_uuid: str,
                         integration_data: Dict) -> Integration:
        """Create a new integration."""
        integration = Integration(tenant_uuid=tenant_uuid, **integration_data)
        self.session.add(integration)
        self.session.commit()
        return integration
    
    def update_integration(self, integration_id: int, tenant_uuid: str,
                         integration_data: Dict) -> Integration:
        """Update an existing integration."""
        integration = self.get_integration(integration_id, tenant_uuid)
        
        for key, value in integration_data.items():
            setattr(integration, key, value)
        
        self.session.commit()
        return integration
    
    def delete_integration(self, integration_id: int, tenant_uuid: str) -> None:
        """Delete an integration."""
        integration = self.get_integration(integration_id, tenant_uuid)
        self.session.delete(integration)
        self.session.commit()
    
    def get_webhook(self, webhook_id: int, tenant_uuid: str) -> Webhook:
        """Get a webhook by ID."""
        webhook = self.session.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.tenant_uuid == tenant_uuid
        ).first()
        
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")
        
        return webhook
    
    def list_webhooks(self, tenant_uuid: str) -> List[Webhook]:
        """List all webhooks for a tenant."""
        return self.session.query(Webhook).filter(
            Webhook.tenant_uuid == tenant_uuid
        ).all()
    
    def create_webhook(self, tenant_uuid: str, webhook_data: Dict) -> Webhook:
        """Create a new webhook."""
        webhook = Webhook(tenant_uuid=tenant_uuid, **webhook_data)
        self.session.add(webhook)
        self.session.commit()
        return webhook
    
    def update_webhook(self, webhook_id: int, tenant_uuid: str,
                      webhook_data: Dict) -> Webhook:
        """Update an existing webhook."""
        webhook = self.get_webhook(webhook_id, tenant_uuid)
        
        for key, value in webhook_data.items():
            setattr(webhook, key, value)
        
        self.session.commit()
        return webhook
    
    def delete_webhook(self, webhook_id: int, tenant_uuid: str) -> None:
        """Delete a webhook."""
        webhook = self.get_webhook(webhook_id, tenant_uuid)
        self.session.delete(webhook)
        self.session.commit()
    
    def get_webhook_deliveries(self, webhook_id: int,
                             tenant_uuid: str) -> List[WebhookDelivery]:
        """Get delivery history for a webhook."""
        webhook = self.get_webhook(webhook_id, tenant_uuid)
        return self.session.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook.id
        ).order_by(WebhookDelivery.timestamp.desc()).all()
    
    def trigger_webhook(self, webhook_id: int, tenant_uuid: str,
                       event_type: str, event_data: Dict) -> WebhookDelivery:
        """Trigger a webhook for an event."""
        webhook = self.get_webhook(webhook_id, tenant_uuid)
        
        if not webhook.enabled or event_type not in webhook.event_types:
            return None
        
        # Check queue and agent filters
        if webhook.queue_ids and event_data.get('queue_id') not in webhook.queue_ids:
            return None
        if webhook.agent_ids and event_data.get('agent_id') not in webhook.agent_ids:
            return None
        
        # Prepare payload
        payload = {
            'event_type': event_type,
            'tenant_uuid': tenant_uuid,
            'timestamp': datetime.utcnow().isoformat(),
            'data': event_data
        }
        
        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            event_id=event_data.get('id', str(datetime.utcnow().timestamp())),
            payload=payload,
            timestamp=datetime.utcnow().isoformat(),
            status='pending'
        )
        self.session.add(delivery)
        self.session.commit()
        
        # Send webhook
        try:
            headers = webhook.headers or {}
            
            # Add signature if secret token is configured
            if webhook.secret_token:
                signature = self._generate_signature(webhook.secret_token, payload)
                headers['X-Webhook-Signature'] = signature
            
            response = requests.request(
                method=webhook.method,
                url=webhook.url,
                json=payload,
                headers=headers,
                verify=webhook.ssl_verify,
                timeout=30
            )
            
            delivery.status_code = response.status_code
            delivery.response = response.text[:1024]  # Truncate long responses
            
            if response.ok:
                delivery.status = 'success'
            else:
                delivery.status = 'failed'
                delivery.error = f"HTTP {response.status_code}: {response.text[:1024]}"
                
                # Schedule retry if enabled
                if webhook.retry_enabled and delivery.attempt < webhook.retry_max_attempts:
                    delivery.next_retry = (
                        datetime.utcnow() + timedelta(seconds=webhook.retry_interval)
                    ).isoformat()
        
        except Exception as e:
            delivery.status = 'failed'
            delivery.error = str(e)[:1024]
            
            # Schedule retry if enabled
            if webhook.retry_enabled and delivery.attempt < webhook.retry_max_attempts:
                delivery.next_retry = (
                    datetime.utcnow() + timedelta(seconds=webhook.retry_interval)
                ).isoformat()
        
        # Update webhook status
        webhook.last_status = delivery.status
        webhook.last_status_time = delivery.timestamp
        
        self.session.commit()
        return delivery
    
    def retry_webhook(self, delivery_id: int) -> WebhookDelivery:
        """Retry a failed webhook delivery."""
        delivery = self.session.query(WebhookDelivery).get(delivery_id)
        
        if not delivery or delivery.status == 'success':
            return None
        
        webhook = delivery.webhook
        if not webhook.enabled or not webhook.retry_enabled:
            return None
        
        # Create new delivery attempt
        new_delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=delivery.event_type,
            event_id=delivery.event_id,
            payload=delivery.payload,
            timestamp=datetime.utcnow().isoformat(),
            status='pending',
            attempt=delivery.attempt + 1
        )
        self.session.add(new_delivery)
        self.session.commit()
        
        # Send webhook
        try:
            headers = webhook.headers or {}
            
            if webhook.secret_token:
                signature = self._generate_signature(webhook.secret_token, new_delivery.payload)
                headers['X-Webhook-Signature'] = signature
            
            response = requests.request(
                method=webhook.method,
                url=webhook.url,
                json=new_delivery.payload,
                headers=headers,
                verify=webhook.ssl_verify,
                timeout=30
            )
            
            new_delivery.status_code = response.status_code
            new_delivery.response = response.text[:1024]
            
            if response.ok:
                new_delivery.status = 'success'
            else:
                new_delivery.status = 'failed'
                new_delivery.error = f"HTTP {response.status_code}: {response.text[:1024]}"
                
                if webhook.retry_enabled and new_delivery.attempt < webhook.retry_max_attempts:
                    new_delivery.next_retry = (
                        datetime.utcnow() + timedelta(seconds=webhook.retry_interval)
                    ).isoformat()
        
        except Exception as e:
            new_delivery.status = 'failed'
            new_delivery.error = str(e)[:1024]
            
            if webhook.retry_enabled and new_delivery.attempt < webhook.retry_max_attempts:
                new_delivery.next_retry = (
                    datetime.utcnow() + timedelta(seconds=webhook.retry_interval)
                ).isoformat()
        
        # Update webhook status
        webhook.last_status = new_delivery.status
        webhook.last_status_time = new_delivery.timestamp
        
        self.session.commit()
        return new_delivery
    
    def process_pending_retries(self) -> int:
        """Process pending webhook retries."""
        now = datetime.utcnow()
        
        # Find deliveries due for retry
        deliveries = self.session.query(WebhookDelivery).filter(
            WebhookDelivery.status == 'failed',
            WebhookDelivery.next_retry <= now.isoformat()
        ).all()
        
        retry_count = 0
        for delivery in deliveries:
            self.retry_webhook(delivery.id)
            retry_count += 1
        
        return retry_count
    
    def _generate_signature(self, secret: str, payload: Dict) -> str:
        """Generate webhook signature."""
        payload_str = json.dumps(payload, sort_keys=True)
        return hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
