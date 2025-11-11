from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.models import User, UserRole
from app.schemas.user import UserUpdate, UserPublic
from app.services.user_service import UserService
from app.core.security import get_current_active_user, require_role
from app.utils.logger import logger


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserPublic)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"Retrieved profile for user ID: {current_user.id}")
    return current_user


@router.patch("/profile", response_model=UserPublic)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    user_service = UserService(db)
    try:
        updated_user = await user_service.update_user_profile(current_user.id, user_update)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Updated profile for user ID: {updated_user.id}")
        return updated_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile for user ID {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the profile."
        )


@router.get("/", response_model=list[UserPublic])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: AsyncSession = Depends(get_db_session)
):
    user_service = UserService(db)
    try:
        users, total_count = await user_service.list_users(skip=skip, limit=limit)
        logger.info(f"Admin user {current_user.id} listed users. Total found: {total_count}, returned: {len(users)}")
        # Convert ORM objects to Pydantic models for serialization
        return [UserPublic.model_validate(user) for user in users]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users for admin user ID {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing users."
        )


@router.patch("/{user_id}/role", response_model=UserPublic)
async def change_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)), # Requires admin role
    db: AsyncSession = Depends(get_db_session)
):

    user_service = UserService(db)
    try:
        updated_user = await user_service.change_user_role(user_id, new_role)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Admin user {current_user.id} changed role for user {user_id} to {new_role.value}")
        return updated_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing role for user {user_id} by admin user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing the user role."
        )