import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date
from typing import List, Dict, Any

import boto3

from models import GlucoseReading
from glucose_utils import calculate_aggregates
from insights_generator import generate_insights

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

s3 = boto3.client('s3', region_name=os.environ['AWS_REGION'])
dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])

S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
GLUCOSE_INSIGHTS_TABLE = os.environ['GLUCOSE_INSIGHTS_TABLE']


def fetch_data_from_s3(user_id: str, days: int = 7) -> List[GlucoseReading]:
    all_readings = []

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days)

    logger.info(f'Fetching data for user {user_id} from {start_date} to {end_date}.')

    current_date = start_date
    files_found = 0

    while current_date <= end_date:
        s3_key = f'normalized/user_id={user_id}/readings_date={current_date.isoformat()}/readings.json'

        try:
            response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            data = json.loads(response['Body'].read().decode('utf-8'))

            readings = data.get('readings', [])

            for reading in readings:
                try:
                    glucose_reading = GlucoseReading(
                        timestamp_local=datetime.fromisoformat(reading['timestamp_local']),
                        value=float(reading['value']),
                        unit=reading['unit']
                    )
                    all_readings.append(glucose_reading)
                except (ValueError, AttributeError, KeyError) as e:
                    logger.warning(f"Failed to parse reading in {s3_key}: {e}")
                    continue

            files_found += 1
        except s3.exceptions.NoSuchKey:
            logger.debug(f'No data found for {current_date} (key: {s3_key}).')
        except Exception as e:
            logger.error(f'Error fetching {s3_key}: {str(e)}')
            raise

        current_date += timedelta(days=1)

    logger.info(f'Fetched total of {len(all_readings)} readings from {files_found} files for user {user_id}.')
    return all_readings

def store_insights(
    user_id: str,
    period_start_date: date,
    period_end_date: date,
    days_included: int,
    aggregates: Dict[str, Any],
    graph_data: List[Dict[str, Any]],
    insights: List[str]
) -> None:
    table = dynamodb.Table(GLUCOSE_INSIGHTS_TABLE)

    period_end_str = period_end_date.isoformat()
    report_key = f'{period_end_str}#weekly'

    item = {
        'user_id': user_id,
        'report_key': report_key,
        'period_start': period_start_date.isoformat(),
        'period_end': period_end_date.isoformat(),
        'days_included': days_included,
        'aggregates': aggregates,
        'graph_data': graph_data,
        'insights': insights,
        'insights_version': 'template-v1',  # Used by email service
        'created_at': datetime.now(timezone.utc).isoformat(),
        'report_type': 'weekly'
    }

    table.put_item(Item=item)
    logger.info(f'Stored insights for user {user_id}, report_key: {report_key} ({days_included} days)')

def fetch_previous_week_aggregates(user_id: str, current_period_end: date) -> Dict[str, Any] | None:
    """Fetch previous week's aggregates from DynamoDB for trend comparison."""
    table = dynamodb.Table(GLUCOSE_INSIGHTS_TABLE)

    # Calculate previous week's end date (7 days before current week's end)
    previous_period_end = current_period_end - timedelta(days=7)
    previous_report_key = f'{previous_period_end.isoformat()}#weekly'

    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'report_key': previous_report_key
            }
        )
        if 'Item' in response:
            return response['Item'].get('aggregates')
        return None
    except Exception as e:
        logger.warning(f'Could not fetch previous week aggregates for user {user_id}: {e}')
        return None


def process_user_data(user_id: str) -> None:
    readings = fetch_data_from_s3(user_id, days=7)

    if not readings:
        raise ValueError(f'No readings found for user {user_id}. Cannot generate insights.')

    logger.info(f'Processing {len(readings)} readings for user {user_id}')

    # Get date range from readings
    timestamps = [r.timestamp_local for r in readings if isinstance(r.timestamp_local, datetime)]
    period_start_date = min(timestamps).date()
    period_end_date = max(timestamps).date()
    num_days = (period_end_date - period_start_date).days + 1

    aggregates = calculate_aggregates(readings, num_days)

    graph_data = [{'timestamp': r.timestamp_local.isoformat(), 'value': r.value} for r in readings]

    # Fetch previous week's data for trend comparison
    previous_aggregates = fetch_previous_week_aggregates(user_id, period_end_date)

    insights = generate_insights(aggregates, period_start_date, period_end_date, previous_aggregates)

    store_insights(
        user_id=user_id,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
        days_included=num_days,
        aggregates=aggregates,
        graph_data=graph_data,
        insights=insights
    )

def lambda_handler(event, context):
    """Data processing worker: processes a single user's data from S3 and saves insights to DynamoDB."""
    logger.info('Starting glucose data processing.')

    for record in event['Records']:
        message_body = json.loads(record['body'])
        user_id = message_body['user_id']

        logger.info(f'Processing data for user: {user_id}.')

        try:
            process_user_data(user_id)
            logger.info(f'Successfully processed data for user: {user_id}.')
        except Exception as e:
            logger.error(f'Error processing user {user_id}: {str(e)}')
            raise  # Let SQS handle retry

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Processing completed successfully.'})
    }