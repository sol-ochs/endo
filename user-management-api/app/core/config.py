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
    SESSIONS_TABLE: str = os.getenv("SESSIONS_TABLE", "endo-sessions-dev")
    DEXCOM_CREDENTIALS_TABLE: str = os.getenv("DEXCOM_CREDENTIALS_TABLE", "endo-dexcom-credentials-dev")

    # Dexcom OAuth configuration
    DEXCOM_CLIENT_ID: str = os.getenv("DEXCOM_CLIENT_ID", "")
    DEXCOM_CLIENT_SECRET: str = os.getenv("DEXCOM_CLIENT_SECRET", "")
    DEXCOM_REDIRECT_URI: str = os.getenv("DEXCOM_REDIRECT_URI", "")
    DEXCOM_API_BASE_URL: str = os.getenv("DEXCOM_API_BASE_URL", "https://sandbox-api.dexcom.com")

    # Frontend configuration
    FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    CLOUDFRONT_URL: str = os.getenv("CLOUDFRONT_URL", "")

    # CORS configuration
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Get allowed CORS origins - includes localhost for dev and CloudFront URL from env."""
        origins = ["http://localhost:3000"]  # Always allow local dev

        # Add CloudFront URL if set
        if self.CLOUDFRONT_URL:
            origins.append(self.CLOUDFRONT_URL)

        return origins

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARN")

settings = Settings()