from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.models import User
from app.schemas.meal import MealCreate, MealUpdate, MealPublic, MealListParams
from app.services.meal_service import MealService
from app.core.security import get_current_active_user
from app.utils.logger import logger


router = APIRouter(prefix="/meals", tags=["Meals"])


@router.post("/", response_model=MealPublic, status_code=status.HTTP_201_CREATED)
async def create_meal_log(
    meal_data: MealCreate,
    idempotency_key: str = Header(None, alias="Idempotency-Key", description="Idempotency key to prevent duplicate meals"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
 
    meal_service = MealService(db)
    try:

        db_meal = await meal_service.create_meal_log(current_user.id, meal_data, idempotency_key) 

        if idempotency_key:
            logger.info(f"Processed meal log request for user {current_user.id} with idempotency key {idempotency_key}. Meal ID: {db_meal.id}")
        else:
            logger.info(f"Created new meal log ID {db_meal.id} for user {current_user.id}")
        return db_meal

    except HTTPException:
        # Re-raise HTTP exceptions (like food not found)
        raise
    except Exception as e:
        logger.error(f"Error creating meal log for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the meal log."
        )


@router.get("/", response_model=dict) # Response is a dict containing 'items' and 'total'
async def list_meals(
    limit: int = 10,
    offset: int = 0,
    start_date: str = None,
    end_date: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):

    from datetime import datetime
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    list_params = MealListParams(limit=limit, offset=offset, start_date=start_dt, end_date=end_dt)
    meal_service = MealService(db)
    try:
        meals, total_count = await meal_service.list_meals(current_user.id, list_params)
        # Convert ORM objects to Pydantic models before returning
        meal_public_list = [MealPublic.model_validate(meal) for meal in meals]
        logger.info(f"User {current_user.id} listed {len(meal_public_list)} meals, total available: {total_count}")
        return {"items": meal_public_list, "total": total_count}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error listing meals for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing meals."
        )



@router.get("/{meal_id}", response_model=MealPublic)
async def get_meal(
    meal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):

    meal_service = MealService(db)
    try:
        meal = await meal_service.get_meal_by_id(current_user.id, meal_id)
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found or does not belong to user")

        logger.info(f"User {current_user.id} retrieved meal log with ID: {meal_id}")
        return meal

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving meal {meal_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the meal log."
        )


@router.patch("/{meal_id}", response_model=MealPublic)
async def update_meal_log(
    meal_id: int,
    meal_update: MealUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    meal_service = MealService(db)
    try:
        updated_meal = await meal_service.update_meal_log(current_user.id, meal_id, meal_update)
        if not updated_meal:
            raise HTTPException(status_code=404, detail="Meal not found or does not belong to user")

        logger.info(f"User {current_user.id} updated meal log with ID: {updated_meal.id}")
        return updated_meal

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating meal {meal_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the meal log."
        )


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_log(
    meal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    meal_service = MealService(db)
    try:
        success = await meal_service.delete_meal_log(current_user.id, meal_id)
        if not success:
            raise HTTPException(status_code=404, detail="Meal not found or does not belong to user")

        logger.info(f"User {current_user.id} deleted meal log with ID: {meal_id}")
        return

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting meal {meal_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the meal log."
        )