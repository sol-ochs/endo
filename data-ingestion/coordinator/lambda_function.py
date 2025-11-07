import json
import logging
import os

import boto3

DEXCOM_CREDENTIALS_TABLE = os.environ['DEXCOM_CREDENTIALS_TABLE']
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']

logger = logging.getLogger()
logger.setLevel(os.environ['LOG_LEVEL'])

dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
sqs = boto3.client('sqs', region_name=os.environ['AWS_REGION'])


def lambda_handler(event, context):
    """Data ingestion coordinator: get all users and enqueue them for ingestion."""
    logger.info('Starting data ingestion coordinator: Scanning for users with Dexcom credentials.')

    table = dynamodb.Table(DEXCOM_CREDENTIALS_TABLE)
    response = table.scan()
    users = response.get('Items', [])

    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        users.extend(response.get('Items', []))

    logger.info(f'Found {len(users)} users with Dexcom credentials.')

    enqueued_count = 0
    failed_count = 0

    for user in users:
        user_id = user['user_id']
        try:
            sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps({
                    'user_id': user_id,
                    'access_token': user['access_token'],
                    'refresh_token': user['refresh_token'],
                    'expires_at': user['expires_at']
                })
            )
            enqueued_count += 1
        except Exception as e:
            logger.error(f'Failed to enqueue user {user_id}: {str(e)}')
            failed_count += 1

    result = {
        'total_users': len(users),
        'enqueued': enqueued_count,
        'failed': failed_count
    }

    logger.info(f'Data ingestion coordinator completed: {result}')

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }