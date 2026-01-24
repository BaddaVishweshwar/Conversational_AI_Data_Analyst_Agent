
import sys
import os

# Add backend to path so we can import app
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.services.auth_service import get_password_hash, verify_password
    
    pwd = "admin123"
    print(f"Testing password: {pwd}")
    
    # 1. Hash
    hashed = get_password_hash(pwd)
    print(f"Generated hash: {hashed}")
    
    # 2. Verify
    is_valid = verify_password(pwd, hashed)
    print(f"Verification result: {is_valid}")
    
    if is_valid:
        print("✅ Password hashing/verification works within python environment.")
    else:
        print("❌ Password verification FAILED.")
        
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Exception: {e}")

# 3. Check DB
print("\n--- Inspecting Database ---")
from sqlalchemy import create_engine, text
db_path = "/Users/vishu/Desktop/AI Data/analytics.db"
engine = create_engine(f"sqlite:///{db_path}")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT email, hashed_password FROM users WHERE email='admin@example.com'"))
        row = result.fetchone()
        if row:
            print(f"User found: {row[0]}")
            print(f"Stored Hash: {row[1]}")
            # Verify stored hash against pwd
            valid_stored = verify_password(pwd, row[1])
            print(f"Stored hash is valid: {valid_stored}")
        else:
            print("❌ User admin@example.com NOT found in DB!")
except Exception as e:
    print(f"DB Error: {e}")
