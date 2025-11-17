import json
import logging
import os
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

from email_template import render_weekly_report_email

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

ses = boto3.client('ses')
dynamodb = boto3.resource('dynamodb')

GLUCOSE_INSIGHTS_TABLE = os.environ['GLUCOSE_INSIGHTS_TABLE']
USERS_TABLE = os.environ['USERS_TABLE']
SENDER_EMAIL = os.environ['SENDER_EMAIL']
FRONTEND_BASE_URL = os.environ['FRONTEND_BASE_URL']


def fetch_user_info(user_id: str) -> Dict[str, Any]:
    table = dynamodb.Table(USERS_TABLE)

    try:
        response = table.get_item(Key={'user_id': user_id})
        if 'Item' not in response:
            raise ValueError(f'User {user_id} not found.')
        return response['Item']
    except Exception as e:
        logger.error(f'Error fetching user info for {user_id}: {e}')
        raise

def fetch_insights(user_id: str, report_key: str) -> Dict[str, Any]:
    table = dynamodb.Table(GLUCOSE_INSIGHTS_TABLE)

    try:
        response = table.get_item(
            Key={
                'user_id': user_id,
                'report_key': report_key
            }
        )
        if 'Item' not in response:
            raise ValueError(f'Insights not found for user {user_id}, report_key {report_key}.')
        return response['Item']
    except Exception as e:
        logger.error(f'Error fetching insights for {user_id}/{report_key}: {e}')
        raise


def send_email(recipient_email: str, subject: str, html_body: str, text_body: str) -> None:
    # Send plaintext only for MVP
    try:
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': [recipient_email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': text_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        logger.info(f'Email sent successfully. Message ID: {response["MessageId"]}.')
    except ClientError as e:
        logger.error(f'Failed to send email: {e.response["Error"]["Message"]}')
        raise

def process_email_job(user_id: str, report_key: str) -> None:
    user_info = fetch_user_info(user_id)
    first_name = user_info['first_name']
    insights_data = fetch_insights(user_id, report_key)

    recipient_email = user_info['email']

    subject, html_body, text_body = render_weekly_report_email(
        first_name=first_name,
        insights_data=insights_data,
        frontend_url=FRONTEND_BASE_URL
    )

    send_email(recipient_email, subject, html_body, text_body)
    logger.info(f'Successfully sent email to {recipient_email} for user {user_id}.')

def lambda_handler(event, context):
    """Email sender Lambda: processes SQS messages and sends emails."""
    logger.info('Starting email sender processing.')

    for record in event['Records']:
        message_body = json.loads(record['body'])
        user_id = message_body['user_id']
        report_key = message_body['report_key']

        logger.info(f'Processing email for user: {user_id}, report: {report_key}.')

        try:
            process_email_job(user_id, report_key)
            logger.info(f'Successfully processed email job for user: {user_id}.')
        except Exception as e:
            logger.error(f'Error processing email for user {user_id}: {str(e)}')
            raise  # Let SQS handle retry

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Email processing completed successfully.'})
    }
