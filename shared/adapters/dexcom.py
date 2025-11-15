import logging
from typing import List, Dict, Any

from models import GlucoseReading, GlucoseDataset
from .base import CGMAdapter

logger = logging.getLogger(__name__)


class DexcomAdapter(CGMAdapter):
    """Adapter for Dexcom API v3 data format."""

    API_VERSION = "v3"

    def normalize_reading(self, raw_reading: Dict[str, Any]) -> GlucoseReading:
        """
        Convert Dexcom API reading to normalized format.

        Dexcom format:
        {
            "systemTime": "2025-01-13T13:00:00",
            "displayTime": "2025-01-13T08:00:00",
            "value": 120,
            "trend": "flat",
            "trendRate": 0.5
        }
        """

        return GlucoseReading(
            timestamp_local=raw_reading['displayTime'],
            value=float(raw_reading['value']),
            unit='mg/dL'
        )

    def normalize_dataset(self, user_id: str, readings_date_utc: str, ingested_at_utc: str, raw_readings: List[Dict[str, Any]]) -> GlucoseDataset:
        """
        Convert Dexcom dataset to normalized format.

        Fails gracefully: skips malformed individual readings but continues processing.
        Fails fast: raises exception if ALL readings are malformed or invalid.

        Raises:
            ValueError: If no readings could be successfully normalized
        """
        if not raw_readings:
            raise ValueError(f"No raw readings provided for user {user_id}")

        normalized_readings = []
        skipped_count = 0
        error_count = 0

        for idx, raw_reading in enumerate(raw_readings):
            try:
                # Validate required fields
                if 'displayTime' not in raw_reading:
                    logger.warning(f"User {user_id}: Skipping reading {idx}: missing 'displayTime' field")
                    skipped_count += 1
                    continue

                if 'value' not in raw_reading:
                    logger.warning(f"User {user_id}: Skipping reading {idx}: missing 'value' field")
                    skipped_count += 1
                    continue

                if raw_reading['value'] is None:
                    logger.debug(f"User {user_id}: Skipping reading {idx}: null value")
                    skipped_count += 1
                    continue

                # Attempt normalization
                normalized_reading = self.normalize_reading(raw_reading)
                normalized_readings.append(normalized_reading)

            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"User {user_id}: Failed to normalize reading {idx}: {type(e).__name__}: {e}")
                error_count += 1
                continue
            except Exception as e:
                logger.error(f"User {user_id}: Unexpected error normalizing reading {idx}: {type(e).__name__}: {e}")
                error_count += 1
                continue

        # Log summary
        total_processed = len(raw_readings)
        success_count = len(normalized_readings)
        logger.info(
            f"User {user_id}: Normalization complete. "
            f"Total: {total_processed}, Success: {success_count}, "
            f"Skipped: {skipped_count}, Errors: {error_count}"
        )

        # Fail fast if no readings were successfully normalized
        if not normalized_readings:
            raise ValueError(
                f"Failed to normalize any readings for user {user_id}. "
                f"Total raw readings: {total_processed}, "
                f"Skipped: {skipped_count}, Errors: {error_count}"
            )

        # Warn if significant data loss (>50% failed)
        failure_rate = (skipped_count + error_count) / total_processed
        if failure_rate > 0.5:
            logger.warning(
                f"User {user_id}: High failure rate during normalization: "
                f"{failure_rate*100:.1f}% of readings failed. "
                f"This may indicate a data format change."
            )

        return GlucoseDataset(
            user_id=user_id,
            readings_date_utc=readings_date_utc,
            ingested_at_utc=ingested_at_utc,
            readings=normalized_readings,
            source='dexcom',
            source_version=self.API_VERSION
        )
