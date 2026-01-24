"""
Simple Working Query Endpoint

This endpoint bypasses the broken V3/V4 pipelines and provides
a working query interface with visualizations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import time
import logging

from ..database import get_db
from ..models import User, Dataset, Query
from ..routes.auth import get_current_user
from ..services.data_service import data_service
from ..services.visualization_service import visualization_service
from ..services.ollama_service import ollama_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simple", tags=["Simple Queries"])


class SimpleQueryRequest(BaseModel):
    dataset_id: int
    query: str


@router.post("/ask")
async def simple_ask(
    request: SimpleQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simple working query endpoint that actually generates visualizations.
    """
    start_time = time.time()
    
    # Get dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create query record
    query_record = Query(
        natural_language_query=request.query,
        user_id=current_user.id,
        dataset_id=dataset.id,
        status="pending"
    )
    db.add(query_record)
    db.commit()
    db.refresh(query_record)
    
    try:
        # Load data
        logger.info(f"Loading dataset from {dataset.file_path}")
        df = data_service.parse_file(dataset.file_path, dataset.file_type)
        logger.info(f"Loaded {len(df)} rows, columns: {list(df.columns)}")
        
        # Generate SQL using Gemini API (much better than local Mistral)
        columns = list(df.columns)
        column_info = ", ".join([f"{col} ({df[col].dtype})" for col in columns])
        sample_row = df.iloc[0].to_dict()
        
        # Build optimized prompt for Gemini
        prompt = f"""You are an expert SQL query generator. Generate a DuckDB SQL query to answer the user's question.

**Database Schema:**
Table: dataset
Columns: {column_info}
Sample row: {sample_row}

**User Question:** {request.query}

**Instructions:**
1. Return ONLY the SQL query, no explanations
2. Use exact column names: {', '.join(columns)}
3. Table name must be 'dataset'
4. For "top N" or "highest", use ORDER BY DESC LIMIT N
5. For "average" or "mean", use AVG()
6. For "total" or "sum", use SUM()
7. For "count", use COUNT()
8. Add appropriate WHERE clauses for filtering
9. Use proper aggregations and GROUP BY when needed

**Examples:**
Q: show top 5 sales
A: SELECT * FROM dataset ORDER BY Sales DESC LIMIT 5

Q: what is average sales
A: SELECT AVG(Sales) as average_sales FROM dataset

Q: show data where TV > 200
A: SELECT * FROM dataset WHERE TV > 200

Q: total sales by radio budget ranges
A: SELECT CASE WHEN Radio < 20 THEN 'Low' WHEN Radio < 40 THEN 'Medium' ELSE 'High' END as radio_range, SUM(Sales) as total_sales FROM dataset GROUP BY radio_range

Generate the SQL query:"""

        sql = None
        max_retries = 2
        
        # Try Gemini API first
        from ..config import settings
        if settings.GEMINI_API_KEY:
            for attempt in range(max_retries):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    model = genai.GenerativeModel(settings.GEMINI_MODEL)
                    
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            'temperature': 0.1,
                            'max_output_tokens': 500,
                        }
                    )
                    
                    raw_sql = response.text.strip()
                    
                    # Clean up the SQL
                    sql = raw_sql
                    
                    # Remove markdown
                    if '```sql' in sql:
                        sql = sql.split('```sql')[1].split('```')[0].strip()
                    elif '```' in sql:
                        sql = sql.split('```')[1].split('```')[0].strip()
                    
                    # Remove common prefixes
                    prefixes = ['SQL:', 'Query:', 'A:', 'Answer:', 'SELECT']
                    for prefix in prefixes:
                        if sql.startswith(prefix) and prefix != 'SELECT':
                            sql = sql[len(prefix):].strip()
                    
                    # Add SELECT back if removed
                    if not sql.upper().startswith('SELECT'):
                        sql = 'SELECT ' + sql
                    
                    # Remove trailing semicolons
                    sql = sql.rstrip(';').strip()
                    
                    # Remove any text after the SQL
                    if '\n\n' in sql:
                        sql = sql.split('\n\n')[0].strip()
                    
                    # Validate SQL
                    sql_upper = sql.upper()
                    if 'SELECT' in sql_upper and 'FROM' in sql_upper and 'DATASET' in sql_upper:
                        logger.info(f"✅ Gemini generated SQL (attempt {attempt + 1}): {sql}")
                        break
                    else:
                        logger.warning(f"Invalid SQL from Gemini (attempt {attempt + 1}): {sql}")
                        sql = None
                        
                except Exception as e:
                    logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")
                    sql = None
        
        # Fallback to local Mistral if Gemini fails or no API key
        if not sql:
            logger.info("Falling back to local Mistral model")
            for attempt in range(max_retries):
                try:
                    import ollama
                    response = ollama.generate(
                        model='mistral:7b',
                        prompt=prompt,
                        options={'temperature': 0.1, 'num_predict': 100}
                    )
                    raw_sql = response['response'].strip()
                    
                    # Clean up the SQL (same logic as above)
                    sql = raw_sql
                    if '```sql' in sql:
                        sql = sql.split('```sql')[1].split('```')[0].strip()
                    elif '```' in sql:
                        sql = sql.split('```')[1].split('```')[0].strip()
                    
                    prefixes = ['SQL:', 'Query:', 'A:', 'Answer:']
                    for prefix in prefixes:
                        if sql.startswith(prefix):
                            sql = sql[len(prefix):].strip()
                    
                    sql = sql.rstrip(';').strip()
                    
                    if '\n\n' in sql:
                        sql = sql.split('\n\n')[0].strip()
                    
                    sql_upper = sql.upper()
                    if 'SELECT' in sql_upper and 'FROM' in sql_upper and 'DATASET' in sql_upper:
                        logger.info(f"Generated SQL with Mistral (attempt {attempt + 1}): {sql}")
                        break
                    else:
                        sql = None
                        
                except Exception as e:
                    logger.error(f"Mistral error (attempt {attempt + 1}): {e}")
                    sql = None
        
        # Final fallback
        if not sql:
            logger.warning("All SQL generation attempts failed, using fallback")
            sql = "SELECT * FROM dataset LIMIT 100"
        
        # Execute SQL using DuckDB
        import duckdb
        con = duckdb.connect(':memory:')
        con.register('dataset', df)
        
        try:
            result = con.execute(sql).fetchdf()
            result_data = result.to_dict('records')
            logger.info(f"✅ Query executed: {len(result_data)} rows returned")
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            logger.error(f"Failed SQL was: {sql}")
            # Fallback to all data
            sql = "SELECT * FROM dataset LIMIT 100"
            result_data = df.to_dict('records')[:100]
        
        con.close()
        
        # Determine chart type based on query
        query_lower = request.query.lower()
        chart_type = 'scatter'  # Default
        if 'bar' in query_lower or 'column' in query_lower:
            chart_type = 'bar'
        elif 'line' in query_lower or 'trend' in query_lower:
            chart_type = 'line'
        elif 'scatter' in query_lower or 'plot' in query_lower or 'vs' in query_lower:
            chart_type = 'scatter'
        
        # Generate visualization
        logger.info(f"Generating {chart_type} visualization...")
        viz_result = visualization_service.generate_chart(
            data=result_data[:100],  # Limit for performance
            columns=list(result_data[0].keys()) if result_data else columns,
            chart_type=chart_type,
            title=request.query
        )
        
        python_chart = None
        if viz_result['success']:
            python_chart = viz_result['image']
            logger.info(f"✅ Generated visualization ({len(python_chart)} chars)")
        
        # Update query record
        execution_time = int((time.time() - start_time) * 1000)
        query_record.generated_sql = sql
        query_record.result_data = result_data
        query_record.python_chart = python_chart
        query_record.visualization_config = {
            "type": chart_type,
            "columns": list(result_data[0].keys()) if result_data else columns
        }
        query_record.insights = f"Showing {len(result_data)} rows from {dataset.name}"
        query_record.execution_time = execution_time
        query_record.status = "success"
        
        db.commit()
        db.refresh(query_record)
        
        return query_record
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        query_record.status = "error"
        query_record.error_message = str(e)
        db.commit()
        db.refresh(query_record)
        raise HTTPException(status_code=500, detail=str(e))
