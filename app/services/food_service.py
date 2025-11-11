from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.meal import Food
from app.schemas.food import FoodCreate, FoodUpdate, FoodSearch


class FoodService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def list_foods(self, search_params: FoodSearch) -> tuple[list[Food], int]:

        query = select(Food)

        if search_params.name:
            query = query.where(Food.name.ilike(f"%{search_params.name}%"))

        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await self.db_session.execute(count_query)
        total_count = total_count_result.scalar()

        query = query.offset(search_params.offset).limit(search_params.limit)

        result = await self.db_session.execute(query)
        foods = result.scalars().all()
        return foods, total_count

    async def get_food_by_id(self, food_id: int) -> Optional[Food]:
        return await self.db_session.get(Food, food_id)

    async def create_food(self, food_data: FoodCreate) -> Food:

        db_food = Food(**food_data.dict())
        self.db_session.add(db_food)
        await self.db_session.commit()
        await self.db_session.refresh(db_food)
        return db_food

    async def update_food(self, food_id: int, food_update: FoodUpdate) -> Optional[Food]:
        """
        Update an existing food item.
        """
        db_food = await self.get_food_by_id(food_id)
        if not db_food:
            return None

        # Update fields only if they are provided in the request
        update_data = food_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_food, field, value)

        self.db_session.add(db_food)
        await self.db_session.commit()
        await self.db_session.refresh(db_food)
        return db_food

    async def delete_food(self, food_id: int) -> bool:

        db_food = await self.get_food_by_id(food_id)
        if not db_food:
            return False

        await self.db_session.delete(db_food)
        await self.db_session.commit()
        return True