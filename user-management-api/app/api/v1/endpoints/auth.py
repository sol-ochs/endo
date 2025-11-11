import base64
import boto3
import hmac
import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Depends

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.api import LoginRequest, LoginResponse, UserResponse, RegistrationRequest, ForgotPasswordRequest, ConfirmForgotPasswordRequest, ConfirmEmailRequest


logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

router = APIRouter()

cognito_client = boto3.client('cognito-idp', region_name=settings.COGNITO_REGION)

def _calculate_secret_hash(username: str) -> str:
    """Calculate the secret hash for Cognito authentication"""
    message = username + settings.COGNITO_CLIENT_ID
    dig = hmac.new(
        settings.COGNITO_CLIENT_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db=Depends(get_db)):
    """Authenticate user with Cognito"""
    try:
        secret_hash = _calculate_secret_hash(request.email)

        response = cognito_client.initiate_auth(
            ClientId=settings.COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': request.email,
                'PASSWORD': request.password.get_secret_value(),
                'SECRET_HASH': secret_hash
            }
        )

        access_token = response['AuthenticationResult']['AccessToken']
        id_token = response['AuthenticationResult']['IdToken']

        # Get user from our database
        user = db.get_by_email(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please contact support."
            )

        # Update last login
        now = datetime.now(timezone.utc).isoformat()
        db.update_last_login(user["user_id"], now)

        # Reactivate user on login if they were deactivated
        if not user.get("is_active", True):
            db.reactivate(user["user_id"])
            user["is_active"] = True

        response_data = LoginResponse(
            access_token=id_token,  # Use ID token for client
            token_type="bearer",
            user=UserResponse(**user)
        )

        return response_data

    except cognito_client.exceptions.NotAuthorizedException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except cognito_client.exceptions.UserNotConfirmedException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not confirmed. Please check your email and confirm your account."
        )
    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user - Cognito tokens are stateless, so this is mainly for logging"""
    logger.info(f"User logged out: {current_user.get('email')}")
    return

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegistrationRequest, db=Depends(get_db)):
    """Register a new user with Cognito"""
    try:
        secret_hash = _calculate_secret_hash(request.email)

        # Check if user already exists locally
        existing_user = db.get_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists. Please log in instead."
            )

        # Create user in Cognito
        response = cognito_client.sign_up(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=request.email,
            Password=request.password.get_secret_value(),
            SecretHash=secret_hash,
            UserAttributes=[
                {'Name': 'email', 'Value': request.email},
                {'Name': 'given_name', 'Value': request.first_name},
                {'Name': 'family_name', 'Value': request.last_name}
            ]
        )

        # Create user in local database
        user_data = {
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
            "cognito_user_sub": response.get('UserSub')
        }

        user_id = db.create(user_data)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user record"
            )

        return {
            "message": "User created successfully. Please check your email for verification.",
            "user_id": user_id,
            "email": request.email
        }

    except cognito_client.exceptions.UsernameExistsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    except cognito_client.exceptions.InvalidPasswordException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid password: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    """Initiate password reset via Cognito"""
    try:
        secret_hash = _calculate_secret_hash(request.email)

        cognito_client.forgot_password(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=request.email,
            SecretHash=secret_hash
        )

        return {"message": "Password reset code sent to your email"}

    except cognito_client.exceptions.UserNotFoundException:
        # Return same message to avoid email enumeration
        return {"message": "Password reset code sent to your email"}
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset code"
        )

@router.post("/confirm-email")
def confirm_email(request: ConfirmEmailRequest):
    """Confirm user email with verification code"""
    try:
        secret_hash = _calculate_secret_hash(request.email)

        cognito_client.confirm_sign_up(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=request.email,
            ConfirmationCode=request.confirmation_code,
            SecretHash=secret_hash
        )

        return {"message": "Email confirmed successfully. You can now log in."}

    except cognito_client.exceptions.CodeMismatchException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    except cognito_client.exceptions.ExpiredCodeException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired"
        )
    except cognito_client.exceptions.NotAuthorizedException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User cannot be confirmed"
        )
    except Exception as e:
        logger.error(f"Email confirmation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm email"
        )

@router.post("/resend-confirmation")
def resend_confirmation(request: ForgotPasswordRequest):
    """Resend email confirmation code"""
    try:
        secret_hash = _calculate_secret_hash(request.email)

        cognito_client.resend_confirmation_code(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=request.email,
            SecretHash=secret_hash
        )

        return {"message": "Confirmation code sent to your email"}

    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except cognito_client.exceptions.InvalidParameterException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already confirmed"
        )
    except Exception as e:
        logger.error(f"Resend confirmation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend confirmation code"
        )

@router.post("/confirm-forgot-password")
def confirm_forgot_password(request: ConfirmForgotPasswordRequest):
    """Confirm password reset with verification code"""
    try:
        secret_hash = _calculate_secret_hash(request.email)

        cognito_client.confirm_forgot_password(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=request.email,
            ConfirmationCode=request.confirmation_code,
            Password=request.new_password.get_secret_value(),
            SecretHash=secret_hash
        )

        return {"message": "Password reset successful"}

    except cognito_client.exceptions.CodeMismatchException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    except cognito_client.exceptions.ExpiredCodeException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired"
        )
    except cognito_client.exceptions.InvalidPasswordException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid password: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Confirm forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )