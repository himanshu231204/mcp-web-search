import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_config
from app.routes import mcp

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

config = get_config()

app = FastAPI(
    title=config.APP_NAME,
    version=config.VERSION,
    description="Remote MCP Web Search Server",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mcp.mcp_router, prefix="/mcp")
app.include_router(mcp.router, prefix="/mcp")


@app.get("/")
async def root():
    return {"name": config.APP_NAME, "version": config.VERSION, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=True)
