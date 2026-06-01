import os
from pydantic_settings import BaseSettings

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")

class Settings(BaseSettings):
    ORACLE_HOST: str
    ORACLE_PORT: int = 1521
    ORACLE_SERVICE: str
    ORACLE_USER: str
    ORACLE_PASSWORD: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLIC_KEY: str
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID: str = ""

    class Config:
        env_file = ENV_PATH

settings = Settings()