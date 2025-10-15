import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_serializer


class DBUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="user_id")
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    is_active: bool = True
    last_login: datetime | None = None
    cognito_user_sub: str | None = None

    @model_serializer
    def serialize(self):
        return {
            "user_id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "cognito_user_sub": self.cognito_user_sub
        }


class DBDexcomCredentials(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    @model_serializer
    def serialize(self):
        return {
            "user_id": self.user_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
