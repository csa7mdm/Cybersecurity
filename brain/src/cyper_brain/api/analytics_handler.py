"""
Analytics Dashboard API

Provides endpoints for viewing analytics and metrics.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from cyper_brain.analytics import AnalyticsService, MetricsCollector

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Global instances (in production, use dependency injection)
analytics_service = AnalyticsService()
metrics_collector = MetricsCollector(analytics_service)


@router.get("/metrics/overview")
async def get_metrics_overview():
    """
    Get overview metrics (DAU, WAU, MAU)
    """
    today = datetime.now()
    
    dau = metrics_collector.get_daily_active_users(today)
    wau = metrics_collector.get_weekly_active_users(today)
    mau = metrics_collector.get_monthly_active_users(today)
    
    return {
        "daily_active_users": dau,
        "weekly_active_users": wau,
        "monthly_active_users": mau,
        "stickiness": round(dau / mau, 2) if mau > 0 else 0
    }


@router.get("/metrics/funnel")
async def get_conversion_funnel():
    """
    Get signup to paid conversion funnel
    """
    steps = [
        "user_signed_up",
        "email_verified",
        "onboarding_completed",
        "first_scan_created",
        "subscription_created"
    ]
    
    funnel = metrics_collector.get_conversion_funnel(steps)
    
    # Calculate conversion rates
    conversions = {}
    for i, step in enumerate(steps):
        count = funnel.get(step, 0)
        conversions[step] = {
            "count": count,
            "percentage": 100.0 if i == 0 else (
                round(count / funnel[steps[0]] * 100, 1) if funnel[steps[0]] > 0 else 0
            )
        }
    
    return {
        "funnel": conversions,
        "steps": steps
    }


@router.get("/metrics/retention")
async def get_retention_metrics():
    """
    Get 7-day and 30-day retention rates
    """
    today = datetime.now()
    
    # Calculate retention for last week's cohort
    cohort_start = today - timedelta(days=7)
    cohort_end = today - timedelta(days=6)
    
    retention_7d = metrics_collector.get_retention_cohort(
        cohort_start=cohort_start,
        cohort_end=cohort_end,
        retention_days=7
    )
    
    # Calculate retention for last month's cohort
    cohort_start_30 = today - timedelta(days=30)
    cohort_end_30 = today - timedelta(days=29)
    
    retention_30d = metrics_collector.get_retention_cohort(
        cohort_start=cohort_start_30,
        cohort_end=cohort_end_30,
        retention_days=30
    )
    
    return {
        "retention_7_day": round(retention_7d * 100, 1),
        "retention_30_day": round(retention_30d * 100, 1)
    }


@router.get("/metrics/features")
async def get_feature_adoption():
    """
    Get feature adoption metrics
    """
    features = {
        "webhooks": "webhook_created",
        "slack_integration": "integration_connected",
        "team_collaboration": "team_member_invited",
        "pdf_reports": "report_generated"
    }
    
    adoption = {}
    for feature_name, event_name in features.items():
        metrics = metrics_collector.get_feature_adoption(
            feature_event=event_name,
            time_period_days=30
        )
        adoption[feature_name] = {
            "adoption_rate": round(metrics["adoption_rate"] * 100, 1),
            "total_uses": metrics["total_uses"]
        }
    
    return adoption


@router.get("/events/user/{user_id}")
async def get_user_events(
    user_id: str,
    category: Optional[str] = None,
    limit: int = 50
):
    """
    Get events for a specific user
    """
    from cyper_brain.analytics import EventCategory
    
    cat = EventCategory(category) if category else None
    events = analytics_service.get_user_events(
        user_id=user_id,
        category=cat,
        limit=limit
    )
    
    return {
        "user_id": user_id,
        "events": [e.to_dict() for e in events],
        "count": len(events)
    }


@router.get("/events/top")
async def get_top_events(days: int = 7, limit: int = 10):
    """
    Get most common events in time period
    """
    cutoff = (datetime.now() - timedelta(days=days)).timestamp()
    
    recent_events = [
        e for e in analytics_service.events
        if e.timestamp >= cutoff
    ]
    
    # Count events by name
    event_counts = {}
    for event in recent_events:
        event_counts[event.event_name] = event_counts.get(event.event_name, 0) + 1
    
    # Sort by count
    top_events = sorted(
        event_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return {
        "period_days": days,
        "top_events": [
            {"event_name": name, "count": count}
            for name, count in top_events
        ]
    }


@router.post("/track")
async def track_event(
    user_id: str,
    event_name: str,
    category: str,
    properties: Optional[dict] = None
):
    """
    Track a custom event
    """
    from cyper_brain.analytics import EventCategory
    
    try:
        cat = EventCategory(category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    analytics_service.track(
        user_id=user_id,
        event_name=event_name,
        category=cat,
        properties=properties or {}
    )
    
    return {"status": "tracked", "event_name": event_name}
