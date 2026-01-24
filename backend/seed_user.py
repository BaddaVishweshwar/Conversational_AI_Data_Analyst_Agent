from app.database import SessionLocal, init_db
from app.services.auth_service import create_user
from app.models import User

def seed_default_user():
    init_db()
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if user:
            print("User admin@example.com already exists.")
            return

        print("Creating default user...")
        create_user(
            db=db,
            email="admin@example.com",
            username="admin",
            password="password123"
        )
        print("✅ User created successfully!")
        print("Email: admin@example.com")
        print("Password: password123")
    except Exception as e:
        print(f"❌ Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_default_user()
