from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: str
    ENVIRONMENT: str
    BINANCE_API_KEY: str
    BINANCE_SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
