import pytest
from httpx import AsyncClient
from app.core.security import verify_password
from app.models import User

@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient, db_session):
    user_data = {
        "name": "Test User",
        "email": "test_register@example.com",
        "password": "securepassword123",
        "gender": "male",
        "age": 30,
        "height_cm": 180.0,
        "weight_kg": 75.0,
        "activity_level": "moderately_active",
        "daily_calorie_goal": 2200.0
    }

    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    response_data = response.json()
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert response_data["token_type"] == "bearer"

    db_user = await db_session.get(User, 1)
    assert db_user is not None
    assert db_user.email == user_data["email"]
    assert db_user.name == user_data["name"]
    assert verify_password(user_data["password"], db_user.password_hash)
    assert db_user.gender == user_data["gender"]
    assert db_user.age == user_data["age"]
    assert db_user.height_cm == user_data["height_cm"]
    assert db_user.weight_kg == user_data["weight_kg"]
    assert db_user.activity_level == user_data["activity_level"]
    assert db_user.daily_calorie_goal == user_data["daily_calorie_goal"]

@pytest.mark.asyncio
async def test_user_registration_duplicate_email(client: AsyncClient, db_session):
    user_data = {
        "name": "Test User",
        "email": "test_dup@example.com",
        "password": "securepassword123",
    }

    response1 = await client.post("/auth/register", json=user_data)
    assert response1.status_code == 201

    response2 = await client.post("/auth/register", json=user_data)
    assert response2.status_code == 409
    assert response2.json()["error"]["code"] == "409"
    assert "already registered" in response2.json()["error"]["message"]
