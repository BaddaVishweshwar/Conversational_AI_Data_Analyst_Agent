
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("backend/.env")

token = os.getenv("GITHUB_TOKEN")
print(f"Token present: {bool(token)}")

try:
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token,
    )
    print("Client initialized successfully")
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "",
            },
            {
                "role": "user",
                "content": "What is the capital of France?",
            }
        ],
        model="gpt-4o",
        temperature=1,
        max_tokens=4096,
        top_p=1
    )

    print(response.choices[0].message.content)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
