"""
ZAA - Main FastAPI Application
The Voice-First AI Agricultural Exchange for Northern Ghana
"""

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


from routers import whatsapp_router, marketplace
from database import init_db
from services.scheduler import start_price_updates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🌾 ZAA starting up...")
    await init_db()
    try:
        start_price_updates()
    except Exception as e:
        logger.warning(f"⚠️ Scheduler startup failed: {str(e)}")
    logger.info("✅ ZAA is live!")
    yield
    logger.info("🛑 ZAA shutting down...")

app = FastAPI(
    title="ZAA API",
    description="Voice-First AI Agricultural Exchange for Northern Ghana",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - Allow buyer dashboard to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(whatsapp_router, prefix="/api/v1/whatsapp", tags=["WhatsApp"])
app.include_router(marketplace.router, prefix="/api/v1/marketplace", tags=["Marketplace"])

@app.get("/")
async def root():
    return {
        "message": "🌾 ZAA is running",
        "version": "1.0.0",
        "region": "Northern Ghana",
        "languages": ["dag", "tw", "gon", "ha", "en"],
        "endpoints": {
            "whatsapp_webhook": "/api/v1/whatsapp/webhook",
            "listings": "/api/v1/marketplace/listings",
            "prices": "/api/v1/marketplace/prices/current",
            "analytics": "/api/v1/marketplace/analytics/overview"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "zaa-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
