import logging
import jwt
from jwt import PyJWKClient
from datetime import datetime, timezone
from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.core.config import settings
from app.core.dependencies import get_db


logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

security = HTTPBearer()

class CognitoJWTValidator:
    def __init__(self):
        self.jwks_url = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        self.jwks_client = PyJWKClient(self.jwks_url)

    def verify_token(self, token: str) -> Dict:
        """Verify and decode a Cognito JWT token"""
        try:
            # Get the signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Verify and decode the token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                audience=settings.COGNITO_CLIENT_ID,
                issuer=f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

cognito_validator = CognitoJWTValidator()

def get_current_user(token=Depends(security), db=Depends(get_db)) -> dict:
    """Get the current user from the Cognito JWT token."""
    try:
        payload = cognito_validator.verify_token(token.credentials)
        email: str = payload.get("email") or payload.get("username")

        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.get_by_email(email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def update_last_login(user_id: str, db=Depends(get_db)) -> bool:
    """Update the last login timestamp for a user."""
    now = datetime.now(timezone.utc).isoformat()
    return db.update_last_login(user_id, now)

def deactivate_user(user_id: str, db=Depends(get_db)) -> bool:
    """Deactivate a user account."""
    return db.deactivate(user_id)