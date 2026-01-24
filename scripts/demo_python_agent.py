
import sys
import os
import pandas as pd
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

# Configure logging
logging.basicConfig(level=logging.INFO)

from app.agents.python_analyst_agent import python_analyst_agent


def main():
    # Mocking the LLM service to verify logic even if Ollama is down
    print("⚠️  Mocking LLM Service for Verification ⚠️")
    
    original_generate = python_analyst_agent.service.generate_response
    

    def mock_generate_response(*args, **kwargs):
        prompt = kwargs.get("prompt", "")
        if "Create a bar chart" in prompt:
             return '{"code": "import plotly.express as px\\nfig = px.bar(df.groupby(\'category\')[\'value\'].sum().reset_index(), x=\'category\', y=\'value\')", "explanation": "Created bar chart."}'
        elif "total value by category" in prompt:
            return '{"code": "result = df.groupby(\'category\')[\'value\'].sum().reset_index()\\nprint(result.to_markdown())", "explanation": "Grouped by category and summed value."}'
        return "{}"


    python_analyst_agent.service.generate_response = mock_generate_response

    try:
        # Create sample data
        df = pd.DataFrame({
            'category': ['A', 'B', 'C', 'A', 'B', 'C'],
            'value': [10, 20, 30, 15, 25, 35],
            'date': pd.to_datetime(['2023-01-01', '2023-01-01', '2023-01-01', '2023-01-02', '2023-01-02', '2023-01-02'])
        })
        
        print("DataFrame:")
        print(df)
        print("-" * 50)
        
        # Test Question 1: Simple Aggregation
        question1 = "What is the total value by category?"
        print(f"\nQuestion: {question1}")
        result1 = python_analyst_agent.analyze(question1, df)
        print(f"Success: {result1['success']}")
        if result1['success']:
            print("Output:\n", result1['output'])
            print("Code:", result1['code'])
        else:
            print("Error:", result1['error'])

        print("-" * 50)

        # Test Question 2: Plotting
        question2 = "Create a bar chart of total value by category."
        print(f"\nQuestion: {question2}")
        result2 = python_analyst_agent.analyze(question2, df)
        print(f"Success: {result2['success']}")
        if result2['success']:
            print("Output available:", bool(result2.get('output')))
            if result2.get('figure_json'):
                print("Figure JSON generated (truncated):", len(result2['figure_json']), "chars")
            else:
                print("No figure generated")
        else:
            print("Error:", result2['error'])
            
    finally:
        python_analyst_agent.service.generate_response = original_generate


if __name__ == "__main__":
    main()
