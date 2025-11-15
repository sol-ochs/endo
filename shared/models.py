from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Union


@dataclass
class GlucoseReading:
    """Normalized glucose reading format."""
    timestamp_local: Union[str, datetime]  # ISO8601 string or datetime object (user's local time)
    value: float                            # Glucose value in mg/dL
    unit: str = "mg/dL"

    def to_dict(self) -> Dict[str, Any]:
        timestamp = self.timestamp_local
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()

        return {
            'timestamp': timestamp,
            'value': self.value,
            'unit': self.unit
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlucoseReading':
        return cls(
            timestamp_local=data['timestamp'],
            value=float(data['value']),
            unit=data.get('unit', 'mg/dL')
        )

@dataclass
class GlucoseDataset:
    """User glucose reading dataset with metadata."""
    user_id: str
    readings_date_utc: str   # YYYY-MM-DD format - date of the readings (UTC)
    ingested_at_utc: str     # ISO8601 timestamp - when data was fetched from source
    readings: List[GlucoseReading]
    source: str              # e.g., "dexcom", "libre", "guardian"
    source_version: str      # API version or data format version

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'readings_date_utc': self.readings_date_utc,
            'ingested_at_utc': self.ingested_at_utc,
            'readings': [r.to_dict() for r in self.readings],
            'metadata': {
                'total_readings': len(self.readings),
                'source': self.source,
                'source_version': self.source_version
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlucoseDataset':
        metadata = data.get('metadata', {})
        readings = [GlucoseReading.from_dict(r) for r in data.get('readings', [])]

        return cls(
            user_id=data['user_id'],
            readings_date_utc=data['readings_date_utc'],
            ingested_at_utc=data['ingested_at_utc'],
            readings=readings,
            source=metadata.get('source', 'unknown'),
            source_version=metadata.get('source_version', 'unknown')
        )
