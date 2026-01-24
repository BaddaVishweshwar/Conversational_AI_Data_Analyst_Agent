from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from app.database import init_db
from app.routes import auth, datasets, queries, connections, dashboards, conversations, admin, simple_queries

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Free, open-source AI-powered business analytics platform"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Request Completed: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request Failed: {e}")
        raise e

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(datasets.router, prefix="/api", tags=["datasets"])
app.include_router(queries.router, prefix="/api", tags=["queries"])
app.include_router(simple_queries.router, prefix="/api", tags=["simple"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(connections.router, prefix="/api", tags=["connections"])
app.include_router(dashboards.router, prefix="/api", tags=["dashboards"])
app.include_router(admin.router, prefix="/api", tags=["admin"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and create upload directory"""
    init_db()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"📊 Ollama host: {settings.OLLAMA_HOST}")
    print(f"🤖 Model: {settings.OLLAMA_MODEL}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.services.ollama_service import ollama_service
    
    try:
        ai_available = ollama_service.check_availability()
    except Exception as e:
        ai_available = False
        print(f"AI service error: {e}")
    
    return {
        "status": "healthy",
        "ai_available": ai_available,
        "model": ollama_service.model_name,
        "provider": ollama_service.provider
    }
