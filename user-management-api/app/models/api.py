import re
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, AfterValidator, SecretStr


def validate_name(name: str | None) -> str | None:
    if name is None:
        return None
    name = name.strip()
    if not name:
        raise ValueError("Names cannot be empty or whitespace only.")
    if len(name) > 50:
        raise ValueError("Names cannot exceed 50 characters.")
    if not re.match(r"^[A-Za-z\s'-]+$", name):
        raise ValueError("Names must contain only letters, spaces, hyphens, and apostrophes.")
    return name

def validate_password(password: SecretStr) -> SecretStr:
    if len(password.get_secret_value()) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(password.get_secret_value()) > 64:
        raise ValueError("Password must not be more than 64 characters long.")
    if re.search(r"\s", password.get_secret_value()):
        raise ValueError("Password must not contain whitespace characters.")
    if not re.search(r"[A-Z]", password.get_secret_value()) or not re.search(r"[a-z]", password.get_secret_value()):
        raise ValueError("Password must contain at least one uppercase and one lowercase letter.")
    if not re.search(r"[0-9]", password.get_secret_value()):
        raise ValueError("Password must contain at least one digit.")
    return password

class SuccessResponse(BaseModel):
    message: str

class RegistrationRequest(BaseModel):
    email: EmailStr
    password: Annotated[SecretStr, AfterValidator(validate_password)]
    first_name: Annotated[str, AfterValidator(validate_name)]
    last_name: Annotated[str, AfterValidator(validate_name)]

class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr

class UserResponse(BaseModel):
    id: str = Field(alias="user_id")
    email: EmailStr
    first_name: str
    last_name: str
    created_at: datetime
    is_active: bool

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
    user: UserResponse

class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    first_name: Annotated[str | None, AfterValidator(validate_name)] = None
    last_name: Annotated[str | None, AfterValidator(validate_name)] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ConfirmForgotPasswordRequest(BaseModel):
    email: EmailStr
    confirmation_code: str
    new_password: Annotated[SecretStr, AfterValidator(validate_password)]

class ConfirmEmailRequest(BaseModel):
    email: EmailStr
    confirmation_code: str