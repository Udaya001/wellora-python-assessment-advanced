from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.models import User
from app.schemas.analytics import DailyAnalytics, WeeklyTrend, RecommendationResponse
from app.services.analytics_service import AnalyticsService
from app.core.security import get_current_active_user
from app.core.cache import cache_manager
from app.utils.logger import logger
from datetime import datetime, date



router = APIRouter(prefix="/analytics", tags=["Analytics & Insights"])


@router.get("/daily", response_model=DailyAnalytics)
async def get_daily_analytics(
    target_date: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    parsed_date = date.today()
    if target_date:
        try:
            parsed_date = datetime.fromisoformat(target_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    cache_key = f"analytics_daily:{current_user.id}:{parsed_date.isoformat()}"

    cached_result = await cache_manager.get_cached_data(cache_key)
    if cached_result:
        logger.info(f"Cache HIT for daily analytics for user {current_user.id} on {parsed_date}")
        # Deserialize from dict back to Pydantic model
        return DailyAnalytics.model_validate(cached_result) # Use model_validate

    logger.info(f"Cache MISS for daily analytics for user {current_user.id} on {parsed_date}. Calculating...")
    analytics_service = AnalyticsService(db)
    try:
        analytics_data = await analytics_service.get_daily_analytics(current_user.id, parsed_date)
        await cache_manager.set_cached_data(cache_key, analytics_data.model_dump(), expiry_seconds=300) # Use model_dump
        logger.info(f"Calculated and cached daily analytics for user {current_user.id} on {parsed_date}")
        return analytics_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating daily analytics for user {current_user.id} on {parsed_date}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while calculating daily analytics."
        )


@router.get("/weekly", response_model=list[WeeklyTrend])
async def get_weekly_trends(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    cache_key = f"analytics_weekly:{current_user.id}"

    cached_result = await cache_manager.get_cached_data(cache_key)
    if cached_result:
        logger.info(f"Cache HIT for weekly trends for user {current_user.id}")
        # Deserialize list of dicts back to list of Pydantic models
        return [WeeklyTrend.model_validate(item) for item in cached_result] # Use model_validate

    logger.info(f"Cache MISS for weekly trends for user {current_user.id}. Calculating...")
    analytics_service = AnalyticsService(db)
    try:
        trends_data = await analytics_service.get_weekly_trends(current_user.id)
        # Serialize list of Pydantic models to list of dicts for caching
        trends_dicts = [item.model_dump() for item in trends_data] # Use model_dump
        await cache_manager.set_cached_data(cache_key, trends_dicts, expiry_seconds=300)
        logger.info(f"Calculated and cached weekly trends for user {current_user.id}")
        return trends_data # Return the list of Pydantic models

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating weekly trends for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while calculating weekly trends."
        )


@router.get("/reco", response_model=RecommendationResponse)
async def get_recommendation(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    cache_key = f"analytics_recommendation:{current_user.id}"

    cached_result = await cache_manager.get_cached_data(cache_key)
    if cached_result:
        logger.info(f"Cache HIT for recommendation for user {current_user.id}")
        # Deserialize from dict back to Pydantic model
        return RecommendationResponse.model_validate(cached_result) # Use model_validate

    logger.info(f"Cache MISS for recommendation for user {current_user.id}. Calculating...")
    analytics_service = AnalyticsService(db)
    try:
        reco_data = await analytics_service.get_recommendation(current_user.id)
        # Serialize Pydantic model to dict for caching
        reco_dict = reco_data.model_dump() # Use model_dump
        await cache_manager.set_cached_data(cache_key, reco_dict, expiry_seconds=300)
        logger.info(f"Calculated and cached recommendation for user {current_user.id}")
        return reco_data # Return the Pydantic model

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating recommendation for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while calculating the recommendation."
        )