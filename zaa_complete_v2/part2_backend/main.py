"""
ZAA - Main FastAPI Application
The Voice-First AI Agricultural Exchange for Northern Ghana
"""

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging

from routers import whatsapp, marketplace
from services.database import init_db

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
    allow_origins=["*"],  # In production, restrict to your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["WhatsApp"])
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
