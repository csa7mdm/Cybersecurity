"""
Slack Integration for Security Notifications

Sends alerts and scan results to Slack channels.
"""

import logging
import os
from typing import Dict, List, Optional
import aiohttp

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Slack notification service
    
    Sends formatted messages to Slack channels via webhooks.
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier
        
        Args:
            webhook_url: Slack webhook URL (or from SLACK_WEBHOOK_URL env)
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")
        
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
    
    async def send_message(
        self,
        text: str,
        blocks: Optional[List[Dict]] = None,
        channel: Optional[str] = None
    ):
        """
        Send message to Slack
        
        Args:
            text: Message text (fallback)
            blocks: Slack Block Kit blocks
            channel: Override default channel
        """
        if not self.webhook_url:
            logger.error("Cannot send Slack message: webhook URL not configured")
            return
        
        payload = {"text": text}
        
        if blocks:
            payload["blocks"] = blocks
        
        if channel:
            payload["channel"] = channel
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("Slack message sent successfully")
                    else:
                        logger.error(f"Slack API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
    
    async def notify_scan_complete(self, scan_data: Dict):
        """Send scan completion notification"""
        target = scan_data.get("target", "Unknown")
        findings_count = scan_data.get("findings_count", 0)
        critical_count = scan_data.get("critical_count", 0)
        
        # Determine color based on findings
        if critical_count > 0:
            color = "#d32f2f"  # Red
            emoji = ":rotating_light:"
        elif findings_count > 0:
            color = "#ffa726"  # Orange
            emoji = ":warning:"
        else:
            color = "#4caf50"  # Green
            emoji = ":white_check_mark:"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Scan Complete: {target}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Findings:*\n{findings_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Critical:*\n{critical_count}"
                    }
                ]
            }
        ]
        
        if scan_data.get("report_url"):
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Report"
                        },
                        "url": scan_data["report_url"],
                        "style": "primary" if critical_count > 0 else "default"
                    }
                ]
            })
        
        await self.send_message(
            text=f"Scan complete for {target}: {findings_count} findings ({critical_count} critical)",
            blocks=blocks
        )
    
    async def notify_critical_finding(self, finding: Dict):
        """Send critical finding alert"""
        title = finding.get("title", "Unknown Vulnerability")
        severity = finding.get("severity", "unknown").upper()
        cvss_score = finding.get("cvss_score", 0.0)
        url = finding.get("url", "N/A")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":rotating_light: CRITICAL: {title}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{severity}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*CVSS Score:*\n{cvss_score}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*URL:*\n{url}"
                    }
                ]
            }
        ]
        
        await self.send_message(
            text=f"CRITICAL: {title} (CVSS {cvss_score})",
            blocks=blocks
        )


class PagerDutyNotifier:
    """
    PagerDuty integration for critical alerts
    
    Creates incidents for critical findings.
    """
    
    def __init__(self, integration_key: Optional[str] = None):
        """
        Initialize PagerDuty notifier
        
        Args:
            integration_key: PagerDuty integration key
        """
        self.integration_key = integration_key or os.getenv("PAGERDUTY_INTEGRATION_KEY", "")
        self.api_url = "https://events.pagerduty.com/v2/enqueue"
    
    async def trigger_incident(
        self,
        summary: str,
        severity: str,
        details: Dict
    ):
        """
        Trigger PagerDuty incident
        
        Args:
            summary: Brief summary
            severity: critical, error, warning, info
            details: Additional details
        """
        if not self.integration_key:
            logger.error("PagerDuty integration key not configured")
            return
        
        payload = {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "payload": {
                "summary": summary,
                "severity": severity,
                "source": "CyperSecurity Platform",
                "custom_details": details
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 202:
                        logger.info("PagerDuty incident triggered")
                    else:
                        logger.error(f"PagerDuty API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to trigger PagerDuty incident: {e}")
    
    async def notify_critical_finding(self, finding: Dict):
        """Create PagerDuty incident for critical finding"""
        await self.trigger_incident(
            summary=f"Critical security finding: {finding.get('title', 'Unknown')}",
            severity="critical",
            details={
                "vulnerability": finding.get("title"),
                "cvss_score": finding.get("cvss_score"),
                "url": finding.get("url"),
                "description": finding.get("description")
            }
        )


class DiscordNotifier:
    """Discord webhook integration"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Discord notifier"""
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "")
    
    async def send_embed(
        self,
        title: str,
        description: str,
        color: int,
        fields: Optional[List[Dict]] = None
    ):
        """Send Discord embed"""
        if not self.webhook_url:
            logger.error("Discord webhook URL not configured")
            return
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": None  # Would use datetime.utcnow().isoformat()
        }
        
        if fields:
            embed["fields"] = fields
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 204]:
                        logger.info("Discord message sent")
                    else:
                        logger.error(f"Discord API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
    
    async def notify_scan_complete(self, scan_data: Dict):
        """Send scan completion to Discord"""
        target = scan_data.get("target", "Unknown")
        findings_count = scan_data.get("findings_count", 0)
        critical_count = scan_data.get("critical_count", 0)
        
        # Color based on severity
        if critical_count > 0:
            color = 0xFF0000  # Red
        elif findings_count > 0:
            color = 0xFFA500  # Orange
        else:
            color = 0x00FF00  # Green
        
        fields = [
            {"name": "Target", "value": target, "inline": True},
            {"name": "Findings", "value": str(findings_count), "inline": True},
            {"name": "Critical", "value": str(critical_count), "inline": True}
        ]
        
        await self.send_embed(
            title="🔍 Scan Complete",
            description=f"Security scan finished for **{target}**",
            color=color,
            fields=fields
        )
