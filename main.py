import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import db_manager
from routes import wallet, transactions, ml, weather

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    await db_manager.connect()
    yield
    # Shutdown: Close DB client
    await db_manager.close()

app = FastAPI(
    title="VoxPay AI — FinTechathon Backend API",
    description=(
        "Production-grade backend for VoxPay AI: voice-first Mobile Financial Services, "
        "AI Alternative Credit Scoring, automated disaster loan protection, and e-CNY cross-border settlement."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Vite dev server and production deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(wallet.router)
app.include_router(transactions.router)
app.include_router(ml.router)
app.include_router(weather.router)

@app.get("/", tags=["Health"])
async def root():
    return {
        "project": "VoxPay AI",
        "competition": "Shenzhen International FinTech Competition (FinTechathon) 2026",
        "status": "online",
        "database": "MongoDB (Active)" if db_manager.is_connected else "In-Memory Resilient Mode",
        "interactive_docs": "/docs"
    }

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "mongodb_connected": db_manager.is_connected
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
