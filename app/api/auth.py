from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.user import UserCreate
from app.schemas.auth import Token, UserLogin, RegistrationResponse
from app.services.user_service import UserService
from app.core.security import (
    get_current_user_from_refresh_token, 
    security,decode_token,
    create_access_token, create_refresh_token
)
from app.core.config import settings
from app.utils.logger import logger


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session)
):
    user_service = UserService(db)
    try:
        db_user = await user_service.register_user(user_data)
        logger.info(f"New user registered with ID: {db_user.id}")

        return {"message": "User registered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration."
        )



@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db_session)
):

    user_service = UserService(db)
    try:
        token_data = await user_service.authenticate_user(login_data)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(f"User logged in successfully with email: {login_data.email}")
        return token_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login."
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token: str, 
    db: AsyncSession = Depends(get_db_session)
):

    try:
        # Validate the refresh token and get user details
        user = await get_current_user_from_refresh_token(refresh_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create new access and refresh tokens (rotation: new refresh token)
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)

        new_access_token_data = {"sub": str(user.id), "role": user.role.value}
        new_refresh_token_data = {"sub": str(user.id), "role": user.role.value}

        new_access_token = create_access_token(
            new_access_token_data, expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(
            new_refresh_token_data, expires_delta=refresh_token_expires
        )

        logger.info(f"Access token refreshed for user ID: {user.id}")
        return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh."
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        token_payload = decode_token(credentials.credentials)
        user_id = token_payload["user_id"]
        logger.info(f"User logged out. Access token presented for user ID: {user_id}")
        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during logout for token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout."
        )