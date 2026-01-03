"""
New V4 endpoint for queries.py - Add this to the file
"""

@router.post("/ask-v4", response_model=QueryResponse, status_code=status.HTTP_201_CREATED)
async def ask_question_v4(
    query_request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask a natural language question using Professional V4 Pipeline with OpenRouter.
    
    Features:
    - Claude 3.5 Sonnet for SQL generation and insights
    - RAG-powered semantic search with embeddings
    - 6-step multi-agent pipeline
    - Self-correcting SQL execution
    - Executive-level business insights
    """
    
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
        logger.info(f"Processing V4 query: {query_request.query}")
        
        # Execute V4 multi-agent analytics pipeline
        analysis_response = await analytics_service_v4.analyze_query(
            user_question=query_request.query,
            dataset_id=dataset.id,
            db=db
        )
        
        # Check if analysis succeeded
        if not analysis_response.get('success', False):
            query.status = "error"
            query.error_message = analysis_response.get('error', 'Analysis failed')
            db.commit()
            db.refresh(query)
            return query
        
        # Extract results from V4 response
        sql_query = analysis_response.get('sql', '')
        result_data = analysis_response.get('data', [])
        row_count = analysis_response.get('row_count', 0)
        insights = analysis_response.get('insights', '')
        visualization = analysis_response.get('visualization', {})
        metadata = analysis_response.get('metadata', {})
        
        # Prepare visualization config for frontend
        viz_config = {
            "type": visualization.get('chart_type', 'table'),
            "reason": visualization.get('reason', ''),
            "data": result_data,
            "columns": list(result_data[0].keys()) if result_data else []
        }
        
        # Update query with results
        execution_time = analysis_response.get('execution_time', int((time.time() - start_time) * 1000))
        query.generated_sql = sql_query
        query.result_data = result_data
        query.visualization_config = viz_config
        query.insights = insights
        query.execution_time = execution_time
        query.status = "success"
        query.intent = analysis_response.get('intent', 'DESCRIPTIVE')
        
        # Store V4 metadata
        query.analysis_plan = {
            "interpretation": analysis_response.get('interpretation', ''),
            "sql_attempts": metadata.get('sql_attempts', 1),
            "columns_retrieved": metadata.get('rag_context_summary', {}).get('columns_retrieved', 0),
            "similar_queries_found": metadata.get('rag_context_summary', {}).get('similar_queries_found', 0),
            "reasoning": metadata.get('reasoning', '')
        }
        
        db.commit()
        db.refresh(query)
        
        # Save to knowledge base for RAG
        from ..services.rag_service import rag_service
        try:
            await rag_service.store_successful_query(
                dataset_id=dataset.id,
                natural_language=query_request.query,
                sql_query=sql_query,
                intent=analysis_response.get('intent', 'DESCRIPTIVE'),
                db=db
            )
        except Exception as e:
            logger.warning(f"Failed to store query in RAG: {str(e)}")
        
        logger.info(f"V4 query completed successfully in {execution_time}ms")
        return query
        
    except Exception as e:
        logger.error(f"Error in V4 pipeline: {str(e)}", exc_info=True)
        query.status = "error"
        query.error_message = str(e)
        db.commit()
        db.refresh(query)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
