import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key: {api_key[:5]}...")

genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello, respond with 'SUCCESS'")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
