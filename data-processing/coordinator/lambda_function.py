import json
import logging
import os
from typing import List

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
sqs = boto3.client('sqs', region_name=os.environ['AWS_REGION'])

USERS_TABLE = os.environ['USERS_TABLE']
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']


def get_active_users() -> List[str]:
    table = dynamodb.Table(USERS_TABLE)
    users = []

    try:
        response = table.scan(
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )
        users.extend([item['user_id'] for item in response.get('Items', [])])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='is_active = :active',
                ExpressionAttributeValues={':active': True},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            users.extend([item['user_id'] for item in response.get('Items', [])])

        logger.info(f'Found {len(users)} active users.')

        return users

    except Exception as e:
        logger.error(f'Error scanning users table: {str(e)}')
        raise

def enqueue_user(user_id: str) -> None:
    message_body = json.dumps({'user_id': user_id})

    try:
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message_body
        )
        logger.debug(f'Enqueued user: {user_id}.')
    except Exception as e:
        logger.error(f'Error enqueuing user {user_id}: {str(e)}')
        raise


def lambda_handler(event, context):
    """
    Data processing coordinator: enqueue all active users for processing.
    """
    logger.info('Starting data processing coordination.')

    users = get_active_users()

    if not users:
        logger.warning('No active users found.')
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No active users to process.'})
        }

    enqueued_count = 0
    error_count = 0

    for user_id in users:
        try:
            enqueue_user(user_id)
            enqueued_count += 1
        except Exception as e:
            logger.error(f'Failed to enqueue user {user_id}: {str(e)}')
            error_count += 1

    logger.info(f'Coordination complete. Enqueued: {enqueued_count}, errors: {error_count}.')

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Coordination complete.',
            'users_enqueued': enqueued_count,
            'errors': error_count
        })
    }
