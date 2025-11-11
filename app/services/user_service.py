from datetime import timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.auth import Token, UserLogin
from app.core.security import get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings
from app.utils.datetime_utils import utc_now


class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def register_user(self, user_data: UserCreate) -> User:
        # Check if user already exists
        existing_user = await self.db_session.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
             
        # Create new user instance
        db_user = User(
            name=user_data.name,
            email=user_data.email,
            gender=user_data.gender,
            age=user_data.age,
            height_cm=user_data.height_cm,
            weight_kg=user_data.weight_kg,
            activity_level=user_data.activity_level,
            daily_calorie_goal=user_data.daily_calorie_goal,
        )
        db_user.set_password(user_data.password) 
        self.db_session.add(db_user)
        await self.db_session.commit()
        await self.db_session.refresh(db_user)
        return db_user

    async def authenticate_user(self, login_data: UserLogin) -> Optional[Token]:

        # Find user by email
        result = await self.db_session.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()

        # Verify user exists and password is correct
        if not user or not user.verify_password(login_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access and refresh tokens
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)

        access_token_data = {"sub": str(user.id), "role": user.role.value}
        refresh_token_data = {"sub": str(user.id), "role": user.role.value}

        access_token = create_access_token(
            access_token_data, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            refresh_token_data, expires_delta=refresh_token_expires
        )

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def get_user_by_id(self, user_id: int) -> Optional[User]:

        return await self.db_session.get(User, user_id)

    async def update_user_profile(self, user_id: int, user_update: UserUpdate) -> Optional[User]:

        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update fields only if they are provided in the request
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db_session.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def change_user_role(self, user_id: int, new_role: UserRole) -> Optional[User]:
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        user.role = new_role
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user