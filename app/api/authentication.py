from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any

from app.services.auth_service import AuthService
from app.models.user import UserCreate, UserResponse
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/signup", response_model=Dict[str, Any])
async def signup(user_data: UserCreate):
    """
    Register a new user using Supabase authentication.
    """
    return await AuthService.sign_up(user_data)

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return access token.
    """
    return await AuthService.sign_in(form_data.username, form_data.password)

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """
    Sign out the current user.
    """
    await AuthService.sign_out(token)
    return {"message": "Successfully signed out"}

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get information about the currently authenticated user.
    """
    user = await AuthService.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user

@router.post("/reset-password")
async def reset_password(email: str):
    """
    Request a password reset email.
    """
    await AuthService.reset_password(email)
    return {"message": "Password reset email sent"}
