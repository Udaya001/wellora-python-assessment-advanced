from pydantic import BaseModel
from typing import List
from datetime import date


class DailyAnalytics(BaseModel):
    date: str 
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    daily_calorie_goal: float
    remaining_calories: float
    status: str 

class WeeklyTrend(BaseModel):
    date: str 
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float


class SuggestedFood(BaseModel):
    id: int
    name: str
    serving_size_g: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class RecommendationResponse(BaseModel):
    rationale: str
    suggested_foods: List[SuggestedFood]