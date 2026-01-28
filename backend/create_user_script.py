import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import User
from app.services.auth_service import get_password_hash

def create_user():
    db = SessionLocal()
    email = "vishuvishweshwar77@gmail.com"
    password = "password123" 
    username = "vishu"
    
    try:
        print(f"Checking for user {email}...")
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"User {email} already exists.")
            # Reset password just in case
            user.hashed_password = get_password_hash(password)
            user.is_admin = True
            user.is_super_admin = True
            db.commit()
            print(f"Updated existing user password to '{password}' and granted admin rights.")
            return

        print(f"Creating user {email}...")
        hashed = get_password_hash(password)
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed,
            is_active=True,
            is_admin=True,
            is_super_admin=True 
        )
        db.add(new_user)
        db.commit()
        print(f"User created successfully.")
        print(f"Email: {email}")
        print(f"Password: {password}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_user()
