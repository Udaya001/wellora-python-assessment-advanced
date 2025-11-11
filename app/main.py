import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, foods, meals, analytics
from app.core.config import settings
from app.core.cache import cache_manager
from app.core.rate_limit import rate_limiter
from app.db.session import engine 
from app.utils.logger import logger
from redis.asyncio import Redis 



# Lifespan event handler for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Wellora API...")
    try:
        # Initialize Cache
        await cache_manager.connect()
        logger.info("Cache manager initialized.")

        # Initialize Rate Limiter with Redis client
        redis_client = Redis.from_url(settings.redis_url)
        await rate_limiter.init_limiter(redis_client)
        logger.info("Rate limiter initialized.")

        logger.info("Wellora API startup complete.")
        yield 
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Wellora API...")
        await cache_manager.disconnect()
        logger.info("Cache manager disconnected.")
        logger.info("Wellora API shutdown complete.")


app = FastAPI(
    title="Wellora Smart Nutrition & Insights API",
    description="A multi-user, async, cached, and observable nutrition tracking API.",
    version="1.0.0",
    lifespan=lifespan, 
)


#  Middleware 

# CORS Middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate Limiting Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    if not client_ip:
        client_ip = request.client.host

    identifier = client_ip

    is_allowed, remaining, reset_time = await rate_limiter.is_allowed(identifier)

    #rate limit headers to the response
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset_time

    if not is_allowed:
        return JSONResponse(
            status_code=429, # Too Many Requests
            content={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": f"Rate limit exceeded. Try again in {reset_time - int(asyncio.get_event_loop().time())} seconds."}}
        )

    response = await call_next(request)

    #rate limit headers to the response after processing the request
    response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
    response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)

    return response


# Exception Handlers 
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": str(exc.status_code), "message": exc.detail}}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception for request {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An internal server error occurred."}}
    )


# API Routes 

# all API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(foods.router)
app.include_router(meals.router)
app.include_router(analytics.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)