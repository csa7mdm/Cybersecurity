"""
Webhook System for External Integrations

Allows users to receive real-time notifications via webhooks
when scans complete, vulnerabilities are found, etc.
"""

import logging
import hmac
import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class WebhookEvent(Enum):
    """Webhook event types"""
    SCAN_STARTED = "scan.started"
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"
    VULNERABILITY_FOUND = "vulnerability.found"
    CRITICAL_FINDING = "critical.finding"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    TRIAL_EXPIRING = "trial.expiring"


@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    id: str
    url: str
    events: List[WebhookEvent]
    secret: str  # For signature verification
    enabled: bool = True
    retry_count: int = 3
    timeout: int = 10
    created_at: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class WebhookDelivery:
    """Record of webhook delivery attempt"""
    endpoint_id: str
    event_type: WebhookEvent
    payload: Dict[str, Any]
    status_code: Optional[int] = None
    success: bool = False
    attempt: int = 1
    timestamp: float = field(default_factory=time.time)
    error_message: Optional[str] = None


class WebhookService:
    """
    Webhook delivery service
    
    Manages webhook endpoints and delivers events with retry logic.
    """
    
    def __init__(self):
        """Initialize webhook service"""
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: List[WebhookDelivery] = []
    
    def register_webhook(
        self,
        url: str,
        events: List[WebhookEvent],
        secret: str
    ) -> WebhookEndpoint:
        """
        Register a new webhook endpoint
        
        Args:
            url: Webhook URL
            events: List of events to subscribe to
            secret: Secret key for signature verification
        
        Returns:
            Registered WebhookEndpoint
        """
        import uuid
        endpoint_id = str(uuid.uuid4())
        
        endpoint = WebhookEndpoint(
            id=endpoint_id,
            url=url,
            events=events,
            secret=secret
        )
        
        self.endpoints[endpoint_id] = endpoint
        logger.info(f"Registered webhook {endpoint_id} for {len(events)} events")
        
        return endpoint
    
    def unregister_webhook(self, endpoint_id: str) -> bool:
        """Unregister webhook endpoint"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"Unregistered webhook {endpoint_id}")
            return True
        return False
    
    def list_webhooks(self) -> List[WebhookEndpoint]:
        """List all registered webhooks"""
        return list(self.endpoints.values())
    
    async def send_webhook(
        self,
        event_type: WebhookEvent,
        payload: Dict[str, Any]
    ):
        """
        Send webhook to all subscribed endpoints
        
        Args:
            event_type: Type of event
            payload: Event data
        """
        # Find all endpoints subscribed to this event
        subscribed = [
            endpoint for endpoint in self.endpoints.values()
            if event_type in endpoint.events and endpoint.enabled
        ]
        
        if not subscribed:
            logger.debug(f"No webhooks registered for {event_type.value}")
            return
        
        logger.info(f"Sending {event_type.value} to {len(subscribed)} endpoints")
        
        # Send to all endpoints concurrently
        tasks = [
            self._deliver_webhook(endpoint, event_type, payload)
            for endpoint in subscribed
        ]
        
        await asyncio.gather(*tasks)
    
    async def _deliver_webhook(
        self,
        endpoint: WebhookEndpoint,
        event_type: WebhookEvent,
        payload: Dict[str, Any]
    ):
        """
        Deliver webhook to single endpoint with retry
        
        Args:
            endpoint: Webhook endpoint
            event_type: Event type
            payload: Event payload
        """
        # Prepare payload with metadata
        full_payload = {
            "event": event_type.value,
            "timestamp": time.time(),
            "data": payload
        }
        
        # Generate signature
        signature = self._generate_signature(endpoint.secret, full_payload)
        
        # Retry loop
        for attempt in range(1, endpoint.retry_count + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        endpoint.url,
                        json=full_payload,
                        headers={
                            "X-Webhook-Signature": signature,
                            "X-Event-Type": event_type.value,
                            "User-Agent": "CyperSecurity-Webhook/1.0"
                        },
                        timeout=aiohttp.ClientTimeout(total=endpoint.timeout)
                    ) as response:
                        status_code = response.status
                        
                        # Log delivery
                        delivery = WebhookDelivery(
                            endpoint_id=endpoint.id,
                            event_type=event_type,
                            payload=full_payload,
                            status_code=status_code,
                            success=(200 <= status_code < 300),
                            attempt=attempt
                        )
                        
                        self.deliveries.append(delivery)
                        
                        if delivery.success:
                            logger.info(
                                f"Webhook delivered to {endpoint.url} "
                                f"(attempt {attempt}/{endpoint.retry_count})"
                            )
                            return
                        else:
                            logger.warning(
                                f"Webhook failed with status {status_code} "
                                f"(attempt {attempt}/{endpoint.retry_count})"
                            )
            
            except asyncio.TimeoutError:
                logger.error(f"Webhook timeout to {endpoint.url} (attempt {attempt})")
            except Exception as e:
                logger.error(f"Webhook error to {endpoint.url}: {e} (attempt {attempt})")
            
            # Wait before retry (exponential backoff)
            if attempt < endpoint.retry_count:
                await asyncio.sleep(2 ** attempt)
        
        # All retries failed
        logger.error(f"Webhook delivery failed after {endpoint.retry_count} attempts")
    
    def _generate_signature(self, secret: str, payload: Dict) -> str:
        """
        Generate HMAC signature for webhook
        
        Args:
            secret: Webhook secret
            payload: Payload to sign
        
        Returns:
            HMAC signature (hex)
        """
        import json
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, secret: str, payload: Dict, signature: str) -> bool:
        """Verify webhook signature"""
        expected = self._generate_signature(secret, payload)
        return hmac.compare_digest(expected, signature)
    
    def get_delivery_logs(
        self,
        endpoint_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """
        Get webhook delivery logs
        
        Args:
            endpoint_id: Filter by endpoint (optional)
            limit: Maximum number of logs
        
        Returns:
            List of delivery logs
        """
        logs = self.deliveries
        
        if endpoint_id:
            logs = [d for d in logs if d.endpoint_id == endpoint_id]
        
        # Return most recent first
        return sorted(logs, key=lambda d: d.timestamp, reverse=True)[:limit]


# Convenience functions for common webhook events
async def notify_scan_complete(webhook_service: WebhookService, scan_data: Dict):
    """Send scan.completed webhook"""
    await webhook_service.send_webhook(
        event_type=WebhookEvent.SCAN_COMPLETED,
        payload=scan_data
    )


async def notify_critical_finding(webhook_service: WebhookService, finding: Dict):
    """Send critical.finding webhook"""
    await webhook_service.send_webhook(
        event_type=WebhookEvent.CRITICAL_FINDING,
        payload=finding
    )


async def notify_payment_success(webhook_service: WebhookService, payment: Dict):
    """Send payment.success webhook"""
    await webhook_service.send_webhook(
        event_type=WebhookEvent.PAYMENT_SUCCESS,
        payload=payment
    )
