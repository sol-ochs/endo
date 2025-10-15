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
    DEXCOM_CREDENTIALS_TABLE: str = os.getenv("DEXCOM_CREDENTIALS_TABLE", "endo-dexcom-credentials-dev")

    # Dexcom API configuration
    DEXCOM_CLIENT_ID: str = os.getenv("DEXCOM_CLIENT_ID", "")
    DEXCOM_CLIENT_SECRET: str = os.getenv("DEXCOM_CLIENT_SECRET", "")
    DEXCOM_API_BASE_URL: str = os.getenv("DEXCOM_API_BASE_URL", "https://sandbox-api.dexcom.com")
    DEXCOM_REDIRECT_URI: str = os.getenv("DEXCOM_REDIRECT_URI", "http://localhost:3000/dexcom/callback")

    # CORS configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        # TODO: Add production origins
    ]

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARN")

settings = Settings()