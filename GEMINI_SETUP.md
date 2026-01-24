# Gemini API Setup Instructions

## Get Your Free Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the API key

## Add to .env File

Open `/Users/vishu/Desktop/AI Data/backend/.env` and add:

```
GEMINI_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual API key.

## That's It!

The system will automatically:
- Use Gemini for SQL generation (much better accuracy)
- Fall back to local Mistral if Gemini fails
- Give you CamelAI-level results

## Test After Adding Key

Try these queries:
- "show me top 10 sales"
- "what is the correlation between TV budget and sales"
- "group sales by radio budget ranges"
- "find rows where newspaper budget is less than average"

You should get much more accurate results!
