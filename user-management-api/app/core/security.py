import logging
import jwt
import json
import requests
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.dependencies import get_db
from app.db.models.database_models import DBUser


logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

security = HTTPBearer()

class CognitoJWTValidator:
    def __init__(self):
        self.jwks_url = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        self.jwks = None
        self._load_jwks()

    def _load_jwks(self):
        """Load JSON Web Key Set from Cognito"""
        try:
            response = requests.get(self.jwks_url)
            response.raise_for_status()
            self.jwks = response.json()
        except Exception as e:
            logger.error(f"Failed to load JWKS: {e}")
            self.jwks = None

    def _get_key(self, token_header):
        """Get the signing key for a JWT token"""
        if not self.jwks:
            self._load_jwks()

        if not self.jwks:
            return None

        kid = token_header.get('kid')
        for key in self.jwks.get('keys', []):
            if key.get('kid') == kid:
                return key
        return None

    def verify_token(self, token: str) -> Dict:
        """Verify and decode a Cognito JWT token"""
        try:
            header = jwt.get_unverified_header(token)
            key = self._get_key(header)

            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find signing key"
                )

            # Construct the public key
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))

            # Verify and decode the token
            payload = jwt.decode(
                token,
                public_key,
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

cognito_validator = CognitoJWTValidator()

def get_current_user(token=Depends(security), db=Depends(get_db)) -> dict:
    """Get the current user from the Cognito JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = cognito_validator.verify_token(token.credentials)
        email: str = payload.get("email") or payload.get("username")

        if email is None:
            raise credentials_exception

    except HTTPException:
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception

    user = db.get_by_email(email)
    if user is None:
        raise credentials_exception
    return user

def update_last_login(user_id: str, db=Depends(get_db)) -> bool:
    """Update the last login timestamp for a user."""
    now = datetime.now(timezone.utc).isoformat()
    return db.update_last_login(user_id, now)

def deactivate_user(user_id: str, db=Depends(get_db)) -> bool:
    """Deactivate a user account."""
    return db.deactivate(user_id)