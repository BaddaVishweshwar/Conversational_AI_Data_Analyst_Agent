
import sys
import os
from sqlalchemy import create_engine

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.config import settings
from app.database import Base, engine
from app.models import User
from app.services.auth_service import create_user
from sqlalchemy.orm import sessionmaker

def init_db_manual():
    print(f"🔌 Connecting to: {settings.DATABASE_URL}")
    
    # Create tables
    print("🔨 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created.")
    
    # Create default user
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    existing = db.query(User).filter(User.email == "admin@example.com").first()
    if not existing:
        print("👤 Creating default admin user...")
        user = create_user(db, "admin@example.com", "admin", "admin123")
        user.is_admin = True
        user.is_super_admin = True
        db.commit()
        print(f"✅ User created: {user.email} / admin123")
    else:
        print("ℹ️ Default user exists. Updating password...")
        from app.services.auth_service import get_password_hash
        existing.hashed_password = get_password_hash("admin123")
        db.commit()
        print(f"✅ User password updated: {existing.email} / admin123")
        
    db.close()

if __name__ == "__main__":
    init_db_manual()
