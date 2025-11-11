import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.analytics_service import AnalyticsService
from app.utils.logger import logger
from app.utils.datetime_utils import utc_now

async def run_nightly_aggregation():
    logger.info("Starting nightly aggregation task...")

    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    yesterday = utc_now() - timedelta(days=1)
    logger.info(f"Recomputing aggregates for date: {yesterday}")

    try:
        async with async_session() as session:
            analytics_service = AnalyticsService(session)

            # Example: call analytics_service.get_daily_analytics for relevant users
            # await analytics_service.get_daily_analytics(user_id, yesterday)

            logger.info(f"Nightly aggregation task completed for date: {yesterday}")

    except Exception as e:
        logger.error(f"Error during nightly aggregation task: {e}")
    finally:
        await engine.dispose()
        logger.info("Nightly aggregation task finished.")


# Example of running as a standalone script
# asyncio.run(run_nightly_aggregation())
