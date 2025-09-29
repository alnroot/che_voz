from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from config.settings import settings
from api.routes import health, agents, conversations, static
from api.websockets import handlers as ws_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ElevenLabs Voice Assistant API",
    description="Clean API for real-time voice conversations with ElevenLabs agents",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Include routes
app.include_router(static.router)
app.include_router(health.router)
app.include_router(agents.router)
app.include_router(conversations.router)
app.include_router(ws_handlers.router)


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    uvicorn.run(app, host=settings.host, port=settings.port)