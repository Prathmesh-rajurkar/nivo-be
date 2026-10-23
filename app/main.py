from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
from app.services.cache import cache_service
from app.api.v1.funds import router as funds_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await cache_service.connect()
    yield
    # Shutdown
    await cache_service.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Nivo - Indian Mutual Fund Research & Comparison Platform",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(funds_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nivo-backend"}


@app.get("/")
async def root():
    return {"message": "Nivo API", "version": settings.VERSION, "docs": "/docs"}