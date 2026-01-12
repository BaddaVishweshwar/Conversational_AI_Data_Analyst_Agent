from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Business Analytics AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./analytics.db"
    
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "deepseek-r1:7b"  # Balanced model - good accuracy + laptop-friendly
    OLLAMA_TIMEOUT: int = 120
    
    # Ollama Advanced Configuration
    OLLAMA_NUM_CTX: int = 4096  # Context window (optimized for 7B models)
    OLLAMA_NUM_GPU: int = 1  # Use GPU if available
    OLLAMA_NUM_THREAD: int = 8  # CPU threads
    OLLAMA_TEMPERATURE_SQL: float = 0.1  # Deterministic for SQL
    OLLAMA_TEMPERATURE_INSIGHTS: float = 0.3  # Slightly creative for insights
    OLLAMA_TEMPERATURE_CHAT: float = 0.7  # Conversational
    
    # HuggingFace Configuration
    HUGGINGFACE_API_KEY: Optional[str] = None
    HUGGINGFACE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"
    USE_HUGGINGFACE: bool = False
    HUGGINGFACE_TIMEOUT: int = 60
    HUGGINGFACE_MAX_TOKENS: int = 2048
    
    
    # Email Configuration
    GMAIL_USER: Optional[str] = None
    GMAIL_APP_PASSWORD: Optional[str] = None
    EMAIL_FROM_NAME: str = "AI Data Analyst"
    RESET_PASSWORD_URL: str = "http://localhost:5174/reset-password"
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    VECTOR_DB_DIR: str = "./vector_db"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set = {".csv", ".xlsx", ".xls", ".sas7bdat", ".parquet"}
    
    # DuckDB Configuration
    DUCKDB_MEMORY_LIMIT: str = "4GB"
    DUCKDB_THREADS: int = 4
    DUCKDB_TEMP_DIR: str = "./duckdb_temp"
    
    # Redis Cache Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_ENABLED: bool = True
    
    # Vector Database (Qdrant)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "dataset_schemas"
    QDRANT_USE_MEMORY: bool = True  # Use in-memory mode for development
    
    # Embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_BATCH_SIZE: int = 100
    
    # Monitoring & Logging
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "ai-data-analyst"
    LANGSMITH_ENABLED: bool = False
    
    # Multi-Agent Configuration
    MAX_SQL_RETRIES: int = 3
    AGENT_TIMEOUT: int = 120  # seconds
    ENABLE_CHAIN_OF_THOUGHT: bool = True
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
