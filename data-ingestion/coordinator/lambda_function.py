import json
import logging
import os

import boto3

DEXCOM_CREDENTIALS_TABLE = os.environ['DEXCOM_CREDENTIALS_TABLE']
USERS_TABLE = os.environ['USERS_TABLE']
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']

logger = logging.getLogger()
logger.setLevel(os.environ['LOG_LEVEL'])

dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
sqs = boto3.client('sqs', region_name=os.environ['AWS_REGION'])


def lambda_handler(event, context):
    """Data ingestion coordinator: get all active users with Dexcom credentials and enqueue them."""
    logger.info('Starting data ingestion coordinator: Scanning for active users.')

    users_table = dynamodb.Table(USERS_TABLE)
    dexcom_table = dynamodb.Table(DEXCOM_CREDENTIALS_TABLE)

    # Scan users table for active users
    response = users_table.scan(
        FilterExpression='is_active = :active',
        ExpressionAttributeValues={':active': True}
    )
    active_users = response.get('Items', [])

    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = users_table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey'],
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )
        active_users.extend(response.get('Items', []))

    logger.info(f'Found {len(active_users)} active users.')

    enqueued_count = 0
    failed_count = 0
    skipped_count = 0

    for user in active_users:
        user_id = user['user_id']

        # Check if user has Dexcom credentials
        try:
            dexcom_response = dexcom_table.get_item(Key={'user_id': user_id})
            if 'Item' not in dexcom_response:
                logger.debug(f'User {user_id} has no Dexcom credentials, skipping.')
                skipped_count += 1
                continue

            dexcom_creds = dexcom_response['Item']
        except Exception as e:
            logger.error(f'Failed to get Dexcom credentials for user {user_id}: {str(e)}')
            failed_count += 1
            continue

        # Enqueue active user with Dexcom credentials
        try:
            sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps({
                    'user_id': user_id,
                    'access_token': dexcom_creds['access_token'],
                    'refresh_token': dexcom_creds['refresh_token'],
                    'expires_at': dexcom_creds['expires_at']
                })
            )
            enqueued_count += 1
        except Exception as e:
            logger.error(f'Failed to enqueue user {user_id}: {str(e)}')
            failed_count += 1

    result = {
        'total_active_users': len(active_users),
        'enqueued': enqueued_count,
        'skipped': skipped_count,
        'failed': failed_count
    }

    logger.info(f'Data ingestion coordinator completed: {result}')

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }