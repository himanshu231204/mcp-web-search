from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_NAME: str = os.getenv("APP_NAME", "MCP Web Search Server")
    VERSION: str = os.getenv("VERSION", "1.0.0")

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "10000"))

    DEFAULT_NUM_RESULTS: int = int(os.getenv("DEFAULT_NUM_RESULTS", "5"))
    MAX_NUM_RESULTS: int = int(os.getenv("MAX_NUM_RESULTS", "20"))

    FETCH_TIMEOUT: int = int(os.getenv("FETCH_TIMEOUT", "10"))
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "10"))
    MCP_REQUEST_TIMEOUT: int = int(os.getenv("MCP_REQUEST_TIMEOUT", "25"))
    SSE_HEARTBEAT_INTERVAL: int = int(os.getenv("SSE_HEARTBEAT_INTERVAL", "5"))

    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "5000"))

    CACHE_SIZE: int = int(os.getenv("CACHE_SIZE", "100"))

    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))


@lru_cache
def get_config() -> Config:
    return Config()
