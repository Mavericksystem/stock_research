from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Market Explanation Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str

    TIINGO_API_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()