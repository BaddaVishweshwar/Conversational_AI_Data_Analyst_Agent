
import pytest
import pandas as pd
import json
from app.services.python_executor import PythonExecutorService

@pytest.fixture
def executor():
    return PythonExecutorService()

@pytest.fixture
def sample_df():
    data = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
    return pd.DataFrame(data)

def test_execute_simple_print(executor, sample_df):
    code = "print(df['col1'].sum())"
    result = executor.execute_code(code, sample_df)
    
    assert result["success"] is True
    assert result["error"] is None
    assert "6" in result["output"]

def test_execute_create_figure(executor, sample_df):
    # Minimal code to create a figure
    code = """
import plotly.express as px
fig = px.bar(df, x='col1', y='col2')
"""
    result = executor.execute_code(code, sample_df)
    
    assert result["success"] is True
    assert result["figure_json"] is not None
    # Verify it's valid json
    fig_dict = json.loads(result["figure_json"])
    assert "data" in fig_dict

def test_execute_error(executor, sample_df):
    code = "print(undefined_variable)"
    result = executor.execute_code(code, sample_df)
    
    assert result["success"] is False
    assert result["error"] is not None
    assert "name 'undefined_variable' is not defined" in str(result["error"])
