"""Insights generation for glucose data."""
from datetime import date
from typing import Dict, Any, List

# Thresholds for significant week-over-week changes
SIGNIFICANT_CHANGE_MGDL = 10  # mg/dL
SIGNIFICANT_CHANGE_PCT = 5     # percentage points


def generate_insights(
    aggregates: Dict[str, Any],
    period_start: date,
    period_end: date,
    previous_aggregates: Dict[str, Any] | None = None
) -> List[str]:
    """
    Generate insights from glucose aggregates, showing changes from previous week if available.

    Args:
        aggregates: Current week's aggregate statistics
        period_start: Start date of current period
        period_end: End date of current period
        previous_aggregates: Previous week's aggregates (optional)

    Returns:
        List of insight strings for email service to format
    """
    insights = []

    num_days = (period_end - period_start).days + 1
    header = f'Glucose summary for {period_start.isoformat()} through {period_end.isoformat()} ({num_days} days)'
    insights.append(header)

    metrics_insights = _generate_metric_insights(aggregates, previous_aggregates)
    insights.extend(metrics_insights)

    return insights

def _generate_metric_insights(current: Dict[str, Any], previous: Dict[str, Any] | None) -> List[str]:
    """Generate insights for each metric, showing changes if previous data exists."""
    insights = []

    # Average glucose
    insights.append(_format_mgdl_metric("Average glucose", current['avg_glucose'], previous.get('avg_glucose') if previous else None))

    # Time-in-range
    insights.append(_format_pct_metric("Time in range (70-180)", current['time_in_range_pct'], previous.get('time_in_range_pct') if previous else None))

    # CGM active
    insights.append(_format_pct_metric("CGM active", current['cgm_active_pct'], previous.get('cgm_active_pct') if previous else None))

    # Range breakdown
    insights.append(_format_pct_metric("Very high (>250)", current['very_high_pct'], previous.get('very_high_pct') if previous else None))
    insights.append(_format_pct_metric("High (180-250)", current['high_pct'], previous.get('high_pct') if previous else None))
    insights.append(_format_pct_metric("Target (70-180)", current['target_pct'], previous.get('target_pct') if previous else None))
    insights.append(_format_pct_metric("Low (54-70)", current['low_pct'], previous.get('low_pct') if previous else None))
    insights.append(_format_pct_metric("Very low (<54)", current['very_low_pct'], previous.get('very_low_pct') if previous else None))

    return insights

def _format_mgdl_metric(label: str, value: float, previous_value: float | None) -> str:
    """Format mg/dL metric with optional change indicator."""
    formatted = f"{label}: {value} mg/dL"

    if previous_value is not None:
        delta = value - previous_value
        if abs(delta) >= SIGNIFICANT_CHANGE_MGDL:
            direction = "↑" if delta > 0 else "↓"
            formatted += f" ({direction}{abs(delta):.1f} from last week)"

    return formatted

def _format_pct_metric(label: str, value: float, previous_value: float | None) -> str:
    """Format percentage metric with optional change indicator."""
    formatted = f"{label}: {value}%"

    if previous_value is not None:
        delta = value - previous_value
        if abs(delta) >= SIGNIFICANT_CHANGE_PCT:
            direction = "↑" if delta > 0 else "↓"
            formatted += f" ({direction}{abs(delta):.1f} from last week)"

    return formatted
