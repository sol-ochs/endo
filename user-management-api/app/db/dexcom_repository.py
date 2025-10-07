import logging
from datetime import datetime, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class DexcomCredentialsRepository:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        self.table = self.dynamodb.Table(settings.DEXCOM_CREDENTIALS_TABLE)

    def create_or_update(self, user_id: str, access_token: str, refresh_token: str, expires_in: int) -> bool:
        """Create or update Dexcom credentials for a user"""
        try:
            now = datetime.now(timezone.utc)
            expires_at = datetime.fromtimestamp(now.timestamp() + expires_in, tz=timezone.utc)

            self.table.put_item(
                Item={
                    'user_id': user_id,
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_at': expires_at.isoformat(),
                    'created_at': now.isoformat(),
                    'updated_at': now.isoformat()
                }
            )
            logger.info(f"Created/updated Dexcom credentials for user {user_id}")
            return True
        except ClientError as e:
            logger.error(f"Error creating/updating Dexcom credentials: {e}")
            return False

    def get_by_user_id(self, user_id: str) -> Optional[dict]:
        """Get Dexcom credentials for a user"""
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            if 'Item' in response:
                return response['Item']
            return None
        except ClientError as e:
            logger.error(f"Error getting Dexcom credentials: {e}")
            return None

    def delete(self, user_id: str) -> bool:
        """Delete Dexcom credentials for a user"""
        try:
            self.table.delete_item(Key={'user_id': user_id})
            logger.info(f"Deleted Dexcom credentials for user {user_id}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting Dexcom credentials: {e}")
            return False

    def has_credentials(self, user_id: str) -> bool:
        """Check if user has Dexcom credentials"""
        credentials = self.get_by_user_id(user_id)
        return credentials is not None

    def update_tokens(self, user_id: str, access_token: str, refresh_token: str, expires_in: int) -> bool:
        """Update access and refresh tokens"""
        try:
            now = datetime.now(timezone.utc)
            expires_at = datetime.fromtimestamp(now.timestamp() + expires_in, tz=timezone.utc)

            self.table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET access_token = :at, refresh_token = :rt, expires_at = :ea, updated_at = :ua',
                ExpressionAttributeValues={
                    ':at': access_token,
                    ':rt': refresh_token,
                    ':ea': expires_at.isoformat(),
                    ':ua': now.isoformat()
                }
            )
            logger.info(f"Updated tokens for user {user_id}")
            return True
        except ClientError as e:
            logger.error(f"Error updating tokens: {e}")
            return False
