from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Market Explanation Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str
    FINNHUB_API_KEY: str
    TIINGO_API_KEY: str

    # --Nvidia NIM--
    NVIDIA_NIM_API_KEY: str
    NVIDIA_NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_NIM_MODEL: str = "nvidia/llama-3.3-nemotron-super-49b-v1"


    # Agent config
    AGENT_TEMPERATURE: float = 0.1
    AGENT_MAX_TOKENS: int =1024
    AGENT_TOP_p: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()