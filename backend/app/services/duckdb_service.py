"""
DuckDB Service - In-Memory SQL Execution for Uploaded Files

This service provides fast, in-memory SQL execution on uploaded datasets using DuckDB.
DuckDB is specifically designed for analytical queries and is much faster than SQLite
for data analysis workloads.

Key Features:
- Load CSV, Parquet, Excel files directly into DuckDB
- Execute SQL queries with full ANSI SQL support
- Support for complex queries (CTEs, window functions, subqueries)
- Automatic type inference and optimization
- Memory-efficient processing of large datasets
"""

import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from ..config import settings

logger = logging.getLogger(__name__)


class DuckDBService:
    """Service for managing DuckDB connections and query execution"""
    
    def __init__(self):
        """Initialize DuckDB service with configuration"""
        self.connections: Dict[int, duckdb.DuckDBPyConnection] = {}
        self.memory_limit = settings.DUCKDB_MEMORY_LIMIT
        self.threads = settings.DUCKDB_THREADS
        
    def get_connection(self, dataset_id: int) -> duckdb.DuckDBPyConnection:
        """
        Get or create a DuckDB connection for a specific dataset.
        Each dataset gets its own in-memory database for isolation.
        
        Args:
            dataset_id: Unique identifier for the dataset
            
        Returns:
            DuckDB connection object
        """
        if dataset_id not in self.connections:
            # Create new in-memory connection
            conn = duckdb.connect(database=':memory:')
            
            # Configure connection
            conn.execute(f"SET memory_limit='{self.memory_limit}'")
            conn.execute(f"SET threads={self.threads}")
            conn.execute("SET enable_progress_bar=false")
            
            self.connections[dataset_id] = conn
            logger.info(f"Created DuckDB connection for dataset {dataset_id}")
            
        return self.connections[dataset_id]
    
    def load_file(
        self, 
        dataset_id: int, 
        file_path: str, 
        table_name: str = "data"
    ) -> Dict[str, Any]:
        """
        Load a file into DuckDB.
        
        Supports:
        - CSV files (.csv)
        - Parquet files (.parquet)
        - Excel files (.xlsx, .xls)
        
        Args:
            dataset_id: Dataset identifier
            file_path: Path to the file
            table_name: Name to give the table in DuckDB
            
        Returns:
            Dictionary with schema information
        """
        conn = self.get_connection(dataset_id)
        file_path_obj = Path(file_path)
        
        try:
            # Determine file type and load accordingly
            if file_path_obj.suffix.lower() == '.csv':
                # DuckDB can read CSV directly with auto-detection
                conn.execute(f"DROP TABLE IF EXISTS {table_name}")  # Drop if exists
                conn.execute(f"""
                    CREATE TABLE {table_name} AS 
                    SELECT * FROM read_csv_auto('{file_path}', 
                        header=true, 
                        auto_detect=true,
                        ignore_errors=true
                    )
                """)
                
            elif file_path_obj.suffix.lower() == '.parquet':
                # DuckDB has native Parquet support
                conn.execute(f"""
                    CREATE TABLE {table_name} AS 
                    SELECT * FROM read_parquet('{file_path}')
                """)
                
            elif file_path_obj.suffix.lower() in ['.xlsx', '.xls']:
                # For Excel, we need to use pandas first
                df = pd.read_excel(file_path)
                conn.register(table_name, df)
                # Make it persistent in the connection
                conn.execute(f"CREATE TABLE {table_name}_temp AS SELECT * FROM {table_name}")
                conn.execute(f"DROP VIEW {table_name}")
                conn.execute(f"ALTER TABLE {table_name}_temp RENAME TO {table_name}")
                
            else:
                raise ValueError(f"Unsupported file type: {file_path_obj.suffix}")
            
            # Get schema information
            schema_info = self.get_schema(dataset_id, table_name)
            
            # Get row count
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            logger.info(f"Loaded {file_path} into DuckDB table '{table_name}' ({row_count} rows)")
            
            return {
                "table_name": table_name,
                "row_count": row_count,
                "schema": schema_info,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error loading file into DuckDB: {str(e)}")
            raise
    
    def get_schema(self, dataset_id: int, table_name: str = "data") -> List[Dict[str, str]]:
        """
        Get schema information for a table.
        
        Args:
            dataset_id: Dataset identifier
            table_name: Name of the table
            
        Returns:
            List of column definitions with name and type
        """
        conn = self.get_connection(dataset_id)
        
        result = conn.execute(f"DESCRIBE {table_name}").fetchall()
        
        schema = []
        for row in result:
            schema.append({
                "column_name": row[0],
                "data_type": row[1],
                "is_nullable": row[2] == "YES" if len(row) > 2 else True
            })
        
        return schema
    
    def execute_query(
        self, 
        dataset_id: int, 
        sql: str,
        limit: Optional[int] = 1000
    ) -> Dict[str, Any]:
        """
        Execute a SQL query and return results.
        
        Args:
            dataset_id: Dataset identifier
            sql: SQL query to execute
            limit: Maximum number of rows to return (default 1000)
            
        Returns:
            Dictionary with results and metadata
        """
        conn = self.get_connection(dataset_id)
        
        try:
            # Add LIMIT if not present and limit is specified
            if limit and "LIMIT" not in sql.upper():
                sql = f"{sql.rstrip(';')} LIMIT {limit}"
            
            # Execute query
            result = conn.execute(sql)
            
            # Fetch results
            rows = result.fetchall()
            columns = [desc[0] for desc in result.description]
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "sql": sql
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "sql": sql
            }
    
    def execute_query_to_df(
        self, 
        dataset_id: int, 
        sql: str
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return results as pandas DataFrame.
        
        Args:
            dataset_id: Dataset identifier
            sql: SQL query to execute
            
        Returns:
            Pandas DataFrame with results
        """
        conn = self.get_connection(dataset_id)
        return conn.execute(sql).df()
    
    def get_sample_data(
        self, 
        dataset_id: int, 
        table_name: str = "data",
        n: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get sample rows from a table.
        
        Args:
            dataset_id: Dataset identifier
            table_name: Name of the table
            n: Number of rows to sample
            
        Returns:
            List of sample rows as dictionaries
        """
        result = self.execute_query(
            dataset_id,
            f"SELECT * FROM {table_name} USING SAMPLE {n}",
            limit=n
        )
        return result.get("data", [])
    
    def get_column_stats(
        self, 
        dataset_id: int, 
        table_name: str = "data"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get statistical information for all columns.
        
        Args:
            dataset_id: Dataset identifier
            table_name: Name of the table
            
        Returns:
            Dictionary mapping column names to their statistics
        """
        conn = self.get_connection(dataset_id)
        schema = self.get_schema(dataset_id, table_name)
        
        stats = {}
        
        for col in schema:
            col_name = col["column_name"]
            col_type = col["data_type"]
            
            # Basic stats for all columns
            null_count = conn.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE \"{col_name}\" IS NULL"
            ).fetchone()[0]
            
            unique_count = conn.execute(
                f"SELECT COUNT(DISTINCT \"{col_name}\") FROM {table_name}"
            ).fetchone()[0]
            
            total_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            stats[col_name] = {
                "data_type": col_type,
                "null_count": null_count,
                "null_percentage": round((null_count / total_count) * 100, 2) if total_count > 0 else 0,
                "unique_count": unique_count,
                "unique_percentage": round((unique_count / total_count) * 100, 2) if total_count > 0 else 0
            }
            
            # Numeric column stats
            if any(t in col_type.upper() for t in ["INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC"]):
                numeric_stats = conn.execute(f"""
                    SELECT 
                        MIN(\"{col_name}\") as min_val,
                        MAX(\"{col_name}\") as max_val,
                        AVG(\"{col_name}\") as mean_val,
                        MEDIAN(\"{col_name}\") as median_val,
                        STDDEV(\"{col_name}\") as std_dev
                    FROM {table_name}
                    WHERE \"{col_name}\" IS NOT NULL
                """).fetchone()
                
                if numeric_stats:
                    stats[col_name].update({
                        "min": numeric_stats[0],
                        "max": numeric_stats[1],
                        "mean": numeric_stats[2],
                        "median": numeric_stats[3],
                        "std_dev": numeric_stats[4]
                    })
            
            # Categorical column stats (top values)
            if unique_count <= 50:  # Only for low cardinality columns
                top_values = conn.execute(f"""
                    SELECT \"{col_name}\", COUNT(*) as count
                    FROM {table_name}
                    WHERE \"{col_name}\" IS NOT NULL
                    GROUP BY \"{col_name}\"
                    ORDER BY count DESC
                    LIMIT 10
                """).fetchall()
                
                stats[col_name]["top_values"] = [
                    {"value": str(row[0]), "count": row[1]} 
                    for row in top_values
                ]
        
        return stats
    
    def close_connection(self, dataset_id: int):
        """
        Close and remove a DuckDB connection.
        
        Args:
            dataset_id: Dataset identifier
        """
        if dataset_id in self.connections:
            self.connections[dataset_id].close()
            del self.connections[dataset_id]
            logger.info(f"Closed DuckDB connection for dataset {dataset_id}")
    
    def close_all_connections(self):
        """Close all DuckDB connections"""
        for dataset_id in list(self.connections.keys()):
            self.close_connection(dataset_id)


# Global instance
duckdb_service = DuckDBService()
