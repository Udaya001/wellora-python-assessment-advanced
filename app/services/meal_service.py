from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import HTTPException, status
from app.models import Meal, Food
from app.models import User
from app.schemas.meal import MealCreate, MealUpdate, MealListParams
from app.core.config import settings
from app.utils.datetime_utils import utc_now


class MealService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_meal_log(self, user_id: int, meal_data: MealCreate, idempotency_key: Optional[str] = None) -> Meal:

        #  Handle Idempotency
        if idempotency_key:
            # Check if a meal with this key already exists for the user
            existing_meal_result = await self.db_session.execute(
                select(Meal).where(
                    and_(
                        Meal.user_id == user_id,
                        Meal.idempotency_key == idempotency_key # Check against the new field
                    )
                )
            )
            existing_meal = existing_meal_result.scalar_one_or_none()
            if existing_meal:
                # If it exists, return the existing meal (idempotency achieved)
                return existing_meal


        food = await self.db_session.get(Food, meal_data.food_id)
        if not food:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Food with id {meal_data.food_id} not found"
            )

        total_calories = food.calories * meal_data.servings
        total_protein_g = food.protein_g * meal_data.servings
        total_carbs_g = food.carbs_g * meal_data.servings
        total_fat_g = food.fat_g * meal_data.servings


        timestamp = meal_data.timestamp or utc_now()


        db_meal = Meal(
            user_id=user_id,
            food_id=meal_data.food_id,
            servings=meal_data.servings,
            timestamp=timestamp,
            notes=meal_data.notes,
            calories=total_calories,
            protein_g=total_protein_g,
            carbs_g=total_carbs_g,
            fat_g=total_fat_g,
            idempotency_key=idempotency_key 
        )

        self.db_session.add(db_meal)
        await self.db_session.commit()
        await self.db_session.refresh(db_meal)
        return db_meal

    async def list_meals(self, user_id: int, list_params: MealListParams) -> tuple[list[Meal], int]:
        query = select(Meal).where(Meal.user_id == user_id)

        if list_params.start_date:
            query = query.where(Meal.timestamp >= list_params.start_date)
        if list_params.end_date:
            query = query.where(Meal.timestamp <= list_params.end_date)

        query = query.order_by(Meal.timestamp.desc())
  
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await self.db_session.execute(count_query)
        total_count = total_count_result.scalar()

        query = query.offset(list_params.offset).limit(list_params.limit)

        result = await self.db_session.execute(query)
        meals = result.scalars().all()
        return meals, total_count

    async def get_meal_by_id(self, user_id: int, meal_id: int) -> Optional[Meal]:
        result = await self.db_session.execute(
            select(Meal).where(
                and_(
                    Meal.id == meal_id,
                    Meal.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_meal_log(self, user_id: int, meal_id: int, meal_update: MealUpdate) -> Optional[Meal]:
        db_meal = await self.get_meal_by_id(user_id, meal_id)
        if not db_meal:
            return None


        update_data = meal_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_meal, field, value)


        if "servings" in update_data: 
            food = await self.db_session.get(Food, db_meal.food_id)
            if food:
                db_meal.calories = food.calories * db_meal.servings
                db_meal.protein_g = food.protein_g * db_meal.servings
                db_meal.carbs_g = food.carbs_g * db_meal.servings
                db_meal.fat_g = food.fat_g * db_meal.servings

        self.db_session.add(db_meal)
        await self.db_session.commit()
        await self.db_session.refresh(db_meal)
        return db_meal

    async def delete_meal_log(self, user_id: int, meal_id: int) -> bool:

        db_meal = await self.get_meal_by_id(user_id, meal_id)
        if not db_meal:
            return False

        await self.db_session.delete(db_meal)
        await self.db_session.commit()
        return True