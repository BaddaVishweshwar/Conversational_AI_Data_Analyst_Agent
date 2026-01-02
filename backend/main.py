from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.config import settings
from app.database import init_db
from app.routes import auth, datasets, queries, connections, dashboards, conversations, admin

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

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(datasets.router, prefix="/api", tags=["datasets"])
app.include_router(queries.router, prefix="/api", tags=["queries"])
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
    from app.services.gemini_service import gemini_service
    
    try:
        ai_available = gemini_service.check_availability()
    except Exception as e:
        ai_available = False
        print(f"AI service error: {e}")
    
    return {
        "status": "healthy",
        "ai_available": ai_available,
        "model": settings.GEMINI_MODEL
    }
