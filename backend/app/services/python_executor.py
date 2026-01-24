
import sys
import io
import contextlib
import logging
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PythonExecutorService:
    """
    Executes Python code dynamically in a controlled environment.
    Designed for use with LLM-generated analysis scripts.
    """

    def execute_code(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute Python code with a DataFrame in context.
        
        Args:
            code: Python script string
            df: Pandas DataFrame to analyze
            
        Returns:
            Dict containing:
            - output: stdout text
            - figure: Plotly figure object (if generated)
            - error: Error message (if any)
            - success: Boolean status
        """
        # Create a buffer to capture stdout
        output_buffer = io.StringIO()
        
        # Prepare local context with df
        local_scope = {"df": df, "pd": pd, "go": go}
        # Pre-import plotly express as px if likely used, though script should import it
        try:
            import plotly.express as px
            local_scope["px"] = px
        except ImportError:
            pass

        try:
            # Execute code while capturing stdout
            with contextlib.redirect_stdout(output_buffer):
                exec(code, {}, local_scope)
            
            output = output_buffer.getvalue()
            
            # Check if a figure was created
            fig = local_scope.get("fig")
            figure_json = None
            if fig and hasattr(fig, "to_json"):
                figure_json = fig.to_json()
                
            return {
                "success": True,
                "output": output,
                "figure_json": figure_json,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error executing Python code: {e}")
            return {
                "success": False,
                "output": output_buffer.getvalue(),
                "figure_json": None,
                "error": str(e)
            }

python_executor = PythonExecutorService()
