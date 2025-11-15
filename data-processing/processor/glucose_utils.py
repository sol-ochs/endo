"""Utility functions for glucose data processing and analysis."""
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any

from models import GlucoseReading


# Glucose range thresholds (mg/dL)
VERY_LOW_THRESHOLD = 54
LOW_THRESHOLD = 70
HIGH_THRESHOLD = 180
VERY_HIGH_THRESHOLD = 250


class GlucoseCategory(str, Enum):
    """Glucose range categories."""
    VERY_LOW = 'very_low'
    LOW = 'low'
    TARGET = 'target'
    HIGH = 'high'
    VERY_HIGH = 'very_high'


def categorize_glucose_value(value: float) -> GlucoseCategory:
    """
    Categorize a glucose value into range buckets.

    Args:
        value: Glucose value in mg/dL

    Returns:
        GlucoseCategory enum value
    """
    if value < VERY_LOW_THRESHOLD:
        return GlucoseCategory.VERY_LOW
    elif value < LOW_THRESHOLD:
        return GlucoseCategory.LOW
    elif value <= HIGH_THRESHOLD:
        return GlucoseCategory.TARGET
    elif value <= VERY_HIGH_THRESHOLD:
        return GlucoseCategory.HIGH
    else:
        return GlucoseCategory.VERY_HIGH


def calculate_aggregates(readings: List[GlucoseReading], num_days: int) -> Dict[str, Any] | None:
    """
    Calculate aggregate statistics from glucose readings.

    Args:
        readings: List of GlucoseReading objects
        num_days: Number of days with readings (for calculating expected readings)

    Returns:
        Dictionary with aggregate statistics or None if no readings:
        - avg_glucose: Average glucose value
        - time_in_range_pct: Percentage in target range (70-180)
        - cgm_active_pct: Percentage of expected readings present
        - very_high_pct, high_pct, target_pct, low_pct, very_low_pct
        - total_readings: Count of readings
    """
    if not readings:
        return None

    glucose_values = [reading.value for reading in readings]

    if not glucose_values:
        return None

    avg_glucose = sum(glucose_values) / len(glucose_values)

    category_counts = defaultdict(int)
    for value in glucose_values:
        category = categorize_glucose_value(value)
        category_counts[category] += 1

    total = len(glucose_values)

    very_low_pct = (category_counts[GlucoseCategory.VERY_LOW] / total) * 100
    low_pct = (category_counts[GlucoseCategory.LOW] / total) * 100
    target_pct = (category_counts[GlucoseCategory.TARGET] / total) * 100
    high_pct = (category_counts[GlucoseCategory.HIGH] / total) * 100
    very_high_pct = (category_counts[GlucoseCategory.VERY_HIGH] / total) * 100

    time_in_range_pct = target_pct

    # CGM active percentage (CGM reads every 5 min = 288 readings/day)
    expected_readings = num_days * 288
    cgm_active_pct = min((total / expected_readings) * 100, 100) if expected_readings > 0 else 0

    return {
        'avg_glucose': round(avg_glucose, 1),
        'time_in_range_pct': round(time_in_range_pct, 1),
        'cgm_active_pct': round(cgm_active_pct, 1),
        'very_high_pct': round(very_high_pct, 1),
        'high_pct': round(high_pct, 1),
        'target_pct': round(target_pct, 1),
        'low_pct': round(low_pct, 1),
        'very_low_pct': round(very_low_pct, 1),
        'total_readings': total
    }
