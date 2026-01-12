"""Test login functionality"""
import requests
import json

# Test backend is running
try:
    response = requests.get("http://localhost:8000/api/auth/me", timeout=2)
    print(f"✅ Backend is running (status: {response.status_code})")
except Exception as e:
    print(f"❌ Backend connection failed: {e}")
    exit(1)

# Test login with existing account
print("\n" + "="*60)
print("TESTING LOGIN")
print("="*60)

test_credentials = [
    {"email": "vishuvishweshwar77@gmail.com", "password": "test123"},
    {"email": "test@example.com", "password": "test123"},
    {"email": "admin@test.com", "password": "admin123"},
]

for creds in test_credentials:
    print(f"\nTrying: {creds['email']}")
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            json=creds,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ LOGIN SUCCESS!")
            print(f"  Access Token: {data.get('access_token', 'N/A')[:50]}...")
            break
        else:
            print(f"  ❌ Failed: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*60)
