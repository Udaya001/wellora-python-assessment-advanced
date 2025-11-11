import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from passlib.context import CryptContext
from app.db.base import Base
from app.utils.datetime_utils import utc_now
import bcrypt


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class Food(Base):

    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    serving_size_g: Mapped[float] = mapped_column(Float)  # Grams per serving
    calories: Mapped[float] = mapped_column(Float)
    protein_g: Mapped[float] = mapped_column(Float)
    carbs_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    meals: Mapped[list["Meal"]] = relationship("Meal", back_populates="food")


class Meal(Base):

    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    food_id: Mapped[int] = mapped_column(Integer, ForeignKey("foods.id"))
    servings: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    calories: Mapped[float] = mapped_column(Float)
    protein_g: Mapped[float] = mapped_column(Float)
    carbs_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="meals")
    food: Mapped["Food"] = relationship("Food", back_populates="meals")


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationship to Meal
    meals: Mapped[list["Meal"]] = relationship("Meal", back_populates="user")



    def set_password(self, password: str):
        password_bytes = password.encode('utf-8')
        # Bcrypt only handles up to 72 bytes
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        return bcrypt.checkpw(password_bytes, self.password_hash.encode('utf-8'))
