from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MealBase(BaseModel):
    food_id: int = Field(..., gt=0, description="ID of the food item consumed")
    servings: float = Field(..., gt=0, description="Number of servings consumed")
    timestamp: Optional[datetime] = Field(None, description="When the meal was consumed. Defaults to now if not provided.")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the meal")


class MealCreate(MealBase):
    pass


class MealUpdate(BaseModel):
    servings: Optional[float] = Field(None, gt=0)
    timestamp: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class MealInDB(MealBase):
    id: int
    user_id: int
    calories: float # Calculated total
    protein_g: float # Calculated total
    carbs_g: float # Calculated total
    fat_g: float # Calculated total
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MealPublic(MealBase):
    id: int
    calories: float # Calculated total
    protein_g: float # Calculated total
    carbs_g: float # Calculated total
    fat_g: float # Calculated total

    class Config:
        from_attributes = True


class MealListParams(BaseModel):
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    start_date: Optional[datetime] = Field(None, description="Filter meals from this date onwards")
    end_date: Optional[datetime] = Field(None, description="Filter meals up to this date")