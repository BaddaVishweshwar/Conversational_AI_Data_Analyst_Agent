"""
Schema Extraction Service - Extract and Profile Dataset Schemas

This service automatically extracts schema information from uploaded datasets,
generates statistical profiles, and prepares data for the semantic layer.

This is critical for achieving 80% query accuracy as mentioned in Backend.txt.
"""

from typing import Dict, Any, List, Optional
import logging
from sqlalchemy.orm import Session
from ..models import Dataset, DatasetSchema, ColumnProfile
from .duckdb_service import duckdb_service
from .embedding_service import embedding_service
import json

logger = logging.getLogger(__name__)


class SchemaExtractionService:
    """Service for extracting and profiling dataset schemas"""
    
    def __init__(self):
        """Initialize schema extraction service"""
        pass
    
    async def extract_and_store_schema(
        self,
        dataset_id: int,
        file_path: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Load file, extract schema, profile columns, generate embeddings.
        
        Args:
            dataset_id: Database ID of the dataset
            file_path: Path to the uploaded file
            db: Database session
            
        Returns:
            Dictionary with extraction results
        """
        try:
            logger.info(f"Starting schema extraction for dataset {dataset_id}")
            
            # Step 1: Load file into DuckDB
            load_result = duckdb_service.load_file(dataset_id, file_path, table_name="data")
            
            if load_result["status"] != "success":
                raise Exception("Failed to load file into DuckDB")
            
            # Step 2: Extract detailed schema
            schema_info = await self._extract_schema_details(dataset_id, "data")
            
            # Step 3: Profile columns (statistics)
            column_stats = duckdb_service.get_column_stats(dataset_id, "data")
            
            # Step 4: Get sample data
            sample_data = duckdb_service.get_sample_data(dataset_id, "data", n=100)
            
            # Step 5: Store schema in database with embeddings
            await self._store_schema_metadata(
                dataset_id, 
                schema_info, 
                column_stats,
                sample_data,
                db
            )
            
            # Step 6: Update dataset record
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                dataset.row_count = load_result["row_count"]
                dataset.column_count = len(schema_info)
                dataset.schema = json.dumps([
                    {"name": col["column_name"], "type": col["data_type"]}
                    for col in schema_info
                ])
                dataset.sample_data = json.dumps(sample_data[:10], default=str)  # Use default=str for non-serializable types
                db.commit()
            
            logger.info(f"Schema extraction completed for dataset {dataset_id}")
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "row_count": load_result["row_count"],
                "column_count": len(schema_info),
                "schema": schema_info,
                "sample_data": sample_data[:5]
            }
            
        except Exception as e:
            logger.error(f"Error in schema extraction: {str(e)}")
            raise
    
    async def _extract_schema_details(
        self,
        dataset_id: int,
        table_name: str
    ) -> List[Dict[str, Any]]:
        """
        Extract detailed schema information including inferred semantics.
        
        Args:
            dataset_id: Dataset identifier
            table_name: Name of the table in DuckDB
            
        Returns:
            List of column definitions with metadata
        """
        # Get basic schema from DuckDB
        basic_schema = duckdb_service.get_schema(dataset_id, table_name)
        
        # Enhance with semantic information
        enhanced_schema = []
        
        for col in basic_schema:
            col_name = col["column_name"]
            col_type = col["data_type"]
            
            # Infer semantic tags based on column name and type
            semantic_tags = self._infer_semantic_tags(col_name, col_type)
            
            # Generate business-friendly name
            business_name = self._generate_business_name(col_name)
            
            # Get sample values for this column
            sample_values = self._get_column_samples(dataset_id, table_name, col_name)
            
            enhanced_schema.append({
                "column_name": col_name,
                "data_type": col_type,
                "is_nullable": col.get("is_nullable", True),
                "business_name": business_name,
                "semantic_tags": semantic_tags,
                "sample_values": sample_values,
                "description": self._generate_column_description(col_name, col_type, semantic_tags)
            })
        
        return enhanced_schema
    
    def _infer_semantic_tags(self, column_name: str, data_type: str) -> List[str]:
        """
        Infer semantic tags from column name and type.
        
        Tags help categorize columns for better query understanding.
        """
        tags = []
        col_lower = column_name.lower()
        type_upper = data_type.upper()
        
        # Date/Time tags
        if any(keyword in col_lower for keyword in ['date', 'time', 'timestamp', 'created', 'updated', 'year', 'month', 'day']):
            tags.append('temporal')
        if 'DATE' in type_upper or 'TIME' in type_upper:
            tags.append('temporal')
        
        # Identifier tags
        if any(keyword in col_lower for keyword in ['id', '_id', 'key', 'code']):
            tags.append('identifier')
        
        # Metric tags (numeric measures)
        if any(keyword in col_lower for keyword in ['amount', 'total', 'sum', 'count', 'price', 'cost', 'revenue', 'sales', 'quantity', 'qty']):
            tags.append('metric')
        if any(t in type_upper for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC']):
            if 'identifier' not in tags:
                tags.append('numeric')
        
        # Dimension tags (categorical)
        if any(keyword in col_lower for keyword in ['name', 'type', 'category', 'status', 'region', 'country', 'city', 'state']):
            tags.append('dimension')
        if 'VARCHAR' in type_upper or 'TEXT' in type_upper or 'STRING' in type_upper:
            if 'identifier' not in tags:
                tags.append('dimension')
        
        # Percentage/Rate tags
        if any(keyword in col_lower for keyword in ['percent', 'rate', 'ratio', 'pct', '%']):
            tags.append('percentage')
        
        # Boolean tags
        if any(keyword in col_lower for keyword in ['is_', 'has_', 'flag', 'active', 'enabled']):
            tags.append('boolean')
        if 'BOOL' in type_upper:
            tags.append('boolean')
        
        # If no tags, add generic
        if not tags:
            tags.append('attribute')
        
        return tags
    
    def _generate_business_name(self, column_name: str) -> str:
        """
        Generate a human-friendly business name from a technical column name.
        
        Examples:
            customer_id -> Customer ID
            total_revenue_usd -> Total Revenue USD
            created_at -> Created At
        """
        # Replace underscores with spaces
        name = column_name.replace('_', ' ')
        
        # Capitalize each word
        name = ' '.join(word.capitalize() for word in name.split())
        
        # Handle common abbreviations
        replacements = {
            'Id': 'ID',
            'Url': 'URL',
            'Api': 'API',
            'Usd': 'USD',
            'Eur': 'EUR',
            'Gbp': 'GBP',
            'Qty': 'Quantity',
            'Pct': 'Percent',
            'Num': 'Number',
            'Amt': 'Amount'
        }
        
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        return name
    
    def _get_column_samples(
        self,
        dataset_id: int,
        table_name: str,
        column_name: str,
        n: int = 10
    ) -> List[Any]:
        """Get sample values from a column"""
        try:
            result = duckdb_service.execute_query(
                dataset_id,
                f'SELECT DISTINCT "{column_name}" FROM {table_name} WHERE "{column_name}" IS NOT NULL LIMIT {n}',
                limit=n
            )
            
            if result["success"]:
                return [row[column_name] for row in result["data"]]
            return []
        except:
            return []
    
    def _generate_column_description(
        self,
        column_name: str,
        data_type: str,
        semantic_tags: List[str]
    ) -> str:
        """Generate a description for a column based on its metadata"""
        business_name = self._generate_business_name(column_name)
        
        # Build description
        parts = [f"{business_name} ({data_type})"]
        
        if 'temporal' in semantic_tags:
            parts.append("- Date/time field")
        elif 'metric' in semantic_tags:
            parts.append("- Numeric metric for analysis")
        elif 'dimension' in semantic_tags:
            parts.append("- Categorical dimension for grouping")
        elif 'identifier' in semantic_tags:
            parts.append("- Unique identifier")
        
        return " ".join(parts)
    
    async def _store_schema_metadata(
        self,
        dataset_id: int,
        schema_info: List[Dict[str, Any]],
        column_stats: Dict[str, Dict[str, Any]],
        sample_data: List[Dict[str, Any]],
        db: Session
    ):
        """
        Store schema metadata and column profiles in database with embeddings.
        
        Args:
            dataset_id: Dataset identifier
            schema_info: Enhanced schema information
            column_stats: Statistical profiles
            sample_data: Sample rows
            db: Database session
        """
        # Delete existing schema entries for this dataset
        db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).delete()
        db.query(ColumnProfile).filter(ColumnProfile.dataset_id == dataset_id).delete()
        
        # Store each column's schema and profile
        for col_info in schema_info:
            col_name = col_info["column_name"]
            
            # Generate embedding for this column
            embedding = embedding_service.embed_column_schema(col_info)
            
            # Create DatasetSchema entry
            schema_entry = DatasetSchema(
                dataset_id=dataset_id,
                table_name="data",
                column_name=col_name,
                data_type=col_info["data_type"],
                business_name=col_info.get("business_name"),
                description=col_info.get("description"),
                semantic_tags=json.dumps(col_info.get("semantic_tags", [])),
                embedding=json.dumps(embedding) if embedding else None,
                is_nullable=col_info.get("is_nullable", True)
            )
            db.add(schema_entry)
            
            # Create ColumnProfile entry if stats available
            if col_name in column_stats:
                stats = column_stats[col_name]
                
                profile_entry = ColumnProfile(
                    dataset_id=dataset_id,
                    column_name=col_name,
                    null_count=stats.get("null_count"),
                    null_percentage=stats.get("null_percentage"),
                    unique_count=stats.get("unique_count"),
                    unique_percentage=stats.get("unique_percentage"),
                    min_value=str(stats.get("min")) if stats.get("min") is not None else None,
                    max_value=str(stats.get("max")) if stats.get("max") is not None else None,
                    mean_value=str(stats.get("mean")) if stats.get("mean") is not None else None,
                    median_value=str(stats.get("median")) if stats.get("median") is not None else None,
                    std_dev=str(stats.get("std_dev")) if stats.get("std_dev") is not None else None,
                    top_values=json.dumps(stats.get("top_values", [])),
                    cardinality=stats.get("unique_count"),
                    sample_values=json.dumps([str(v) for v in col_info.get("sample_values", [])])  # Convert to strings for JSON serialization
                )
                db.add(profile_entry)
        
        db.commit()
        logger.info(f"Stored schema metadata for {len(schema_info)} columns")


# Global instance
schema_extraction_service = SchemaExtractionService()
