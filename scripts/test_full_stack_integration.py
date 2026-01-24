
import sys
import os
import asyncio
import pandas as pd
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

# Mock dependencies before importing service
sys.modules['app.services.rag_service'] = MagicMock()
sys.modules['app.services.rag_service'].rag_service = MagicMock()
sys.modules['app.services.rag_service'].rag_service.build_complete_context = AsyncMock(return_value={
    'schema': {'relevant_columns': []},
    'similar_queries': []
})

# Mock Validation & Intent (Critical to bypass Ollama)
sys.modules['app.services.question_validator'] = MagicMock()
sys.modules['app.services.question_validator'].question_validator = MagicMock()
sys.modules['app.services.question_validator'].question_validator.validate_question = AsyncMock(return_value={
    'is_valid': True, 'is_answerable': True
})

sys.modules['app.agents.intent_classifier_agent'] = MagicMock()
# Mock the Intent Enum and Result
mock_intent_enum = MagicMock()
mock_intent_enum.CORRELATION.value = 'CORRELATION'
mock_result = MagicMock()
mock_result.intent = 'CORRELATION' # Pass string directly or mock enum if check uses is
mock_result.confidence = 0.95
sys.modules['app.agents.intent_classifier_agent'].intent_classifier = MagicMock()
sys.modules['app.agents.intent_classifier_agent'].intent_classifier.classify = MagicMock(return_value=mock_result)

sys.modules['app.agents.query_understanding_agent'] = MagicMock()
sys.modules['app.agents.query_understanding_agent'].query_understanding_agent = MagicMock()
sys.modules['app.agents.query_understanding_agent'].query_understanding_agent.analyze_query = AsyncMock(return_value={
    'answerable': True, 'intent': 'CORRELATION', 'analysis': 'Mock analysis'
})

# Mock Database Session
mock_db = MagicMock()

async def test_integration():
    print("🚀 Starting Integration Test")
    
    # Import service after mocking
    from app.services.analytics_service_v4 import analytics_service_v4
    from app.services.duckdb_service import duckdb_service
    from app.agents.python_analyst_agent import python_analyst_agent
    
    # 1. Setup Data
    dataset_id = 999
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 30, 40, 50],
        'category': ['A', 'A', 'B', 'B', 'C']
    })
    
    # Register data in DuckDB
    conn = duckdb_service.get_connection(dataset_id)
    conn.register('data', df)
    
    # 2. Mock Agent to avoid LLM calls
    original_analyze = python_analyst_agent.analyze
    python_analyst_agent.analyze = MagicMock(return_value={
        "success": True,
        "code": "print('Mocked Code')",
        "explanation": "Calculated correlation.",
        "output": "Correlation is 1.0",
        "figure_json": '{"data": [], "layout": {}}' # Mock Plotly JSON
    })
    
    try:
        # 3. Test Routing (Asking for Correlation)
        question = "Calculate the correlation between x and y"
        print(f"\nTesting Question: '{question}'")
        
        result = await analytics_service_v4.analyze_query(question, dataset_id, mock_db)
        
        # 4. Assertions
        print(f"Success: {result['success']}")
        print(f"Metadata Agent: {result.get('metadata', {}).get('agent')}")
        
        # Verify Routing
        if result.get('metadata', {}).get('agent') == 'python_analyst':
            print("✅ Correctly routed to Python Analyst Agent")
        else:
            print("❌ Failed to route to Python Agent")
            
        # Verify Visualization format
        viz = result.get('visualization')
        if viz and len(viz) > 0 and viz[0]['chart_type'] == 'plotly_json':
             print("✅ Visualization format is correct (plotly_json)")
        else:
             print(f"❌ Visualization format incorrect: {viz}")
             
    finally:
        python_analyst_agent.analyze = original_analyze
        duckdb_service.close_connection(dataset_id)

if __name__ == "__main__":
    asyncio.run(test_integration())
