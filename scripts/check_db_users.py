
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.config import settings
from app.models import User

def check_db():
    print(f"🔌 Connecting to: {settings.DATABASE_URL}")
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Try a simple query
        result = db.execute(text("SELECT 1")).scalar()
        print("✅ Database connection successful.")
        
        # Check Users
        users = db.query(User).all()
        print(f"👥 Users found: {len(users)}")
        for u in users:
            print(f" - ID: {u.id}, Email: {u.email}, Active: {u.is_active}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    check_db()
