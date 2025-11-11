from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    gender: Optional[str] = Field(None, max_length=20)
    age: Optional[int] = Field(None, ge=0, le=150)
    height_cm: Optional[float] = Field(None, gt=0)
    weight_kg: Optional[float] = Field(None, gt=0)
    activity_level: Optional[str] = Field(None, max_length=50) 
    daily_calorie_goal: Optional[float] = Field(None, gt=0)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    gender: Optional[str] = Field(None, max_length=20)
    age: Optional[int] = Field(None, ge=0, le=150)
    height_cm: Optional[float] = Field(None, gt=0)
    weight_kg: Optional[float] = Field(None, gt=0)
    activity_level: Optional[str] = Field(None, max_length=50)
    daily_calorie_goal: Optional[float] = Field(None, gt=0)


class UserInDB(UserBase):
    id: int
    role: UserRole 
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 

class UserPublic(BaseModel):
    id: int
    name: str
    email: str
    gender: Optional[str]
    age: Optional[int]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    activity_level: Optional[str]
    daily_calorie_goal: Optional[float]
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True