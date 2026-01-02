"""
Conversations Router - API endpoints for conversational NLP

Handles multi-turn conversations with context awareness,
follow-up query resolution, and natural language responses.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

from ..database import get_db
from ..models import User, Dataset, Conversation, Message
from ..routes.auth import get_current_user
from ..services.conversation_service import conversation_service
from ..services.analytics_service_v2 import analytics_service_v2
from ..services.data_service import data_service
from ..services.response_formatter import response_formatter
from ..agents.query_resolver_agent import query_resolver

router = APIRouter(prefix="/conversations", tags=["Conversations"])


# Pydantic schemas
class ConversationCreate(BaseModel):
    dataset_id: int
    initial_query: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    dataset_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str


class ProcessingStep(BaseModel):
    status: str  # 'understanding', 'querying', 'generating_sql', 'executing', 'formatting', 'complete'
    message: str
    data: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    query_data: Optional[Dict[str, Any]]
    processing_steps: Optional[List[Dict[str, Any]]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[MessageResponse]


def clean_interpretation(interpretation):
    if not interpretation:
        return None
    # Pydantic v2 use model_dump(), v1 use dict()
    # Assuming v1 or v2 compatibility, try dict() first or basic getattr
    try:
        if hasattr(interpretation, 'model_dump'):
            return interpretation.model_dump()
        return interpretation.dict()
    except:
        return None

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    # Verify dataset ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create conversation
    conversation = conversation_service.create_conversation(
        db=db,
        user_id=current_user.id,
        dataset_id=request.dataset_id,
        initial_query=request.initial_query
    )
    
    # Add message count
    response = ConversationResponse.from_orm(conversation)
    response.message_count = len(conversation.messages)
    
    return response


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    dataset_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all conversations for the current user"""
    conversations = conversation_service.get_user_conversations(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
        limit=limit
    )
    
    # Add message counts
    responses = []
    for conv in conversations:
        response = ConversationResponse.from_orm(conv)
        response.message_count = len(conv.messages)
        responses.append(response)
    
    return responses


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a conversation with all messages"""
    conversation = conversation_service.get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv_response = ConversationResponse.from_orm(conversation)
    conv_response.message_count = len(conversation.messages)
    
    messages = [MessageResponse.from_orm(msg) for msg in conversation.messages]
    
    return ConversationDetailResponse(
        conversation=conv_response,
        messages=messages
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message in a conversation and get AI response
    
    This is the main conversational NLP endpoint that:
    1. Resolves context from conversation history
    2. Handles follow-up queries
    3. Generates natural language responses
    4. Returns processing steps for UI visualization
    """
    # Get conversation
    conversation = conversation_service.get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get dataset
    dataset = db.query(Dataset).filter(Dataset.id == conversation.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Add user message
    user_message = conversation_service.add_message(
        db=db,
        conversation_id=conversation_id,
        role='user',
        content=message.content
    )
    
    # Get conversation context
    context = conversation_service.get_conversation_context(
        db=db,
        conversation_id=conversation_id
    )
    
    # Processing steps to return
    processing_steps = []
    
    try:
        # Step 1: Resolve query with context
        processing_steps.append({
            "status": "understanding",
            "message": "Understanding your query...",
            "data": None
        })
        
        resolved = query_resolver.resolve_query(
            current_query=message.content,
            context=context
        )
        
        # Step 2: Show query understanding
        if resolved['is_followup']:
            processing_steps.append({
                "status": "context_resolved",
                "message": f"Detected follow-up query (intent: {resolved['intent']})",
                "data": {
                    "query": resolved['resolved_query'],
                    "references_previous": True
                }
            })
        else:
            processing_steps.append({
                "status": "new_query",
                "message": "Processing new query",
                "data": {"query": message.content}
            })
        
        # Step 3: Query database
        processing_steps.append({
            "status": "querying",
            "message": "Querying Database...",
            "data": None
        })
        
        # Prepare execution context
        df = None
        connection = None
        
        if dataset.connection_id:
            from ..models import DataConnection
            connection = db.query(DataConnection).filter(
                DataConnection.id == dataset.connection_id
            ).first()
        else:
            df = data_service.parse_file(dataset.file_path, dataset.file_type)
        
        # Execute analytics pipeline
        analysis_response = analytics_service_v2.analyze(
            query=resolved['resolved_query'],
            dataset=dataset,
            df=df,
            connection=connection
        )
        
        # Step 4: Show generated SQL
        processing_steps.append({
            "status": "generating_sql",
            "message": "Generated SQL",
            "data": {
                "sql": analysis_response.analysis_plan.sql_query
            }
        })
        
        # Check if analysis succeeded
        if not analysis_response.execution_result.success:
            # Add error step
            processing_steps.append({
                "status": "error",
                "message": f"Analysis failed: {analysis_response.execution_result.error}",
                "data": {"error": analysis_response.execution_result.error}
            })
            
            # Error response
            error_message = conversation_service.add_message(
                db=db,
                conversation_id=conversation_id,
                role='assistant',
                content=f"I encountered an error: {analysis_response.execution_result.error}\n\nI tried to self-correct but couldn't resolve the issue.",
                query_data={
                    "error": analysis_response.execution_result.error,
                    "generated_sql": analysis_response.analysis_plan.sql_query,
                    # Fallback for visualization to prevent UI crashes if it expects something
                    "visualizations": [],
                    "visualization": None
                },
                processing_steps=processing_steps
            )
            return MessageResponse.from_orm(error_message)
        
        # Step 5: Format response
        processing_steps.append({
            "status": "formatting",
            "message": "Formatting response...",
            "data": None
        })
        
        # Generate natural language response
        natural_response = response_formatter.format_response(
            query=message.content,
            result_data=analysis_response.execution_result.data,
            columns=analysis_response.execution_result.columns,
            intent=analysis_response.intent.intent.value
        )
        
        # Step 6: Complete
        processing_steps.append({
            "status": "complete",
            "message": "Analysis complete",
            "data": {
                "row_count": analysis_response.execution_result.row_count,
                "execution_time_ms": analysis_response.execution_result.execution_time_ms
            }
        })
        
        # Prepare query data for storage
        visualizations_data = []
        if analysis_response.visualization:
            # Handle list vs single object (just in case of mixed usage during migration)
            viz_list = analysis_response.visualization if isinstance(analysis_response.visualization, list) else [analysis_response.visualization]
            for viz in viz_list:
                visualizations_data.append({
                    "chart_type": viz.chart_type.value,
                    "x_axis": viz.x_axis,
                    "y_axis": viz.y_axis,
                    "title": viz.title,
                    "description": viz.description
                })

        query_data = {
            "generated_sql": analysis_response.analysis_plan.sql_query,
            "result_data": analysis_response.execution_result.data,
            "columns": analysis_response.execution_result.columns,
            "visualizations": visualizations_data, # New Plural Field
            # Keep legacy single field for backward compat if needed, or just let frontend handle new field
            "visualization": visualizations_data[0] if visualizations_data else None, 
            "intent": {
                "intent": analysis_response.intent.intent.value,
                "confidence": analysis_response.intent.confidence
            },
            "interpretation": clean_interpretation(analysis_response.interpretation),
            "insights": {
                "direct_answer": analysis_response.insights.direct_answer,
                "what_data_shows": analysis_response.insights.what_data_shows,
                "why_it_happened": analysis_response.insights.why_it_happened,
                "business_implications": analysis_response.insights.business_implications,
                "confidence": analysis_response.insights.confidence
            }
        }
        
        # Merge high-level steps with granular reasoning steps
        # We start with basic buckets, but we can also just append the granular string steps
        # The frontend now accepts strings in processing_steps.
        final_steps = processing_steps.copy()
        if analysis_response.reasoning_steps:
             for step in analysis_response.reasoning_steps:
                 if isinstance(step, str):
                     final_steps.append({
                         "status": "reasoning",
                         "message": step,
                         "data": None
                     })
                 else:
                     # Already a dict (unlikely based on error, but safe)
                     final_steps.append(step)
        
        # Add assistant message
        assistant_message = conversation_service.add_message(
            db=db,
            conversation_id=conversation_id,
            role='assistant',
            content=analysis_response.insights.direct_answer, # Use direct answer as main content
            query_data=query_data,
            processing_steps=final_steps
        )
        
        return MessageResponse.from_orm(assistant_message)
        
    except Exception as e:
        # Error handling
        error_steps = processing_steps + [{
            "status": "error",
            "message": f"Error: {str(e)}",
            "data": None
        }]
        
        error_message = conversation_service.add_message(
            db=db,
            conversation_id=conversation_id,
            role='assistant',
            content=f"I encountered an error processing your query: {str(e)}",
            query_data={"error": str(e)},
            processing_steps=error_steps
        )
        
        return MessageResponse.from_orm(error_message)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    success = conversation_service.delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return None
