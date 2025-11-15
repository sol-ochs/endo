import json
import logging
import os
from datetime import datetime, timezone, timedelta

import boto3
import requests

from adapters import DexcomAdapter

logger = logging.getLogger()
logger.setLevel(os.environ['LOG_LEVEL'])

dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
s3 = boto3.client('s3', region_name=os.environ['AWS_REGION'])

DEXCOM_API_BASE_URL = os.environ['DEXCOM_API_BASE_URL']
DEXCOM_CLIENT_ID = os.environ['DEXCOM_CLIENT_ID']
DEXCOM_CLIENT_SECRET = os.environ['DEXCOM_CLIENT_SECRET']
DEXCOM_CREDENTIALS_TABLE = os.environ['DEXCOM_CREDENTIALS_TABLE']
S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
DEXCOM_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


def is_token_expired(credentials: dict) -> bool:
    expires_at_dt = datetime.fromisoformat(credentials['expires_at'])
    expires_at = int(expires_at_dt.timestamp())

    current_time = int(datetime.now(timezone.utc).timestamp())
    return current_time >= (expires_at - 300) # 5 minute buffer

def refresh_access_token(credentials: dict) -> str:
    url = f'{DEXCOM_API_BASE_URL}/v2/oauth2/token'
    data = {
        'client_id': DEXCOM_CLIENT_ID,
        'client_secret': DEXCOM_CLIENT_SECRET,
        'refresh_token': credentials['refresh_token'],
        'grant_type': 'refresh_token'
    }

    response = requests.post(
        url,
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    response.raise_for_status()
    token_data = response.json()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data['expires_in'])

    table = dynamodb.Table(DEXCOM_CREDENTIALS_TABLE)
    table.update_item(
        Key={'user_id': credentials['user_id']},
        UpdateExpression='SET access_token = :token, expires_at = :expires',
        ExpressionAttributeValues={
            ':token': token_data['access_token'],
            ':expires': expires_at.isoformat()
        }
    )

    logger.info(f'Token refreshed for user: {credentials["user_id"]}.')
    return token_data['access_token']

def fetch_glucose_readings(access_token: str) -> list[dict]:
    """Fetch glucose readings from Dexcom API for previous day (UTC)."""
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1))
    start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)

    url = f'{DEXCOM_API_BASE_URL}/v3/users/self/egvs'
    params = {
        'startDate': start_date.strftime(DEXCOM_DATETIME_FORMAT),
        'endDate': end_date.strftime(DEXCOM_DATETIME_FORMAT)
    }

    response = requests.get(
        url,
        params=params,
        headers={'Authorization': f'Bearer {access_token}'}
    )

    if response.status_code != 200:
        logger.error(f'Dexcom API error: {response.status_code} - {response.text}')

    response.raise_for_status()

    data = response.json()
    return data.get('records', data.get('egvs', []))

def save_to_s3(user_id: str, raw_readings: list[dict]) -> None:
    """Save glucose readings to S3 in normalized format."""
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1))
    readings_date = yesterday.strftime('%Y-%m-%d')
    ingested_at = datetime.now(timezone.utc).isoformat()

    adapter = DexcomAdapter()
    normalized_dataset = adapter.normalize_dataset(
        user_id=user_id,
        readings_date_utc=readings_date,
        ingested_at_utc=ingested_at,
        raw_readings=raw_readings
    )

    s3_key = f'normalized/user_id={user_id}/readings_date={readings_date}/readings.json'

    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(normalized_dataset.to_dict(), indent=2),
        ContentType='application/json'
    )

    logger.info(f'Saved {len(normalized_dataset.readings)} normalized readings to S3://{S3_BUCKET_NAME}/{s3_key} for user: {user_id}.')

def lambda_handler(event, context):
    """Data ingestion worker: process a single user's data ingestion request from SQS."""
    for record in event['Records']:
        message_body = json.loads(record['body'])
        user_id = message_body['user_id']

        logger.info(f'Processing data ingestion request for user: {user_id}.')

        try:
            credentials = {
                'user_id': user_id,
                'access_token': message_body['access_token'],
                'refresh_token': message_body['refresh_token'],
                'expires_at': message_body['expires_at']
            }

            access_token = credentials['access_token']
            if is_token_expired(credentials):
                logger.info(f'Token expired for user: {user_id}, refreshing...')
                access_token = refresh_access_token(credentials)

            readings = fetch_glucose_readings(access_token)

            if readings:
                save_to_s3(user_id, readings)
                logger.info(f'Successfully processed data for user: {user_id}.')
            else:
                logger.warning(f'No readings found for user: {user_id}.')
        except Exception as e:
            logger.error(f'Error processing data for user: {user_id}. Error: {str(e)}')
            raise

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Batch processed successfully'})
    }