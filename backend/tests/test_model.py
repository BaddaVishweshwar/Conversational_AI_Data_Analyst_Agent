
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load env from backend root
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, '.env'))

from app.services.gemini_service import gemini_service
import google.generativeai as genai

async def test_ping():
    print(f"Testing Model: {gemini_service.model_name}")
    try:
        model = genai.GenerativeModel(gemini_service.model_name)
        response = model.generate_content("Hello, can you hear me?")
        print(f"SUCCESS. Response: {response.text}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    asyncio.run(test_ping())
