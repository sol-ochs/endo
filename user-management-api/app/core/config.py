import os
from typing import List


class Settings:
    # AWS Cognito configuration
    COGNITO_REGION: str = os.getenv("COGNITO_REGION", "us-east-1")
    COGNITO_USER_POOL_ID: str = os.getenv("COGNITO_USER_POOL_ID", "")
    COGNITO_CLIENT_ID: str = os.getenv("COGNITO_CLIENT_ID", "")
    COGNITO_CLIENT_SECRET: str = os.getenv("COGNITO_CLIENT_SECRET", "")

    # AWS configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    USERS_TABLE: str = os.getenv("USERS_TABLE", "endo-users-dev")

    # CORS configuration
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000"
    ).split(",")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARN")

settings = Settings()