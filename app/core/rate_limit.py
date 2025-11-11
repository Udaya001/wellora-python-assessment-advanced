import time
import logging
from redis.asyncio import Redis
from fastapi import HTTPException, status
from app.core.config import settings
from app.utils.logger import logger



class RateLimiter:
    def __init__(self):
        self.redis_client: Redis = None

    async def init_limiter(self, redis_client: Redis):
        """Initialize the rate limiter with a Redis client."""
        self.redis_client = redis_client
        logger.info("Rate limiter initialized with Redis client.")

    async def is_allowed(self, identifier: str) -> tuple[bool, int, int]: # Returns (allowed, remaining_requests, reset_time_seconds)
        if not self.redis_client:
            logger.warning("Redis client not initialized for rate limiter. Allowing request.")
            return True, settings.rate_limit_requests, int(time.time()) + settings.rate_limit_window

        current_time = int(time.time())
        key = f"rate_limit:{identifier}"
        pipeline = self.redis_client.pipeline()

        # Remove outdated timestamps (older than the window)
        pipeline.zremrangebyscore(key, 0, current_time - settings.rate_limit_window)

        # Get current count within the window
        current_count = await self.redis_client.zcard(key)

        if current_count >= settings.rate_limit_requests:
            # Rate limit exceeded
            # Calculate reset time: time when the oldest request in the window expires
            oldest_request_time = await self.redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_request_time:
                reset_time = int(oldest_request_time[0][1]) + settings.rate_limit_window
            else:
                # Fallback, shouldn't happen if zcard >= limit
                reset_time = current_time + settings.rate_limit_window
            return False, settings.rate_limit_requests - current_count, reset_time

        # Add current request timestamp
        pipeline.zadd(key, {str(current_time): current_time})
        # Set expiry on the key to clean up automatically
        pipeline.expire(key, settings.rate_limit_window)
        await pipeline.execute()

        remaining_requests = settings.rate_limit_requests - current_count - 1
        reset_time = current_time + settings.rate_limit_window
        return True, remaining_requests, reset_time


rate_limiter = RateLimiter()