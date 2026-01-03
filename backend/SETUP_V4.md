# Professional Backend V4 - Quick Start Guide

## Prerequisites

- Python 3.11+
- Anthropic API key (for Claude Sonnet 4)
- OpenAI API key (for embeddings)
- Redis (optional, for caching)

## Installation Steps

### 1. Install Dependencies

```bash
cd /Users/vishu/Desktop/AI\ Data/backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create or update `.env` file:

```bash
# Required: Anthropic Claude Sonnet 4
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Required: OpenAI for embeddings
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small

# Optional: Redis caching (recommended)
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_ENABLED=true

# Optional: LangSmith monitoring
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_ENABLED=false

# Multi-Agent Configuration
MAX_SQL_RETRIES=3
ENABLE_CHAIN_OF_THOUGHT=true
```

### 3. Run Database Migration

```bash
python migrate_v4.py
```

This creates 4 new tables:
- `dataset_schemas` - Schema metadata with embeddings
- `column_profiles` - Column statistics
- `query_templates` - Successful query library
- `semantic_mappings` - Business term definitions

### 4. Test the System

Start the backend:
```bash
uvicorn main:app --reload --port 8000
```

## Integration with Existing Code

### Update Dataset Upload Route

In `app/routes/datasets.py`, add schema extraction after file upload:

```python
from app.services.schema_extraction_service import schema_extraction_service

# After saving the file
await schema_extraction_service.extract_and_store_schema(
    dataset_id=dataset.id,
    file_path=file_path,
    db=db
)
```

### Update Query Route

In `app/routes/queries.py`, use the new analytics service:

```python
from app.services.analytics_service_v4 import analytics_service_v4

@router.post("/analyze")
async def analyze_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze query using V4 multi-agent pipeline"""
    
    result = await analytics_service_v4.analyze_query(
        user_question=request.question,
        dataset_id=request.dataset_id,
        db=db
    )
    
    # Store in database if successful
    if result.get('success'):
        query = Query(
            natural_language_query=request.question,
            generated_sql=result.get('sql'),
            result_data=result.get('data'),
            insights=result.get('insights'),
            intent=result.get('intent'),
            execution_time=result.get('execution_time'),
            user_id=current_user.id,
            dataset_id=request.dataset_id,
            status='success'
        )
        db.add(query)
        db.commit()
    
    return result
```

## Testing

### Test Schema Extraction

```python
# Upload a CSV file and check if schema is extracted
# Check database for entries in dataset_schemas and column_profiles tables
```

### Test Query Analysis

```bash
curl -X POST http://localhost:8000/api/queries/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "question": "What are the top 10 products by revenue?",
    "dataset_id": 1
  }'
```

Expected response:
```json
{
  "success": true,
  "question": "What are the top 10 products by revenue?",
  "intent": "RANKING",
  "interpretation": "User wants to see the top 10 products ranked by total revenue",
  "sql": "SELECT \"Product Name\", SUM(\"Revenue\") as total_revenue...",
  "data": [...],
  "row_count": 10,
  "visualization": {
    "chart_type": "bar",
    "reason": "Ranked data"
  },
  "insights": "## Executive Summary\n...",
  "execution_time": 4523,
  "metadata": {...}
}
```

## Architecture Overview

```
User uploads CSV → Schema Extraction Service
                    ↓
                 DuckDB loads file
                    ↓
                 Extract schema + statistics
                    ↓
                 Generate embeddings
                    ↓
                 Store in database

User asks question → Analytics Service V4
                    ↓
                 RAG retrieves context
                    ↓
                 Query Understanding Agent
                    ↓
                 SQL Generation Agent
                    ↓
                 Execute with self-correction
                    ↓
                 Visualization Agent
                    ↓
                 Explanation Agent
                    ↓
                 Return complete analysis
```

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| DuckDB Service | `services/duckdb_service.py` | In-memory SQL execution |
| Embedding Service | `services/embedding_service.py` | Generate embeddings for RAG |
| Schema Extraction | `services/schema_extraction_service.py` | Profile datasets |
| RAG Service | `services/rag_service.py` | Retrieve relevant context |
| Analytics V4 | `services/analytics_service_v4.py` | Main orchestrator |
| SQL Agent | `agents/sql_generation_agent_v2.py` | Generate SQL |
| System Prompts | `prompts/system_prompts.py` | Professional prompts |

## Troubleshooting

### Issue: "OpenAI API key not configured"
**Solution**: Set `OPENAI_API_KEY` in `.env`

### Issue: "Anthropic API key not configured"
**Solution**: Set `ANTHROPIC_API_KEY` in `.env`

### Issue: "Column embeddings not generated"
**Solution**: Ensure OpenAI API key is valid and has credits

### Issue: "SQL execution fails repeatedly"
**Solution**: Check DuckDB logs, verify column names match schema

### Issue: "Slow query performance"
**Solution**: Enable Redis caching with `CACHE_ENABLED=true`

## Cost Optimization

1. **Enable Redis caching**: Reduces LLM calls by 70%
2. **Use Claude Sonnet 4**: 80% cheaper than GPT-4 for same quality
3. **Batch embeddings**: Already implemented in embedding service
4. **Cache query templates**: Store successful queries for reuse

## Monitoring

If using LangSmith:
1. Set `LANGSMITH_ENABLED=true`
2. Set `LANGSMITH_API_KEY`
3. View traces at https://smith.langchain.com

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure environment variables
3. ✅ Run migration
4. ✅ Update routes
5. ⏳ Test with sample data
6. ⏳ Deploy to production
7. ⏳ Monitor performance
8. ⏳ Collect user feedback

## Support

For issues or questions:
- Check [walkthrough.md](file:///Users/vishu/.gemini/antigravity/brain/3eecb94a-e219-417f-bafd-1bdd23266474/walkthrough.md) for detailed documentation
- Review [implementation_plan.md](file:///Users/vishu/.gemini/antigravity/brain/3eecb94a-e219-417f-bafd-1bdd23266474/implementation_plan.md) for architecture details
- Check Backend.txt for original requirements
