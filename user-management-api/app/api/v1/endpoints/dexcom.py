import logging
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.security import get_current_user
from app.db.dexcom_repository import DexcomCredentialsRepository

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

router = APIRouter()


def _store_oauth_state(state: str, user_id: str) -> None:
    """Store OAuth state in DynamoDB with 10-minute TTL for CSRF protection."""
    import boto3
    from datetime import datetime, timezone, timedelta
    from app.core.config import settings

    dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
    table = dynamodb.Table(settings.SESSIONS_TABLE)

    expires_at = int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())

    table.put_item(
        Item={
            'session_id': f"oauth_state:{state}",
            'user_id': user_id,
            'expires_at': expires_at
        }
    )


def _get_and_delete_oauth_state(state: str) -> str | None:
    """Retrieve and delete OAuth state from DynamoDB."""
    import boto3
    from app.core.config import settings

    dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
    table = dynamodb.Table(settings.SESSIONS_TABLE)

    try:
        response = table.get_item(Key={'session_id': f"oauth_state:{state}"})
        if 'Item' not in response:
            return None

        user_id = response['Item']['user_id']

        # Delete the state to prevent reuse
        table.delete_item(Key={'session_id': f"oauth_state:{state}"})

        return user_id
    except Exception:
        return None


@router.get("/connect")
async def connect_dexcom(current_user: dict = Depends(get_current_user)):
    """
    Initiate Dexcom OAuth flow by redirecting to Dexcom authorization page
    """
    # Generate a random state parameter to prevent CSRF
    state = secrets.token_urlsafe(32)
    _store_oauth_state(state, current_user['user_id'])

    # Build authorization URL
    auth_params = {
        'client_id': settings.DEXCOM_CLIENT_ID,
        'redirect_uri': settings.DEXCOM_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'offline_access',
        'state': state
    }

    auth_url = f"{settings.DEXCOM_API_BASE_URL}/v2/oauth2/login?{urlencode(auth_params)}"

    logger.info(f"Initiating Dexcom OAuth for user {current_user['user_id']}")

    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.get("/callback")
async def dexcom_callback(
    code: str = Query(..., description="Authorization code from Dexcom"),
    state: str = Query(..., description="State parameter for CSRF protection")
):
    """
    Handle OAuth callback from Dexcom
    """
    # Verify state to prevent CSRF
    user_id = _get_and_delete_oauth_state(state)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter"
        )

    # Exchange authorization code for access token
    token_url = f"{settings.DEXCOM_API_BASE_URL}/v2/oauth2/token"

    token_data = {
        'client_id': settings.DEXCOM_CLIENT_ID,
        'client_secret': settings.DEXCOM_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': settings.DEXCOM_REDIRECT_URI
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            if response.status_code != 200:
                logger.error(f"Dexcom token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange authorization code: {response.text}"
                )

            token_response = response.json()

            # Store tokens in DynamoDB
            dexcom_repo = DexcomCredentialsRepository()
            success = dexcom_repo.create_or_update(
                user_id=user_id,
                access_token=token_response['access_token'],
                refresh_token=token_response['refresh_token'],
                expires_in=token_response['expires_in']
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to store Dexcom credentials"
                )

            logger.info(f"Successfully connected Dexcom account for user {user_id}")

            # Redirect to frontend account page with success message
            return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/account?dexcom=connected")

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during Dexcom OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect to Dexcom API"
        )
    except Exception as e:
        logger.error(f"Unexpected error during Dexcom OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/status")
async def dexcom_status(current_user: dict = Depends(get_current_user)):
    """
    Check if user has connected their Dexcom account
    """
    dexcom_repo = DexcomCredentialsRepository()
    has_credentials = dexcom_repo.has_credentials(current_user['user_id'])

    credentials = None
    if has_credentials:
        credentials = dexcom_repo.get_by_user_id(current_user['user_id'])

    return {
        "connected": has_credentials,
        "expires_at": credentials.get('expires_at') if credentials else None
    }


@router.delete("/disconnect")
async def disconnect_dexcom(current_user: dict = Depends(get_current_user)):
    """
    Disconnect Dexcom account by deleting stored credentials
    """
    dexcom_repo = DexcomCredentialsRepository()
    success = dexcom_repo.delete(current_user['user_id'])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Dexcom account"
        )

    logger.info(f"Disconnected Dexcom account for user {current_user['user_id']}")

    return {"message": "Dexcom account disconnected successfully"}
