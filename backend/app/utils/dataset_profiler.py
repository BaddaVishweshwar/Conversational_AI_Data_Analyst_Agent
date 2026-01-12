"""
Dataset Profiler - Comprehensive Data Analysis and Semantic Understanding

This utility extracts rich metadata from datasets including:
- Statistical profiles (min, max, mean, unique counts, nulls)
- Semantic type detection (email, phone, ID, date patterns)
- Business meaning generation using LLM
- Sample values for context
- Data quality metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatasetProfiler:
    """Comprehensive dataset profiling for semantic understanding"""
    
    def __init__(self, ollama_service=None):
        """
        Initialize profiler with optional LLM service for business meanings.
        
        Args:
            ollama_service: OllamaService instance for generating business meanings
        """
        self.ollama_service = ollama_service
    
    def profile_dataset(self, df: pd.DataFrame, dataset_name: str = "data") -> Dict[str, Any]:
        """
        Generate comprehensive profile of a dataset.
        
        Args:
            df: Pandas DataFrame to profile
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary with rich metadata
        """
        logger.info(f"Profiling dataset: {dataset_name} ({len(df)} rows, {len(df.columns)} columns)")
        
        profile = {
            "dataset_name": dataset_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
            "columns": [],
            "sample_rows": df.head(5).to_dict('records'),
            "data_quality": self._assess_data_quality(df)
        }
        
        # Profile each column
        for col in df.columns:
            column_profile = self._profile_column(df, col)
            profile["columns"].append(column_profile)
        
        return profile
    
    def _profile_column(self, df: pd.DataFrame, column_name: str) -> Dict[str, Any]:
        """
        Profile a single column with comprehensive metadata.
        
        Args:
            df: DataFrame
            column_name: Name of column to profile
            
        Returns:
            Dictionary with column metadata
        """
        col_data = df[column_name]
        
        profile = {
            "column_name": column_name,
            "data_type": str(col_data.dtype),
            "null_count": int(col_data.isnull().sum()),
            "null_percentage": round(col_data.isnull().sum() / len(df) * 100, 2),
            "unique_count": int(col_data.nunique()),
            "unique_percentage": round(col_data.nunique() / len(df) * 100, 2),
        }
        
        # Detect semantic type
        profile["semantic_type"] = self._detect_semantic_type(col_data, column_name)
        
        # Type-specific statistics
        if pd.api.types.is_numeric_dtype(col_data):
            profile.update(self._profile_numeric_column(col_data))
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            profile.update(self._profile_datetime_column(col_data))
        else:
            profile.update(self._profile_text_column(col_data))
        
        # Sample values (non-null)
        sample_values = col_data.dropna().head(10).tolist()
        profile["sample_values"] = [str(v) for v in sample_values]
        
        # Generate business meaning if LLM available
        if self.ollama_service:
            profile["business_meaning"] = self._generate_business_meaning(column_name, profile)
        
        return profile
    
    def _profile_numeric_column(self, col_data: pd.Series) -> Dict[str, Any]:
        """Profile numeric column with statistics."""
        non_null = col_data.dropna()
        
        if len(non_null) == 0:
            return {
                "min_value": None,
                "max_value": None,
                "mean_value": None,
                "median_value": None,
                "std_dev": None
            }
        
        return {
            "min_value": float(non_null.min()),
            "max_value": float(non_null.max()),
            "mean_value": round(float(non_null.mean()), 2),
            "median_value": float(non_null.median()),
            "std_dev": round(float(non_null.std()), 2) if len(non_null) > 1 else 0
        }
    
    def _profile_datetime_column(self, col_data: pd.Series) -> Dict[str, Any]:
        """Profile datetime column."""
        non_null = col_data.dropna()
        
        if len(non_null) == 0:
            return {
                "min_date": None,
                "max_date": None,
                "date_range_days": None
            }
        
        min_date = non_null.min()
        max_date = non_null.max()
        
        return {
            "min_date": str(min_date),
            "max_date": str(max_date),
            "date_range_days": (max_date - min_date).days if pd.notna(min_date) and pd.notna(max_date) else None
        }
    
    def _profile_text_column(self, col_data: pd.Series) -> Dict[str, Any]:
        """Profile text column."""
        non_null = col_data.dropna().astype(str)
        
        if len(non_null) == 0:
            return {
                "avg_length": None,
                "min_length": None,
                "max_length": None
            }
        
        lengths = non_null.str.len()
        
        return {
            "avg_length": round(float(lengths.mean()), 1),
            "min_length": int(lengths.min()),
            "max_length": int(lengths.max())
        }
    
    def _detect_semantic_type(self, col_data: pd.Series, column_name: str) -> str:
        """
        Detect semantic type of column (email, phone, ID, etc.)
        
        Args:
            col_data: Column data
            column_name: Column name
            
        Returns:
            Semantic type string
        """
        # Check column name patterns first
        name_lower = column_name.lower()
        
        if any(x in name_lower for x in ['id', '_id', 'key']):
            return 'identifier'
        if any(x in name_lower for x in ['email', 'e-mail']):
            return 'email'
        if any(x in name_lower for x in ['phone', 'mobile', 'tel']):
            return 'phone'
        if any(x in name_lower for x in ['date', 'time', 'timestamp']):
            return 'datetime'
        if any(x in name_lower for x in ['price', 'cost', 'amount', 'revenue', 'sales']):
            return 'currency'
        if any(x in name_lower for x in ['percent', 'rate', 'ratio']):
            return 'percentage'
        if any(x in name_lower for x in ['url', 'link', 'website']):
            return 'url'
        if any(x in name_lower for x in ['zip', 'postal', 'postcode']):
            return 'postal_code'
        
        # Check data patterns
        sample = col_data.dropna().astype(str).head(100)
        
        if len(sample) == 0:
            return 'unknown'
        
        # Email pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if sample.str.match(email_pattern).mean() > 0.8:
            return 'email'
        
        # Phone pattern
        phone_pattern = r'^[\d\s\-\(\)\+]{10,}$'
        if sample.str.match(phone_pattern).mean() > 0.8:
            return 'phone'
        
        # URL pattern
        url_pattern = r'^https?://'
        if sample.str.match(url_pattern).mean() > 0.8:
            return 'url'
        
        # Check if numeric
        if pd.api.types.is_numeric_dtype(col_data):
            # Check if looks like ID (sequential integers)
            if pd.api.types.is_integer_dtype(col_data):
                unique_ratio = col_data.nunique() / len(col_data)
                if unique_ratio > 0.95:
                    return 'identifier'
            return 'numeric'
        
        # Check if datetime
        if pd.api.types.is_datetime64_any_dtype(col_data):
            return 'datetime'
        
        # Check if categorical (low unique count)
        unique_ratio = col_data.nunique() / len(col_data)
        if unique_ratio < 0.05:
            return 'categorical'
        
        return 'text'
    
    def _generate_business_meaning(self, column_name: str, profile: Dict[str, Any]) -> str:
        """
        Generate business meaning for column using LLM.
        
        Args:
            column_name: Name of column
            profile: Column profile dictionary
            
        Returns:
            Business meaning string
        """
        try:
            prompt = f"""Given this column from a dataset, provide a brief business meaning (1 sentence, max 15 words).

Column Name: {column_name}
Data Type: {profile['data_type']}
Semantic Type: {profile['semantic_type']}
Sample Values: {', '.join(profile['sample_values'][:5])}

Business Meaning:"""
            
            meaning = self.ollama_service.generate_response(
                prompt=prompt,
                temperature=0.3,
                task_type='insight_generation'
            )
            
            # Clean up response
            meaning = meaning.strip().split('\n')[0]  # Take first line only
            if len(meaning) > 100:
                meaning = meaning[:97] + "..."
            
            return meaning
        except Exception as e:
            logger.warning(f"Failed to generate business meaning for {column_name}: {e}")
            return f"{profile['semantic_type'].replace('_', ' ').title()} column"
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Assess overall data quality.
        
        Args:
            df: DataFrame
            
        Returns:
            Data quality metrics
        """
        total_cells = df.shape[0] * df.shape[1]
        null_cells = df.isnull().sum().sum()
        
        return {
            "total_cells": int(total_cells),
            "null_cells": int(null_cells),
            "null_percentage": round(null_cells / total_cells * 100, 2) if total_cells > 0 else 0,
            "completeness_score": round((1 - null_cells / total_cells) * 100, 1) if total_cells > 0 else 100,
            "duplicate_rows": int(df.duplicated().sum()),
            "duplicate_percentage": round(df.duplicated().sum() / len(df) * 100, 2) if len(df) > 0 else 0
        }


# Singleton instance (will be initialized with ollama_service when needed)
dataset_profiler = None

def get_profiler(ollama_service=None):
    """Get or create dataset profiler instance."""
    global dataset_profiler
    if dataset_profiler is None:
        dataset_profiler = DatasetProfiler(ollama_service)
    return dataset_profiler
