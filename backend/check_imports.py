import sys
import os

sys.path.append(os.getcwd())

print("Testing imports...")
try:
    from app.services import analytics_service_v2
    print("✅ Successfully imported analytics_service_v2")
except Exception as e:
    print(f"❌ Import Failed: {e}")
    exit(1)
