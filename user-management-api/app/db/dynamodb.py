import boto3

from app.core.config import settings


def get_dynamodb_resource():
    """Creates and returns a DynamoDB resource."""
    # For real AWS environments (dev, prod)
    return boto3.resource(
        service_name="dynamodb",
        region_name=settings.AWS_REGION
    )