import pandas as pd
import duckdb
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from ..config import settings


class DataService:
    """Service for data processing and analysis"""
    
    @staticmethod
    def parse_file(file_path: str, file_type: str) -> pd.DataFrame:
        """Parse uploaded file into DataFrame"""
        try:
            if file_type == "csv":
                df = pd.read_csv(file_path)
            elif file_type in ["xlsx", "xls"]:
                df = pd.read_excel(file_path)
            elif file_type == "sas7bdat":
                df = pd.read_sas(file_path)
            elif file_type == "parquet":
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            return df
        except Exception as e:
            raise Exception(f"Error parsing file: {str(e)}")
    
    @staticmethod
    def get_schema(df: pd.DataFrame) -> Dict[str, str]:
        """Extract schema from DataFrame"""
        schema = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            
            # Simplify dtype names
            if dtype.startswith('int'):
                schema[col] = 'INTEGER'
            elif dtype.startswith('float'):
                schema[col] = 'FLOAT'
            elif dtype == 'bool':
                schema[col] = 'BOOLEAN'
            elif dtype == 'datetime64[ns]':
                schema[col] = 'DATETIME'
            else:
                schema[col] = 'VARCHAR'
        
        return schema
    
    @staticmethod
    def get_sample_data(df: pd.DataFrame, n: int = 5) -> List[Dict]:
        """Get sample rows from DataFrame"""
        sample = df.head(n)
        return json.loads(sample.to_json(orient='records'))
    
    @staticmethod
    def execute_sql_query(
        sql_query: str, 
        df: Optional[pd.DataFrame] = None, 
        connection: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Execute SQL query on DataFrame (DuckDB) or remote Connection (SQLAlchemy)"""
        try:
            if connection:
                # Use ConnectionService for remote execution
                from .connection_service import connection_service
                return connection_service.execute_query(connection, sql_query)
            
            if df is not None:
                # Use DuckDB for local DataFrame queries
                con = duckdb.connect(database=':memory:')
                # Explicitly register the dataframe as a table named 'data'
                con.register('data', df)
                
                result = con.execute(sql_query).df()
                con.close()
                return {
                    "success": True,
                    "data": result.to_dict('records'),
                    "columns": list(result.columns),
                    "error": None
                }
            
            return {"success": False, "data": None, "columns": None, "error": "No data source (DF or connection) provided"}
            
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "row_count": 0,
                "columns": [],
                "error": str(e)
            }
    
    @staticmethod
    def validate_sql(sql_query: str) -> Dict[str, Any]:
        """Validate SQL query for safety"""
        # Forbidden keywords that could be dangerous
        forbidden_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 
            'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE'
        ]
        
        sql_upper = sql_query.upper()
        
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return {
                    "valid": False,
                    "error": f"Forbidden keyword detected: {keyword}"
                }
        
        return {
            "valid": True,
            "error": None
        }
    
    @staticmethod
    def detect_chart_type(result_data: List[Dict], columns: List[str]) -> str:
        """Detect appropriate chart type based on result data"""
        if not result_data or not columns:
            return "table"
        
        num_columns = len(columns)
        num_rows = len(result_data)
        
        # Analyze column types
        first_row = result_data[0]
        numeric_cols = []
        text_cols = []
        
        for col in columns:
            value = first_row.get(col)
            if isinstance(value, (int, float)):
                numeric_cols.append(col)
            else:
                text_cols.append(col)
        
        # Chart type logic - prioritize bar charts for grouped data
        if num_columns == 2 and len(text_cols) == 1 and len(numeric_cols) == 1:
            # One category, one value - perfect for bar chart
            return "bar"
        elif num_columns >= 2 and len(text_cols) >= 1 and len(numeric_cols) >= 1:
            # Multiple columns with categories and numbers - bar chart
            return "bar"
        elif num_rows <= 10 and len(numeric_cols) == 1 and len(text_cols) == 1:
            # Small dataset with categories - could be pie chart
            return "pie"
        elif num_columns == 2 and len(numeric_cols) == 2:
            # Two numeric columns - scatter plot
            return "scatter"
        elif len(numeric_cols) >= 2:
            # Multiple numeric columns - line chart
            return "line"
        else:
            return "table"
    
    @staticmethod
    def prepare_visualization_config(
        result_data: List[Dict],
        columns: List[str],
        chart_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepare visualization configuration"""
        
        if not chart_type:
            chart_type = DataService.detect_chart_type(result_data, columns)
        
        config = {
            "type": chart_type,
            "data": result_data,
            "columns": columns
        }
        
        # Add chart-specific configuration
        if chart_type in ["bar", "line", "pie"]:
            # Assume first column is x-axis/category, rest are values
            if len(columns) >= 2:
                config["xAxis"] = columns[0]
                config["yAxis"] = columns[1:]
        elif chart_type == "scatter":
            if len(columns) >= 2:
                config["xAxis"] = columns[0]
                config["yAxis"] = columns[1]
        
        return config


# Singleton instance
data_service = DataService()
