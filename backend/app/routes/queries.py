from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
import time
from ..database import get_db
from ..models import User, Dataset, Query
from ..routes.auth import get_current_user
from ..services.ai_service import ai_service
from ..services.analytics_service_v2 import analytics_service_v2
from ..services.data_service import data_service
from ..services.visualization_service import visualization_service
from ..services.knowledge_service import knowledge_service

router = APIRouter(prefix="/queries", tags=["Queries"])


# Pydantic schemas
class QueryRequest(BaseModel):
    dataset_id: int
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    id: int
    natural_language_query: str
    generated_sql: Optional[str]
    result_data: Optional[Any]
    visualization_config: Optional[Any]
    python_chart: Optional[str]
    execution_time: Optional[int]
    status: Optional[str]
    error_message: Optional[str]
    insights: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class QueryHistoryResponse(BaseModel):
    id: int
    natural_language_query: str
    status: str
    created_at: datetime
    dataset_id: Optional[int]
    session_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class QueryUpdate(BaseModel):
    visualization_config: Optional[dict] = None
    insights: Optional[str] = None
    status: Optional[str] = None


class ExecuteSQLRequest(BaseModel):
    dataset_id: int
    sql: str


@router.post("/execute", response_model=QueryResponse)
async def execute_raw_sql(
    request: ExecuteSQLRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute raw SQL against a dataset"""
    start_time = time.time()
    
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create query record
    query = Query(
        natural_language_query=f"Direct SQL: {request.sql[:50]}...",
        generated_sql=request.sql,
        user_id=current_user.id,
        dataset_id=dataset.id,
        status="pending"
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    
    try:
        # Prepare execution context
        df = None
        connection = None
        
        if dataset.connection_id:
            from ..models import DataConnection
            connection = db.query(DataConnection).filter(DataConnection.id == dataset.connection_id).first()
        else:
            df = data_service.parse_file(dataset.file_path, dataset.file_type)
            
        execution_result = data_service.execute_sql_query(
            sql_query=request.sql,
            df=df,
            connection=connection
        )
        
        if not execution_result["success"]:
            query.status = "error"
            query.error_message = execution_result["error"]
            db.commit()
            db.refresh(query)
            return query

        # Prepare visualization config
        viz_config = data_service.prepare_visualization_config(
            result_data=execution_result["data"],
            columns=execution_result["columns"]
        )
        
        # Update query
        execution_time = int((time.time() - start_time) * 1000)
        query.result_data = execution_result["data"]
        query.visualization_config = viz_config
        query.execution_time = execution_time
        query.status = "success"
        
        db.commit()
        db.refresh(query)
        return query
        
    except Exception as e:
        query.status = "error"
        query.error_message = str(e)
        db.commit()
        db.refresh(query)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=QueryResponse, status_code=status.HTTP_201_CREATED)
async def ask_question(
    query_request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a natural language question about a dataset using multi-agent pipeline"""
    
    start_time = time.time()
    
    # Get dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == query_request.dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create query record
    query = Query(
        natural_language_query=query_request.query,
        user_id=current_user.id,
        dataset_id=dataset.id,
        session_id=query_request.session_id,
        status="pending"
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    
    try:
        # Prepare execution context
        df = None
        connection = None
        
        if dataset.connection_id:
            from ..models import DataConnection
            connection = db.query(DataConnection).filter(DataConnection.id == dataset.connection_id).first()
        else:
            df = data_service.parse_file(dataset.file_path, dataset.file_type)
        
        # Execute multi-agent analytics pipeline
        analysis_response = analytics_service_v2.analyze(
            query=query_request.query,
            dataset=dataset,
            df=df,
            connection=connection
        )
        
        # Check if analysis succeeded
        if not analysis_response.execution_result.success:
            query.status = "error"
            query.error_message = analysis_response.execution_result.error
            query.intent = analysis_response.intent.intent.value
            query.reasoning_steps = analysis_response.reasoning_steps
            db.commit()
            db.refresh(query)
            return query
        
        # Generate Python visualization if needed
        python_viz = {"success": False, "image": None}
        if analysis_response.analysis_plan.python_code:
            python_viz = visualization_service.generate_custom_chart(
                data=analysis_response.execution_result.data,
                python_code=analysis_response.analysis_plan.python_code,
                title=query_request.query
            )
        
        # Convert insights to text format
        insights_text = f"""### 📊 Direct Answer
{analysis_response.insights.direct_answer}

### 🔍 What the Data Shows
{chr(10).join('- ' + fact for fact in analysis_response.insights.what_data_shows)}

### 💡 Why This Happened
{chr(10).join('- ' + reason for reason in analysis_response.insights.why_it_happened)}

### 🎯 Business Implications
{chr(10).join('- ' + impl for impl in analysis_response.insights.business_implications)}
"""
        
        # Prepare visualization config for frontend
        viz_config = {
            "type": analysis_response.visualization.chart_type.value,
            "xAxis": analysis_response.visualization.x_axis,
            "yAxis": analysis_response.visualization.y_axis,
            "data": analysis_response.execution_result.data,
            "columns": analysis_response.execution_result.columns
        }
        
        # Update query with all results
        execution_time = int((time.time() - start_time) * 1000)
        query.generated_sql = analysis_response.analysis_plan.sql_query
        query.generated_code = analysis_response.analysis_plan.python_code
        query.result_data = analysis_response.execution_result.data
        query.visualization_config = viz_config
        query.python_chart = python_viz["image"] if python_viz["success"] else None
        query.insights = insights_text
        query.execution_time = execution_time
        query.status = "success"
        
        # New multi-agent fields
        query.intent = analysis_response.intent.intent.value
        query.analysis_plan = {
            "steps": [
                {
                    "step_number": step.step_number,
                    "operation": step.operation,
                    "description": step.description,
                    "columns_involved": step.columns_involved
                }
                for step in analysis_response.analysis_plan.steps
            ],
            "expected_columns": analysis_response.analysis_plan.expected_columns
        }
        query.schema_analysis = {
            "total_rows": analysis_response.schema_analysis.total_rows if analysis_response.schema_analysis else 0,
            "numeric_columns": analysis_response.schema_analysis.numeric_columns if analysis_response.schema_analysis else [],
            "categorical_columns": analysis_response.schema_analysis.categorical_columns if analysis_response.schema_analysis else [],
            "datetime_columns": analysis_response.schema_analysis.datetime_columns if analysis_response.schema_analysis else [],
            "data_quality_score": analysis_response.schema_analysis.data_quality_score if analysis_response.schema_analysis else 0.0
        }
        query.reasoning_steps = analysis_response.reasoning_steps
        query.metrics_used = analysis_response.execution_result.metrics
        
        db.commit()
        db.refresh(query)
        
        # Save to knowledge base for RAG
        knowledge_service.add_expertise(
            query=query_request.query,
            sql=analysis_response.analysis_plan.sql_query,
            schema=str(dataset.schema),
            dataset_id=dataset.id,
            user_id=current_user.id
        )
        
        return query
        
    except Exception as e:
        query.status = "error"
        query.error_message = str(e)
        db.commit()
        db.refresh(query)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/{query_id}/retry", response_model=QueryResponse)
async def retry_query(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry a failed query by re-generating SQL and re-executing"""
    
    start_time = time.time()
    
    # Get query and ensure it belongs to user
    query = db.query(Query).filter(
        Query.id == query_id,
        Query.user_id == current_user.id
    ).first()
    
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
        
    dataset = query.dataset
    if not dataset:
         raise HTTPException(status_code=404, detail="Associated dataset not found")

    # Reset status
    query.status = "pending"
    query.error_message = None
    db.commit()
    
    try:
        # Retrieve related expertise for RAG
        related_expertise = knowledge_service.get_related_expertise(
            query=query.natural_language_query, 
            dataset_id=dataset.id
        )
        
        # Generator analysis plan (SQL + Python) - RE-GENERATE to fix bad SQL
        analysis_result = ai_service.generate_analysis_plan(
            natural_query=query.natural_language_query,
            schema=dataset.schema,
            sample_data=dataset.sample_data,
            related_expertise=related_expertise
        )
        
        if not analysis_result["success"]:
            query.status = "error"
            query.error_message = analysis_result["error"]
            db.commit()
            db.refresh(query)
            return query
        
        generated_sql = analysis_result["sql"]
        generated_python = analysis_result["python"]
        query.generated_sql = generated_sql
        query.generated_code = generated_python
        query.analysis_strategy = analysis_result.get("strategy")
        
        # Validate SQL
        validation = data_service.validate_sql(generated_sql)
        if not validation["valid"]:
            query.status = "error"
            query.error_message = validation["error"]
            db.commit()
            db.refresh(query)
            return query
        
        # Prepare execution context
        df = None
        connection = None
        
        if dataset.connection_id:
            from ..models import DataConnection
            connection = db.query(DataConnection).filter(DataConnection.id == dataset.connection_id).first()
        else:
            df = data_service.parse_file(dataset.file_path, dataset.file_type)
            
        execution_result = data_service.execute_sql_query(
            sql_query=generated_sql,
            df=df,
            connection=connection
        )
        
        if not execution_result["success"]:
            query.status = "error"
            query.error_message = execution_result["error"]
            db.commit()
            db.refresh(query)
            return query
        
        # Prepare visualization config
        viz_config = data_service.prepare_visualization_config(
            result_data=execution_result["data"],
            columns=execution_result["columns"]
        )
        
        # Generate Chart
        python_viz = {"success": False, "image": None}
        has_code = False
        if generated_python:
            cleaned_code = "\n".join([line for line in generated_python.split("\n") if line.strip() and not line.strip().startswith("#")])
            if cleaned_code.strip():
                has_code = True
        
        if has_code:
            python_viz = visualization_service.generate_custom_chart(
                data=execution_result["data"],
                python_code=generated_python,
                title=query.natural_language_query
            )
        else:
            if viz_config:
                viz_config["type"] = "table"
                viz_config.pop("xAxis", None)
                viz_config.pop("yAxis", None)
        
        # Generate insights
        insights = None
        try:
            insights = ai_service.generate_insights(
                query=query.natural_language_query,
                result_data=execution_result["data"],
                chart_type=viz_config["type"]
            )
        except Exception as e:
            print(f"Error generating insights: {e}")
        
        # Update query with results
        execution_time = int((time.time() - start_time) * 1000)
        query.result_data = execution_result["data"]
        query.visualization_config = viz_config
        query.python_chart = python_viz["image"] if python_viz["success"] else None
        query.insights = insights
        query.execution_time = execution_time
        query.status = "success"
        
        db.commit()
        db.refresh(query)
        
        # Add to knowledge base
        knowledge_service.add_expertise(
            query=query.natural_language_query,
            sql=generated_sql,
            schema=str(dataset.schema),
            dataset_id=dataset.id,
            user_id=current_user.id
        )
        
        response = QueryResponse.from_orm(query)
        response.insights = insights
        response.strategy = query.analysis_strategy
        
        return response

    except Exception as e:
        query.status = "error"
        query.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[QueryResponse])
async def get_query_history(
    dataset_id: Optional[int] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    order: str = "asc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get query history for current user, optionally filtered by dataset and session"""
    query = db.query(Query).filter(Query.user_id == current_user.id)
    
    if dataset_id:
        query = query.filter(Query.dataset_id == dataset_id)
        
    if session_id:
        query = query.filter(Query.session_id == session_id)
    
    if order == "desc":
        query = query.order_by(Query.created_at.desc())
    else:
        query = query.order_by(Query.created_at.asc())
        
    queries = query.limit(limit).all()
    
    return queries


@router.get("/sessions", response_model=List[dict])
async def get_chat_sessions(
    dataset_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of chat sessions with metadata"""
    # This query groups by session_id and returns the most recent message for each session
    # We'll use a slightly inefficient but simple approach first: distinct session_ids
    
    query = db.query(Query.session_id, Query.created_at, Query.natural_language_query, Query.dataset_id)\
        .filter(Query.user_id == current_user.id)\
        .filter(Query.session_id.isnot(None))
        
    if dataset_id:
        query = query.filter(Query.dataset_id == dataset_id)
        
    # Order by newest first
    results = query.order_by(Query.created_at.desc()).all()
    
    # Process in python to get unique sessions (deduplication)
    # We want the *latest* timestamp for each session to sort sessions
    sessions_map = {}
    for r in results:
        if r.session_id not in sessions_map:
            sessions_map[r.session_id] = {
                "session_id": r.session_id,
                "created_at": r.created_at,
                "first_query": r.natural_language_query,
                "dataset_id": r.dataset_id
            }
            
    return list(sessions_map.values())


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific chat session and all its queries"""
    # Delete all queries with this session_id for the current user
    # We use synchronize_session=False for bulk deletes usually, or query.delete()
    
    result = db.query(Query).filter(
        Query.session_id == session_id,
        Query.user_id == current_user.id
    ).delete(synchronize_session=False)
    
    db.commit()
    
    if result == 0:
        # Might want to check if it existed but belong to someone else, but 
        # for privacy/simplicity returning success or 404 is fine.
        # Here we just assume if nothing deleted, maybe it didn't exist, which is fine for idempotent delete.
        pass
    
    return None


@router.get("/{query_id}", response_model=QueryResponse)
async def get_query(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific query result"""
    query = db.query(Query).filter(
        Query.id == query_id,
        Query.user_id == current_user.id
    ).first()
    
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    return query


@router.patch("/{query_id}", response_model=QueryResponse)
async def update_query(
    query_id: int,
    query_data: QueryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update query metadata (e.g. tweaked visualization config)"""
    query = db.query(Query).filter(
        Query.id == query_id,
        Query.user_id == current_user.id
    ).first()
    
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    data = query_data.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(query, key, value)
    
    db.commit()
    db.refresh(query)
    return query
