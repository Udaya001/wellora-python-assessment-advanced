from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status
from app.models import Meal, Food
from app.models import User
from app.schemas.analytics import DailyAnalytics, WeeklyTrend, RecommendationResponse 

class AnalyticsService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_daily_analytics(self, user_id: int, target_date: Optional[datetime] = None) -> DailyAnalytics:
        """
        Calculate daily analytics for a user for a specific date (defaults to today).
        Includes totals, remaining calories, and status.
        """
        if target_date is None:
            target_date = datetime.utcnow().date()

        # Convert datetime to date for comparison if needed within the query
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        # Query total calories consumed for the day
        total_calories_result = await self.db_session.execute(
            select(func.sum(Meal.calories)).where(
                and_(
                    Meal.user_id == user_id,
                    Meal.timestamp >= start_of_day,
                    Meal.timestamp <= end_of_day
                )
            )
        )
        total_calories_consumed = total_calories_result.scalar() or 0.0

        # Query total macros consumed for the day
        total_macros_result = await self.db_session.execute(
            select(
                func.sum(Meal.protein_g).label('total_protein'),
                func.sum(Meal.carbs_g).label('total_carbs'),
                func.sum(Meal.fat_g).label('total_fat')
            ).where(
                and_(
                    Meal.user_id == user_id,
                    Meal.timestamp >= start_of_day,
                    Meal.timestamp <= end_of_day
                )
            )
        )
        macros_row = total_macros_result.first()
        total_protein_g = macros_row.total_protein or 0.0
        total_carbs_g = macros_row.total_carbs or 0.0
        total_fat_g = macros_row.total_fat or 0.0

        user = await self.db_session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        daily_calorie_goal = user.daily_calorie_goal or 0.0 # Default to 0 if not set

 
        remaining_calories = daily_calorie_goal - total_calories_consumed
        if total_calories_consumed <= daily_calorie_goal:
            status_str = "On Track"
        else:
            status_str = "Exceeded"

        return DailyAnalytics(
            date=target_date.isoformat(),
            total_calories=total_calories_consumed,
            total_protein_g=total_protein_g,
            total_carbs_g=total_carbs_g,
            total_fat_g=total_fat_g,
            daily_calorie_goal=daily_calorie_goal,
            remaining_calories=remaining_calories,
            status=status_str
        )

    async def get_weekly_trends(self, user_id: int) -> List[WeeklyTrend]:

        today = datetime.utcnow().date()
        week_start = today - timedelta(days=6) 

        week_dates = [week_start + timedelta(days=i) for i in range(7)]


        daily_totals_query = select(
            func.date(Meal.timestamp).label('meal_date'),
            func.sum(Meal.calories).label('total_calories'),
            func.sum(Meal.protein_g).label('total_protein_g'),
            func.sum(Meal.carbs_g).label('total_carbs_g'),
            func.sum(Meal.fat_g).label('total_fat_g')
        ).where(
            and_(
                Meal.user_id == user_id,
                func.date(Meal.timestamp) >= week_start,
                func.date(Meal.timestamp) <= today
            )
        ).group_by(func.date(Meal.timestamp))

        result = await self.db_session.execute(daily_totals_query)
        daily_data = {row.meal_date: {
            'total_calories': row.total_calories or 0.0,
            'total_protein_g': row.total_protein_g or 0.0,
            'total_carbs_g': row.total_carbs_g or 0.0,
            'total_fat_g': row.total_fat_g or 0.0,
        } for row in result}

        trends = []
        for date in week_dates:
            data = daily_data.get(date, {
                'total_calories': 0.0,
                'total_protein_g': 0.0,
                'total_carbs_g': 0.0,
                'total_fat_g': 0.0,
            })
            trends.append(WeeklyTrend(
                date=date.isoformat(),
                total_calories=data['total_calories'],
                total_protein_g=data['total_protein_g'],
                total_carbs_g=data['total_carbs_g'],
                total_fat_g=data['total_fat_g']
            ))

        return trends

    async def get_recommendation(self, user_id: int) -> RecommendationResponse:

        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        three_days_ago = today - timedelta(days=3)


        user = await self.db_session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        daily_calorie_goal = user.daily_calorie_goal or 0.0

        start_yesterday = datetime.combine(yesterday, datetime.min.time())
        end_yesterday = datetime.combine(yesterday, datetime.max.time())

        yesterday_calories_result = await self.db_session.execute(
            select(func.sum(Meal.calories)).where(
                and_(
                    Meal.user_id == user_id,
                    Meal.timestamp >= start_yesterday,
                    Meal.timestamp <= end_yesterday
                )
            )
        )
        yesterday_calories = yesterday_calories_result.scalar() or 0.0

        exceeded_yesterday = yesterday_calories > daily_calorie_goal

        start_3_days = datetime.combine(three_days_ago, datetime.min.time())
        end_today = datetime.combine(today, datetime.max.time())

        daily_consumption_query = select(
            func.date(Meal.timestamp).label('meal_date'),
            func.sum(Meal.calories).label('total_calories')
        ).where(
            and_(
                Meal.user_id == user_id,
                Meal.timestamp >= start_3_days,
                Meal.timestamp <= end_today
            )
        ).group_by(func.date(Meal.timestamp))

        result = await self.db_session.execute(daily_consumption_query)
        daily_consumptions = {row.meal_date: row.total_calories or 0.0 for row in result}

        under_goal_3_days = True
        for i in range(3):
            check_date = today - timedelta(days=i)
            daily_total = daily_consumptions.get(check_date, 0.0)
            if daily_total >= daily_calorie_goal:
                under_goal_3_days = False
                break

        rationale = ""
        suggested_foods = []

        if exceeded_yesterday:
            rationale = "You exceeded your calorie goal yesterday. Here are some lower-calorie options."
            suggested_foods_query = select(Food).where(Food.calories < daily_calorie_goal).order_by(Food.calories.asc()).limit(5)
            result = await self.db_session.execute(suggested_foods_query)
            suggested_foods = result.scalars().all()

        elif under_goal_3_days:
            rationale = "You've been under your calorie goal for the last 3 days. Here are some protein-dense options to help you meet your target."
            suggested_foods_query = select(Food).order_by(Food.protein_g.desc()).limit(5)
            result = await self.db_session.execute(suggested_foods_query)
            suggested_foods = result.scalars().all()
        else:
            rationale = "Your calorie intake is consistent. No specific recommendation at this time."
        suggested_food_dicts = [
            {
                "id": food.id,
                "name": food.name,
                "serving_size_g": food.serving_size_g,
                "calories": food.calories,
                "protein_g": food.protein_g,
                "carbs_g": food.carbs_g,
                "fat_g": food.fat_g
            } for food in suggested_foods
        ]

        return RecommendationResponse(
            rationale=rationale,
            suggested_foods=suggested_food_dicts
        )