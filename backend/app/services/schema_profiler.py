"""
Schema Profiler Service

Extracts technical metadata and statistics from the database to support
accurate query generation and semantic understanding.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ColumnProfile:
    name: str
    dtype: str
    null_count: int
    null_percentage: float
    unique_count: int
    min_value: Any = None
    max_value: Any = None
    avg_value: float = None
    std_dev: float = None
    sample_values: List[Any] = None

@dataclass
class TableProfile:
    name: str
    row_count: int
    columns: Dict[str, ColumnProfile]
    primary_key: Optional[List[str]] = None

class SchemaProfiler:
    """
    Analyzes database tables to extract rich metadata and statistics.
    """
    
    def profile_table(self, df: pd.DataFrame, table_name: str = "data") -> TableProfile:
        """
        Profile a dataframe (representing a table) to extract comprehensive statistics.
        
        Args:
            df: DataFrame to profile
            table_name: logical name of the table
            
        Returns:
            TableProfile object containing all metadata
        """
        try:
            row_count = len(df)
            columns = {}
            
            for col in df.columns:
                columns[col] = self._profile_column(df[col])
                
            # Heuristic for Primary Key:
            # First column that is unique and has no nulls
            primary_key = None
            for col_name, profile in columns.items():
                if profile.unique_count == row_count and profile.null_count == 0:
                    primary_key = [col_name]
                    break
            
            profile = TableProfile(
                name=table_name,
                row_count=row_count,
                columns=columns,
                primary_key=primary_key
            )
            
            logger.info(f"✅ Profiled table '{table_name}': {row_count} rows, {len(columns)} columns")
            return profile
            
        except Exception as e:
            logger.error(f"Error profiling table {table_name}: {str(e)}")
            # Return empty profile on failure
            return TableProfile(name=table_name, row_count=0, columns={})
    
    def _profile_column(self, series: pd.Series) -> ColumnProfile:
        """Generate profile for a single column."""
        
        # Basic stats
        null_count = int(series.isnull().sum())
        total_count = len(series)
        null_pct = (null_count / total_count * 100) if total_count > 0 else 0
        unique_count = int(series.nunique())
        
        # Get samples (top 5 frequent non-null values)
        try:
            value_counts = series.value_counts().head(5)
            samples = value_counts.index.tolist()
            # If too few unique values, just take unique values
            if unique_count <= 5:
                samples = series.dropna().unique().tolist()
        except Exception:
            samples = []
            
        # Initialize profile
        profile = ColumnProfile(
            name=str(series.name),
            dtype=str(series.dtype),
            null_count=null_count,
            null_percentage=round(null_pct, 2),
            unique_count=unique_count,
            sample_values=samples
        )
        
        # Numeric Stats
        if pd.api.types.is_numeric_dtype(series) and unique_count > 0:
            non_null = series.dropna()
            if not non_null.empty:
                profile.min_value = float(non_null.min())
                profile.max_value = float(non_null.max())
                profile.avg_value = float(non_null.mean())
                if len(non_null) > 1:
                    profile.std_dev = float(non_null.std())

        # Date stats (if applicable) - could add later
        
        return profile

    def to_dict(self, profile: TableProfile) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        return {
            "table_name": profile.name,
            "row_count": profile.row_count,
            "primary_key": profile.primary_key,
            "columns": {
                name: {
                    "type": col.dtype,
                    "min": col.min_value,
                    "max": col.max_value,
                    "avg": col.avg_value,
                    "std_dev": col.std_dev,
                    "missing_percentage": col.null_percentage,
                    "unique_count": col.unique_count,
                    "sample_values": col.sample_values
                } for name, col in profile.columns.items()
            }
        }

# Singleton instance
schema_profiler = SchemaProfiler()
