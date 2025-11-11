import json
import logging
from typing import Optional, Any
from redis.asyncio import Redis
from app.core.config import settings
from app.utils.logger import logger



class CacheManager:
    def __init__(self):
        self.redis_client: Optional[Redis] = None

    async def connect(self):
        try:
            self.redis_client = Redis.from_url(settings.redis_url)
            # Test the connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise e # Re-raise to prevent app startup if cache is critical

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()

    async def get_cached_data(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            logger.warning("Redis client not initialized. Skipping cache get.")
            return None

        try:
            cached_value = await self.redis_client.get(key)
            if cached_value:
                logger.info(f"Cache HIT for key: {key}")
                return json.loads(cached_value)
            logger.info(f"Cache MISS for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Error getting from cache for key {key}: {e}")
            # Proceed without cache if there's an error
            return None

    async def set_cached_data(self, key: str, data: Any, expiry_seconds: int = 300): # Default 5 minutes (300 sec)
        if not self.redis_client:
            logger.warning("Redis client not initialized. Skipping cache set.")
            return

        try:
            json_data = json.dumps(data)
            await self.redis_client.setex(key, expiry_seconds, json_data)
            logger.info(f"Cache SET for key: {key} with expiry {expiry_seconds}s")
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            # Failing to set cache shouldn't break the main flow

    async def delete_cached_data(self, key: str):
        if not self.redis_client:
            logger.warning("Redis client not initialized. Skipping cache delete.")
            return

        try:
            await self.redis_client.delete(key)
            logger.info(f"Cache DELETED for key: {key}")
        except Exception as e:
            logger.error(f"Error deleting from cache for key {key}: {e}")



cache_manager = CacheManager()