from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    host: str = "localhost"
    port: int = 8000
    debug: bool = True

    # Database
    database_url: str
    test_database_url: Optional[str] = None 

    # Redis
    redis_url: str

    # JWT
    jwt_secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  


    class Config:
        env_file = ".env" 


settings = Settings()