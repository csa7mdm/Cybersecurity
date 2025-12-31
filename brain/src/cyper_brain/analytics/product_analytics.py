"""
Product Analytics Service

Tracks user behavior, product usage, and engagement metrics.
"""

import logging
import time
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from enum import Enum
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EventCategory(Enum):
    """Analytics event categories"""
    USER = "user"
    SCAN = "scan"
    BILLING = "billing"
    INTEGRATION = "integration"
    REPORT = "report"
    TEAM = "team"


@dataclass
class AnalyticsEvent:
    """Analytics event"""
    user_id: str
    event_name: str
    category: EventCategory
    properties: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission"""
        return {
            "user_id": self.user_id,
            "event_name": self.event_name,
            "category": self.category.value,
            "properties": self.properties,
            "timestamp": self.timestamp,
            "session_id": self.session_id
        }


class AnalyticsService:
    """
    Product analytics service
    
    Tracks user behavior and product usage for insights and optimization.
    Compatible with Amplitude, Mixpanel, or custom backend.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize analytics service
        
        Args:
            api_key: Analytics platform API key (optional)
        """
        self.api_key = api_key or os.getenv("ANALYTICS_API_KEY", "")
        self.events: List[AnalyticsEvent] = []  # In-memory storage (use DB in prod)
        self.enabled = bool(self.api_key) or os.getenv("ANALYTICS_ENABLED", "true").lower() == "true"
    
    def track(
        self,
        user_id: str,
        event_name: str,
        category: EventCategory,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """
        Track an analytics event
        
        Args:
            user_id: User ID
            event_name: Event name (e.g., "scan_created")
            category: Event category
            properties: Additional event properties
            session_id: Session identifier
        """
        if not self.enabled:
            logger.debug(f"Analytics disabled, skipping event: {event_name}")
            return
        
        event = AnalyticsEvent(
            user_id=user_id,
            event_name=event_name,
            category=category,
            properties=properties or {},
            session_id=session_id
        )
        
        self.events.append(event)
        logger.info(f"Tracked event: {event_name} for user {user_id}")
        
        # In production, send to analytics platform
        # self._send_to_platform(event)
    
    def identify(
        self,
        user_id: str,
        traits: Dict[str, Any]
    ):
        """
        Identify user with traits
        
        Args:
            user_id: User ID
            traits: User traits (email, name, plan, etc.)
        """
        if not self.enabled:
            return
        
        self.track(
            user_id=user_id,
            event_name="user_identified",
            category=EventCategory.USER,
            properties={"traits": traits}
        )
    
    def get_user_events(
        self,
        user_id: str,
        category: Optional[EventCategory] = None,
        limit: int = 100
    ) -> List[AnalyticsEvent]:
        """
        Get events for a user
        
        Args:
            user_id: User ID
            category: Filter by category (optional)
            limit: Maximum events to return
        
        Returns:
            List of events
        """
        events = [e for e in self.events if e.user_id == user_id]
        
        if category:
            events = [e for e in events if e.category == category]
        
        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_event_count(
        self,
        event_name: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> int:
        """
        Get count of specific event
        
        Args:
            event_name: Event name
            start_time: Start timestamp (optional)
            end_time: End timestamp (optional)
        
        Returns:
            Event count
        """
        events = [e for e in self.events if e.event_name == event_name]
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        return len(events)


class MetricsCollector:
    """
    Collects and aggregates product metrics
    
    Calculates KPIs like DAU, WAU, MAU, retention, etc.
    """
    
    def __init__(self, analytics_service: AnalyticsService):
        """Initialize metrics collector"""
        self.analytics = analytics_service
    
    def get_daily_active_users(self, date: datetime) -> int:
        """
        Get Daily Active Users (DAU)
        
        Args:
            date: Date to calculate for
        
        Returns:
            Number of unique active users
        """
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        start_ts = start.timestamp()
        end_ts = end.timestamp()
        
        # Get unique users who had any activity
        active_events = [
            e for e in self.analytics.events
            if start_ts <= e.timestamp < end_ts
        ]
        
        unique_users = set(e.user_id for e in active_events)
        return len(unique_users)
    
    def get_weekly_active_users(self, date: datetime) -> int:
        """Get Weekly Active Users (WAU)"""
        start = date - timedelta(days=7)
        end = date
        
        start_ts = start.timestamp()
        end_ts = end.timestamp()
        
        active_events = [
            e for e in self.analytics.events
            if start_ts <= e.timestamp < end_ts
        ]
        
        unique_users = set(e.user_id for e in active_events)
        return len(unique_users)
    
    def get_monthly_active_users(self, date: datetime) -> int:
        """Get Monthly Active Users (MAU)"""
        start = date - timedelta(days=30)
        end = date
        
        start_ts = start.timestamp()
        end_ts = end.timestamp()
        
        active_events = [
            e for e in self.analytics.events
            if start_ts <= e.timestamp < end_ts
        ]
        
        unique_users = set(e.user_id for e in active_events)
        return len(unique_users)
    
    def get_conversion_funnel(
        self,
        steps: List[str],
        start_time: Optional[float] = None
    ) -> Dict[str, int]:
        """
        Calculate conversion funnel
        
        Args:
            steps: List of event names in order
            start_time: Start time for analysis
        
        Returns:
            Dict with counts for each step
        """
        funnel = {}
        
        for i, step in enumerate(steps):
            events = [
                e for e in self.analytics.events
                if e.event_name == step
            ]
            
            if start_time:
                events = [e for e in events if e.timestamp >= start_time]
            
            unique_users = set(e.user_id for e in events)
            funnel[step] = len(unique_users)
        
        return funnel
    
    def get_retention_cohort(
        self,
        cohort_start: datetime,
        cohort_end: datetime,
        retention_days: int = 7
    ) -> float:
        """
        Calculate retention rate for cohort
        
        Args:
            cohort_start: Cohort start date
            cohort_end: Cohort end date
            retention_days: Days to check retention
        
        Returns:
            Retention rate (0.0-1.0)
        """
        # Get users who signed up in cohort period
        cohort_users = set()
        for event in self.analytics.events:
            if (event.event_name == "user_signed_up" and
                cohort_start.timestamp() <= event.timestamp < cohort_end.timestamp()):
                cohort_users.add(event.user_id)
        
        if not cohort_users:
            return 0.0
        
        # Check how many returned after retention_days
        retention_start = cohort_end + timedelta(days=retention_days)
        retention_end = retention_start + timedelta(days=1)
        
        retained_users = set()
        for event in self.analytics.events:
            if (event.user_id in cohort_users and
                retention_start.timestamp() <= event.timestamp < retention_end.timestamp()):
                retained_users.add(event.user_id)
        
        return len(retained_users) / len(cohort_users)
    
    def get_feature_adoption(
        self,
        feature_event: str,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate feature adoption metrics
        
        Args:
            feature_event: Event name for feature usage
            time_period_days: Period to analyze
        
        Returns:
            Adoption metrics
        """
        now = datetime.now()
        start = now - timedelta(days=time_period_days)
        
        # Get total users in period
        all_events = [
            e for e in self.analytics.events
            if start.timestamp() <= e.timestamp
        ]
        total_users = len(set(e.user_id for e in all_events))
        
        # Get users who used feature
        feature_events = [
            e for e in all_events
            if e.event_name == feature_event
        ]
        feature_users = len(set(e.user_id for e in feature_events))
        
        adoption_rate = feature_users / total_users if total_users > 0 else 0
        
        return {
            "total_users": total_users,
            "feature_users": feature_users,
            "adoption_rate": adoption_rate,
            "total_uses": len(feature_events)
        }


# Convenience functions for common events
def track_user_signup(analytics: AnalyticsService, user_id: str, properties: Dict):
    """Track user signup"""
    analytics.track(
        user_id=user_id,
        event_name="user_signed_up",
        category=EventCategory.USER,
        properties=properties
    )


def track_scan_created(analytics: AnalyticsService, user_id: str, scan_type: str):
    """Track scan creation"""
    analytics.track(
        user_id=user_id,
        event_name="scan_created",
        category=EventCategory.SCAN,
        properties={"scan_type": scan_type}
    )


def track_scan_completed(analytics: AnalyticsService, user_id: str, scan_data: Dict):
    """Track scan completion"""
    analytics.track(
        user_id=user_id,
        event_name="scan_completed",
        category=EventCategory.SCAN,
        properties=scan_data
    )


def track_subscription_created(analytics: AnalyticsService, user_id: str, plan: str):
    """Track subscription"""
    analytics.track(
        user_id=user_id,
        event_name="subscription_created",
        category=EventCategory.BILLING,
        properties={"plan": plan}
    )


def track_integration_connected(analytics: AnalyticsService, user_id: str, integration: str):
    """Track integration connection"""
    analytics.track(
        user_id=user_id,
        event_name="integration_connected",
        category=EventCategory.INTEGRATION,
        properties={"integration": integration}
    )
