"""Test script to check HuggingFace configuration"""
from app.config import settings

print("=" * 60)
print("HUGGINGFACE CONFIGURATION CHECK")
print("=" * 60)
print(f"USE_HUGGINGFACE: {settings.USE_HUGGINGFACE} (type: {type(settings.USE_HUGGINGFACE)})")
print(f"HUGGINGFACE_API_KEY: {'set' if settings.HUGGINGFACE_API_KEY else 'NOT SET'}")
print(f"HUGGINGFACE_MODEL: {settings.HUGGINGFACE_MODEL}")
print("=" * 60)

if settings.USE_HUGGINGFACE:
    print("✅ HuggingFace is ENABLED")
else:
    print("❌ HuggingFace is DISABLED")
    print("\nTo enable HuggingFace, set USE_HUGGINGFACE=True in .env")
