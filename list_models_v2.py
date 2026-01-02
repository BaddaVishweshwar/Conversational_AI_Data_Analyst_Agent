import google.generativeai as genai
import os
import sys
from dotenv import load_dotenv

print("STEP 1: Starting script...")
load_dotenv("backend/.env")
api_key = os.getenv("GOOGLE_API_KEY")
print(f"STEP 2: Found API Key: {api_key[:5]}...")

print("STEP 3: Configuring genai...")
genai.configure(api_key=api_key)

print("STEP 4: Attempting to list models...")
try:
    for m in genai.list_models():
        print(f" - Found model: {m.name}")
    print("STEP 5: Success listing models.")
except Exception as e:
    print(f"STEP 5: ERROR: {e}", file=sys.stderr)
