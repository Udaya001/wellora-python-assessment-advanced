# app/schemas/food.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FoodBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Name of the food item")
    serving_size_g: float = Field(..., gt=0, description="Serving size in grams")
    calories: float = Field(..., ge=0, description="Calories per serving")
    protein_g: float = Field(..., ge=0, description="Protein in grams per serving")
    carbs_g: float = Field(..., ge=0, description="Carbs in grams per serving")
    fat_g: float = Field(..., ge=0, description="Fat in grams per serving")


class FoodCreate(FoodBase):
    pass # Inherit all fields from FoodBase


class FoodUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    serving_size_g: Optional[float] = Field(None, gt=0)
    calories: Optional[float] = Field(None, ge=0)
    protein_g: Optional[float] = Field(None, ge=0)
    carbs_g: Optional[float] = Field(None, ge=0)
    fat_g: Optional[float] = Field(None, ge=0)


class FoodInDB(FoodBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FoodPublic(FoodBase):
    id: int

    class Config:
        from_attributes = True


class FoodSearch(BaseModel):
    name: Optional[str] = Field(None, description="Search food by name (partial match)")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")