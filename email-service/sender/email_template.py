"""
Simple plaintext email templates for Endo weekly reports (MVP).
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Tuple


def format_date(date_str: str) -> str:
    """Format ISO date string to human-readable format."""
    try:
        date_obj = datetime.fromisoformat(date_str)
        return date_obj.strftime('%B %d, %Y')
    except (ValueError, AttributeError):
        return date_str

def format_percent(value: float | Decimal) -> str:
    """Format decimal to percentage string."""
    if isinstance(value, Decimal):
        value = float(value)
    return f"{value:.1f}%"

def format_glucose(value: float | Decimal, unit: str = 'mg/dL') -> str:
    """Format glucose value with unit."""
    if isinstance(value, Decimal):
        value = float(value)
    return f"{value:.0f} {unit}"

def render_weekly_report_email(first_name: str, insights_data: Dict[str, Any], frontend_url: str) -> Tuple[str, str, str]:
    """
    Render weekly report email template (plaintext only for MVP).

    Returns:
        Tuple of (subject, html_body, text_body)
    """
    aggregates = insights_data.get('aggregates', {})
    insights = insights_data.get('insights', [])
    period_start = format_date(insights_data['period_start'])
    period_end = format_date(insights_data['period_end'])

    subject = f"Your Weekly Glucose Report - {period_end}"

    # Plain text email
    text_body = f"""
Endo - Your Weekly Glucose Report

Hi {first_name},

Here's your glucose summary for {period_start} to {period_end}.

KEY METRICS
-----------
Average Glucose: {format_glucose(aggregates.get('average_glucose', 0))}
Time in Range: {format_percent(aggregates.get('time_in_range', 0))}
GMI: {aggregates.get('gmi', 0):.1f}%

KEY INSIGHTS
------------
{chr(10).join([f"• {insight}" for insight in insights])}

---
You're receiving this because you signed up for Endo weekly reports.
Update your preferences: {frontend_url}/settings
"""

    return subject, "", text_body  # No HTML for MVP
