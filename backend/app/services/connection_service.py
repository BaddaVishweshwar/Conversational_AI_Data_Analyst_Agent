import pandas as pd
from sqlalchemy import create_engine, text, inspect
from typing import Dict, Any, List, Optional
import snowflake.connector
from ..models import DataConnection

class ConnectionService:
    """Service to handle multiple database connections"""

    def get_connection_url(self, conn: DataConnection) -> str:
        """Generate SQLAlchemy connection URL"""
        if conn.type == "postgres":
            return f"postgresql://{conn.username}:{conn.password}@{conn.host}:{conn.port or 5432}/{conn.database}"
        elif conn.type == "mysql":
            return f"mysql+pymysql://{conn.username}:{conn.password}@{conn.host}:{conn.port or 3306}/{conn.database}"
        elif conn.type == "sqlite":
            # For SQLite, 'database' field stores the file path
            return f"sqlite:///{conn.database}"
        return ""

    def test_connection(self, conn: DataConnection) -> Dict[str, Any]:
        """Test database connectivity"""
        try:
            if conn.type == "snowflake":
                ctx = snowflake.connector.connect(
                    user=conn.username,
                    password=conn.password,
                    account=conn.host, # Snowflake account
                    warehouse=conn.additional_params.get("warehouse"),
                    database=conn.database,
                    schema=conn.additional_params.get("schema")
                )
                ctx.close()
                return {"success": True, "error": None}
            
            url = self.get_connection_url(conn)
            engine = create_engine(url)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"success": True, "error": None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_query(self, conn: DataConnection, sql: str) -> pd.DataFrame:
        """Execute query on remote database and return DataFrame"""
        if conn.type == "snowflake":
            ctx = snowflake.connector.connect(
                user=conn.username,
                password=conn.password,
                account=conn.host,
                warehouse=conn.additional_params.get("warehouse"),
                database=conn.database,
                schema=conn.additional_params.get("schema")
            )
            df = pd.read_sql(sql, ctx)
            ctx.close()
            return df

        url = self.get_connection_url(conn)
        engine = create_engine(url)
        return pd.read_sql(sql, engine)

    def get_tables(self, conn: DataConnection) -> List[str]:
        """List all tables in the database"""
        try:
            if conn.type == "snowflake":
                # Snowflake implementation
                schema = conn.additional_params.get("schema", "PUBLIC")
                sql = f"SHOW TABLES IN SCHEMA {conn.database}.{schema}"
                df = self.execute_query(conn, sql)
                # Snowflake column names are upper case usually
                cols = [c.lower() for c in df.columns]
                if 'name' in cols:
                    return df.iloc[:, cols.index('name')].tolist()
                return []

            url = self.get_connection_url(conn)
            engine = create_engine(url)
            inspector = inspect(engine)
            return inspector.get_table_names()
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []

    def get_sample_data(self, conn: DataConnection, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample rows from a table"""
        # Basic SQL injection prevention for table name (very simple)
        if not table_name.isidentifier():
             # Fallback for complex names or just quote it
             table_name = f'"{table_name}"'
        
        sql = f"SELECT * FROM {table_name} LIMIT {limit}"
        df = self.execute_query(conn, sql)
        # Convert NaNs to None for JSON compatibility
        return df.where(pd.notnull(df), None).to_dict('records')

    def get_table_schema(self, conn: DataConnection, table_name: str) -> Dict[str, Any]:
        """Fetch schema for a specific table in the remote DB"""
        # We try to get schema via introspection first as it's lighter than querying data
        # But data_service.get_schema works on DF, which is fine for now.
        # Let's stick to the plan: query 0 rows.
        
        # Basic SQL injection prevention
        clean_table = table_name if table_name.isidentifier() else f'"{table_name}"'
        
        df = self.execute_query(conn, f"SELECT * FROM {clean_table} LIMIT 0")
        from .data_service import data_service
        return data_service.get_schema(df)

connection_service = ConnectionService()
