import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

models_to_try = ['gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest']

for model_name in models_to_try:
    print(f"Testing model: {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, respond with 'SUCCESS'")
        print(f" - SUCCESS: {response.text}")
        break
    except Exception as e:
        print(f" - FAILED: {e}")
