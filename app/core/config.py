import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_NAME: str = "MCP Web Search Server"
    VERSION: str = "1.0.0"
    
    HOST: str = "0.0.0.0"
    PORT: int = 10000
    
    DEFAULT_NUM_RESULTS: int = 5
    MAX_NUM_RESULTS: int = 20
    
    FETCH_TIMEOUT: int = 10
    SEARCH_TIMEOUT: int = 10
    
    MAX_CONTENT_LENGTH: int = 5000
    
    CACHE_SIZE: int = 100
    
    RATE_LIMIT_PER_MINUTE: int = 20


@lru_cache
def get_config() -> Config:
    return Config()