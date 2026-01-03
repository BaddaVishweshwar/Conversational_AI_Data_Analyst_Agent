"""
Database Migration Script for Professional Backend V4

This script creates the new tables needed for the semantic layer and multi-agent system.
Run this after updating models.py to create the new tables.
"""

from sqlalchemy import create_engine
from app.database import Base
from app.models import (
    DatasetSchema,
    ColumnProfile,
    QueryTemplate,
    SemanticMapping
)
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Create new tables for semantic layer"""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        logger.info("Creating new tables for semantic layer...")
        
        # Create all tables (will only create new ones)
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Migration complete! New tables created:")
        logger.info("  - dataset_schemas")
        logger.info("  - column_profiles")
        logger.info("  - query_templates")
        logger.info("  - semantic_mappings")
        
        logger.info("\nThese tables support:")
        logger.info("  • Schema metadata with embeddings for RAG")
        logger.info("  • Column statistical profiles")
        logger.info("  • Query template library for few-shot learning")
        logger.info("  • Business term definitions and mappings")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    run_migration()
