import logging

from fastapi import APIRouter, HTTPException, status, Depends

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.api import UserUpdateRequest, UserResponse


logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user."""
    return UserResponse(**current_user)

@router.put("/me", response_model=UserResponse)
def update_current_user(req: UserUpdateRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Update current user's profile."""
    if req.email and req.email != current_user["email"]:
        existing_user = db.get_by_email(req.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )

    success = db.update_profile(
        user_id=current_user["user_id"],
        updates=req.model_dump(exclude_none=True)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

    updated_user = db.get_by_id(current_user["user_id"])

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated user profile"
        )

    return UserResponse(**updated_user)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_current_user(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Deactivate current user's account."""
    success = db.deactivate(current_user["user_id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )

    # UI deletes token client-side

    return