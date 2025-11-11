import enum
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Enum, Float 
from sqlalchemy.orm import Mapped, mapped_column, relationship 
from passlib.context import CryptContext
from app.db.base import Base 
from app.utils.datetime_utils import utc_now 

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base): 

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    gender: Mapped[Optional[str]] = mapped_column(String, nullable=True) 
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True) 
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True) 
    activity_level: Mapped[Optional[str]] = mapped_column(String, nullable=True) 
    daily_calorie_goal: Mapped[Optional[float]] = mapped_column(Float, nullable=True) 
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now(), onupdate=utc_now())

    # Relationship to Meal
    meals: Mapped[list["Meal"]] = relationship("Meal", back_populates="user")

    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)