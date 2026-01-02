import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")
api_key = os.getenv("GOOGLE_API_KEY")
print(f"Checking with key: {api_key[:5]}...")
genai.configure(api_key=api_key)

try:
    models = genai.list_models()
    count = 0
    for m in models:
        print(f"Model: {m.name}")
        count += 1
    print(f"Total models found: {count}")
except Exception as e:
    print(f"Error listing models: {e}")
