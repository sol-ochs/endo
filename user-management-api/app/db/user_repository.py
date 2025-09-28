import logging

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from pydantic import ValidationError

from app.core.config import settings
from app.db.models.database_models import DBUser


logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db_resource):
        self._users_table = db_resource.Table(settings.USERS_TABLE)

    def create(self, user_data: dict) -> str | None:
        """Creates a new user in the database."""
        try:
            user = DBUser(**user_data)
            self._users_table.put_item(Item=user.model_dump(by_alias=True))
            return user.id
        except ValidationError as e:
            logger.error(f"Error validating user data: {e}")
            return None
        except ClientError as e:
            logger.error(f"Error saving new user to database: {e}")
            return None

    def get_by_id(self, user_id: str) -> dict | None:
        """Fetches a user by user ID."""
        try:
            logger.info(f"Fetching user_id: {user_id}")
            response = self._users_table.get_item(Key={'user_id': user_id})
            if 'Item' not in response:
                logger.warning(f"User not found for user_id: {user_id}")
                return None
            user = DBUser(**response['Item'])
            return user.model_dump()
        except ValidationError as e:
            logger.error(f"Error validating data returned for user_id: {user_id}. Error: {e}")
            return None
        except ClientError as e:
            logger.error(f"Error fetching user_id: {user_id}. Error: {e}")
            return None

    def get_by_email(self, email: str) -> dict | None:
        """Fetches a user by email address."""
        try:
            logger.info(f"Fetching user for email: {email}")
            response = self._users_table.query(
                IndexName='email-index',
                KeyConditionExpression=Key('email').eq(email)
            )
            if 'Items' not in response or len(response['Items']) == 0:
                logger.debug(f"User not found for email: {email}")
                return None
            user = DBUser(**response['Items'][0])
            return user.model_dump()
        except ValidationError as e:
            logger.error(f"Error validating data returned for user with email: {email}. Error: {e}")
            return None
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.debug(f"Table not found when fetching user by email: {email}")
                return None
            else:
                logger.error(f"Error fetching user by email: {email}. Error: {e}")
                return None

    def update_profile(self, user_id: str, updates: dict) -> bool:
        """Updates specific user profile fields."""
        try:
            logger.info(f"Updating user_id: {user_id}. Fields: {list(updates.keys())}")

            if not updates:
                logger.warning(f"No updates provided for user_id: {user_id}")
                return False

            update_expression_parts = []
            expression_values = {}

            if "first_name" in updates:
                update_expression_parts.append("first_name = :fn")
                expression_values[":fn"] = updates["first_name"]
            if "last_name" in updates:
                update_expression_parts.append("last_name = :ln")
                expression_values[":ln"] = updates["last_name"]
            if "email" in updates:
                update_expression_parts.append("email = :em")
                expression_values[":em"] = updates["email"]

            self._users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=f"SET {', '.join(update_expression_parts)}",
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError as e:
            logger.error(f"Error updating user_id: {user_id}. Error: {e}")
            return False

    def update_last_login(self, user_id: str, last_login: str) -> bool:
        """Updates the last login timestamp for a user."""
        try:
            logger.info(f"Updating last login for user_id: {user_id}")
            self._users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression="SET last_login = :ll",
                ExpressionAttributeValues={':ll': last_login}
            )
            return True
        except ClientError as e:
            logger.error(f"Error updating last login for user_id: {user_id}. Error: {e}")
            return False

    def update_password(self, user_id: str, new_password_hash: str) -> bool:
        """Updates user password."""
        try:
            logger.info(f"Updating password for user_id: {user_id}")
            self._users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression="SET password = :pw",
                ExpressionAttributeValues={':pw': new_password_hash}
            )
            return True
        except ClientError as e:
            logger.error(f"Error updating password for user_id: {user_id}. Error: {e}")
            return False

    def deactivate(self, user_id: str) -> bool:
        """Deactivates a user by setting is_active to False."""
        try:
            logger.info(f"Deactivating user_id: {user_id}")
            self._users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression="SET is_active = :ia",
                ExpressionAttributeValues={':ia': False}
            )
            return True
        except ClientError as e:
            logger.error(f"Error deactivating user_id: {user_id}. Error: {e}")
            return False