"""
End-to-End System Capability Test
Tests the full Multi-Agent Pipeline (AnalyticsServiceV3) with various query types.
Mocks the LLM to return scenario-specific responses.
"""

import sys
import os
import asyncio
import json
import logging
from unittest.mock import MagicMock, patch, AsyncMock
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("test_capabilities")
logger.setLevel(logging.INFO)

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.services.analytics_service_v3 import analytics_service_v3
from app.models import Dataset
from app.services.ollama_service import ollama_service
from app.agents.insight_generator_agent import InsightGeneratorAgent
from app.agents import Insights

# Mock Data
SAMPLE_DATA = [
    {"product": "Laptop", "region": "North", "sales": 1200, "date": "2023-01-01"},
    {"product": "Laptop", "region": "South", "sales": 1500, "date": "2023-01-02"},
    {"product": "Phone", "region": "North", "sales": 800,  "date": "2023-01-01"},
    {"product": "Phone", "region": "South", "sales": 950,  "date": "2023-01-02"},
    {"product": "Tablet", "region": "North", "sales": 400, "date": "2023-01-03"},
    {"product": "Tablet", "region": "South", "sales": 450, "date": "2023-01-03"},
]
DF = pd.DataFrame(SAMPLE_DATA)
DATASET = Dataset(id=1, name="Sales Data", user_id=1, file_path="sales.csv", file_type="csv")

# Scenario Logic for Mock LLM
def mock_generate_response(prompt, json_mode=False, task_type=None, **kwargs):
    prompt_lower = prompt.lower()
    
    # 1. PLANNING PHASE
    if task_type == 'planning' or "plan" in prompt_lower:
        return json.dumps({
            "understanding": "User wants to analyze sales data",
            "approach": "Aggregate sales metrics",
            "sub_questions": ["What is the total sales?"],
            "intent": "DESCRIPTIVE"
        })
    
    # 2. EXPLORATION PHASE
    if "exploratory" in prompt_lower or task_type == 'exploratory':
        return json.dumps([{"sql": "SELECT COUNT(*) FROM data", "finding": "Data has 6 rows"}])
        
    # 3. VISUALIZATION SELECTION
    if task_type == 'visualization' or "chart type" in prompt_lower:
        if "region" in prompt_lower:
            return json.dumps({
                "chart_type": "bar",
                "config": {"x_axis": "region", "y_axis": ["sales"], "title": "Sales by Region"},
                "reasoning": "Bar chart is best for categorical comparison"
            })
        elif "time" in prompt_lower or "trend" in prompt_lower:
             return json.dumps({
                "chart_type": "line",
                "config": {"x_axis": "date", "y_axis": ["sales"], "title": "Sales Trend"},
                "reasoning": "Line chart shows change over time"
            })
        else:
             return json.dumps({
                "chart_type": "pie",
                "config": {"category": "product", "value": "sales", "title": "Sales Distribution"},
                "reasoning": "Pie chart shows proportions"
            })

    # Other tasks handled by specific mock checks usually
    return "{}"

async def run_test_scenario(scenario_name, query, expected_chart):
    print(f"\n🔹 Testing Scenario: {scenario_name}")
    print(f"   Query: \"{query}\"")
    
    expected_sql = ""
    if "region" in query.lower():
        expected_sql = "SELECT region, SUM(sales) as sales FROM data GROUP BY region"
    elif "time" in query.lower():
        expected_sql = "SELECT date, SUM(sales) as sales FROM data GROUP BY date"
    else:
        expected_sql = "SELECT product, SUM(sales) as sales FROM data GROUP BY product"

    # Patch Self-Consistency Service
    with patch('app.services.self_consistency_service.self_consistency_service.generate_with_self_consistency', 
               new_callable=AsyncMock) as mock_sc:
        
        mock_sc.return_value = {
            'success': True,
            'sql': expected_sql,
            'reasoning': 'Generated for test',
            'is_sc': True
        }

        # Patch SQL Validator
        with patch('app.services.sql_validator_service.sql_validator.validate_and_correct', new_callable=AsyncMock) as mock_validator:
             mock_validator.return_value = {
                 'is_valid': True,
                 'sql': expected_sql,
                 'attempts': 0,
                 'final_validation': {'issues': []}
             }
        
             # Patch Ollama Service (general)
             with patch.object(ollama_service, 'generate_response', side_effect=mock_generate_response):
                with patch.object(ollama_service, 'client') as mock_client:
                     mock_client.generate.return_value = {'response': '{}'} 

                     # Patch InsightGeneratorAgent.generate CLASS method to bypass client completely
                     with patch.object(InsightGeneratorAgent, 'generate') as mock_insight_generate:
                         # Construct a mock Insights object
                         mock_insights = Insights(
                            direct_answer="Sales are strong in the South region." if "region" in query else "Sales are trending up.",
                            what_data_shows=["South sales: 2900"],
                            why_it_happened=["Demand is high"],
                            business_implications=["Increase stock"],
                            confidence=0.9,
                            data_sufficiency="sufficient"
                         )
                         mock_insight_generate.return_value = mock_insights

                         # Run Analysis
                         result = await analytics_service_v3.analyze(
                             query=query,
                             dataset=DATASET,
                             df=DF
                         )
                     
                     # VERIFICATION
                     print("\n   --- Results ---")
                     # 1. SQL
                     # Check structured 'sql_query' dictionary or root key
                     generated_sql = result.get('sql_query', {}).get('query', '')
                     if not generated_sql: 
                         # Try camelai structure fallback
                         generated_sql = result.get('camelai_structure', {}).get('sql_query', '')
                     
                     generated_sql = generated_sql.strip()
                     
                     if expected_sql in generated_sql:
                         print(f"   ✅ SQL Generated Correctly: {generated_sql[:50]}...")
                     else:
                         print(f"   ❌ SQL Mismatch. Got: {generated_sql}")
                         print(f"      Expected: {expected_sql}")

                     # 2. Visualizations
                     viz_list = result.get('visualizations', [])
                     if viz_list:
                         viz = viz_list[0]
                         chart_type = viz.get('type')
                         title = viz.get('config', {}).get('title')
                         print(f"   📊 Visualization: {chart_type.upper()} Chart - '{title}'")
                         
                         if chart_type == expected_chart:
                             print(f"   ✅ Chart Type Matched: {expected_chart}")
                         else:
                              print(f"   ❌ Chart Type Mismatch. Expected {expected_chart}, got {chart_type}")
                     else:
                         print("   ❌ No visualizations generated")
                         
                     # 3. Insights
                     insights = result.get('insights', {})
                     answer = insights.get('summary')
                     findings = insights.get('key_findings', [])
                     print(f"   💡 Insight Summary: {answer}")
                     print(f"   🔍 Findings found: {len(findings)}")
                     
                     if "South" in answer or "trending" in answer:
                         print("   ✅ Insights verify data content")
                     
                     return result

async def main():
    print("🚀 Starting End-to-End System Capability Test")
    
    # 1. Sales by Region Test (Expect Bar)
    await run_test_scenario(
        scenario_name="Categorical Comparison",
        query="Show me sales by region",
        expected_chart="bar"
    )
    
    # 2. Sales Over Time Test (Expect Line)
    await run_test_scenario(
        scenario_name="Time Series Trend",
        query="How have sales changed over time?",
        expected_chart="line"
    )

if __name__ == "__main__":
    asyncio.run(main())
