from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.models import User, UserRole
from app.schemas.food import FoodCreate, FoodUpdate, FoodPublic, FoodSearch
from app.services.food_service import FoodService
from app.core.security import require_role
from app.utils.logger import logger

router = APIRouter(prefix="/foods", tags=["Food Catalog"])


@router.get("/", response_model=dict) 
async def list_foods(
    name: str = Query(None, description="Search food by name (partial match)"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db_session)
):

    search_params = FoodSearch(name=name, limit=limit, offset=offset)
    food_service = FoodService(db)
    try:
        foods, total_count = await food_service.list_foods(search_params)
        # Convert ORM objects to Pydantic models before returning
        food_public_list = [FoodPublic.model_validate(food) for food in foods]
        logger.info(f"Listed {len(food_public_list)} foods, total available: {total_count}")
        return {"items": food_public_list, "total": total_count} # Ensure 'items' contains Pydantic models

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error listing foods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing foods."
        )


@router.get("/{food_id}", response_model=FoodPublic)
async def get_food(
    food_id: int,
    db: AsyncSession = Depends(get_db_session)
):

    food_service = FoodService(db)
    try:
        food = await food_service.get_food_by_id(food_id)
        if not food:
            raise HTTPException(status_code=404, detail="Food not found")

        logger.info(f"Retrieved food with ID: {food_id}")
        return food

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving food with ID {food_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the food item."
        )


@router.post("/", response_model=FoodPublic, status_code=status.HTTP_201_CREATED)
async def create_food(
    food_data: FoodCreate, 
    current_user: User = Depends(require_role(UserRole.ADMIN.value)), 
    db: AsyncSession = Depends(get_db_session)
):

    food_service = FoodService(db)
    try:
        db_food = await food_service.create_food(food_data) 
        logger.info(f"Admin user {current_user.id} created food item with ID: {db_food.id}")
        return db_food

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating food item by admin user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the food item."
        )


@router.patch("/{food_id}", response_model=FoodPublic)
async def update_food(
    food_id: int,
    food_update: FoodUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)), # Requires admin role
    db: AsyncSession = Depends(get_db_session)
):

    food_service = FoodService(db)
    try:
        updated_food = await food_service.update_food(food_id, food_update)
        if not updated_food:
            raise HTTPException(status_code=404, detail="Food not found")

        logger.info(f"Admin user {current_user.id} updated food item with ID: {updated_food.id}")
        return updated_food

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating food item {food_id} by admin user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the food item."
        )


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food(
    food_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)), # Requires admin role
    db: AsyncSession = Depends(get_db_session)
):
    food_service = FoodService(db)
    try:
        success = await food_service.delete_food(food_id)
        if not success:
            raise HTTPException(status_code=404, detail="Food not found")

        logger.info(f"Admin user {current_user.id} deleted food item with ID: {food_id}")
        return

    except HTTPException:

        raise
    except Exception as e:
        logger.error(f"Error deleting food item {food_id} by admin user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the food item."
        )