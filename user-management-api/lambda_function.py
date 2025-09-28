from app.main import handler
from app.dynamodb_repository import DynamoDBRepository


db = DynamoDBRepository()

def lambda_handler(event, context):
    return handler(event, context)