import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents import IntentType, IntentResult, SchemaAnalysis, ColumnMetadata, ColumnType, ExecutionResult, ChartType
from app.agents.query_resolver_agent import query_resolver
from app.agents.visualization_selector_agent import visualization_selector

def test_query_resolver():
    print("\n--- Testing Query Resolver (LLM Context) ---")
    
    # Mock context: User asked for sales, Assistant showed data
    context = {
        "history": [
            {"role": "user", "content": "Show me total sales by region"},
            {"role": "assistant", "content": "Here represents the total sales by region."}
        ],
        "last_query": "Show me total sales by region"
    }
    
    # Ambiguous follow-up
    current_query = "What about for individual products?"
    
    print(f"Context: {context['last_query']}")
    print(f"Query: {current_query}")
    
    # This calls actual Ollama, ensure it's running
    try:
        result = query_resolver.resolve_query(current_query, context)
        print(f"✅ Resolved: {result['resolved_query']}")
        print(f"   Intent: {result['intent']}")
        print(f"   Is Followup: {result['is_followup']}")
    except Exception as e:
        print(f"❌ Failed: {e}")

def test_visualization_selector():
    print("\n--- Testing Visualization Selector (LLM) ---")
    
    # Mock results
    metrics = {"sales": 1000}
    cols = ["region", "sales"]
    data = [
        {"region": "North", "sales": 500},
        {"region": "South", "sales": 300},
        {"region": "East", "sales": 200}
    ]
    
    execution_result = ExecutionResult(
        success=True,
        data=data,
        columns=cols,
        row_count=3
    )
    
    intent = IntentResult(intent=IntentType.COMPARATIVE, confidence=0.99)
    query = "Compare sales by region"
    
    try:
        viz = visualization_selector.select(intent, execution_result, query)
        print(f"✅ Selected Chart: {viz.chart_type.value}")
        print(f"   Reason: {viz.rejection_reason}") # mapped reason here
        if viz.chart_type == ChartType.BAR:
            print("   SUCCESS: Correctly chose BAR for categorical comparison")
        else:
            print(f"   WARNING: Expected BAR, got {viz.chart_type.value}")
            
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_query_resolver()
    test_visualization_selector()
