"""Base adapter interface for CGM data sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from models import GlucoseReading, GlucoseDataset


class CGMAdapter(ABC):
    """Base adapter interface for CGM data sources."""

    @abstractmethod
    def normalize_reading(self, raw_reading: Dict[str, Any]) -> GlucoseReading:
        """Convert a single raw reading to normalized format."""
        pass

    @abstractmethod
    def normalize_dataset(self, user_id: str, readings_date_utc: str, ingested_at_utc: str, raw_readings: List[Dict[str, Any]]) -> GlucoseDataset:
        """Convert a complete dataset to normalized format."""
        pass