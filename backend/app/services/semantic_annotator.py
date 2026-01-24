"""
Semantic Annotator Service

Enriches technical schema metadata with business context, descriptions,
and synonyms using LLM.
"""

import logging
import json
from typing import Dict, Any, List
from .schema_profiler import TableProfile
from .ollama_service import ollama_service

logger = logging.getLogger(__name__)

# Prompt for annotating a single table
TABLE_ANNOTATION_PROMPT = """
You are a Data Architect. Analyze this table schema and provide business context.

Table: {table_name}
Columns:
{column_list}

Sample Data:
{sample_data}

Task:
1. Provide a 1-sentence description of what this table represents in a business context.
2. For each column, provide a short business description (if obvious) or "Standard field" if generic.
3. Identify potential synonyms for key columns (e.g., "revenue" -> "sales", "income").

Output JSON format:
{{
    "table_description": "Contains customer order history including dates and totals.",
    "column_annotations": {{
        "column_name": {{
            "description": "Total value of the order in USD",
            "synonyms": ["sales", "revenue", "order total"]
        }}
    }}
}}

Respond with ONLY the JSON.
"""

class SemanticAnnotator:
    """
    Uses LLM to add semantic meaning to database schemas.
    """
    
    def annotate_table(self, profile: TableProfile) -> Dict[str, Any]:
        """
        Generate semantic annotations for a table profile.
        """
        try:
            logger.info(f"🤖 Annotating table: {profile.name}")
            
            # Format inputs for prompt
            column_list = ""
            sample_rows = []
            
            # Use sample values from the first few columns to create a "row" view
            # This is a bit rough since samples in profile are per-column and not aligned rows
            # but it gives the LLM some context of values.
            # A better approach relies on actual row samples, but profile storage is columnar.
            # We will list samples per column for context.
            
            for col_name, col_profile in profile.columns.items():
                samples_str = ", ".join([str(s) for s in (col_profile.sample_values or [])[:3]])
                column_list += f"- {col_name} ({col_profile.dtype}): samples [{samples_str}]\n"
            
            prompt = TABLE_ANNOTATION_PROMPT.format(
                table_name=profile.name,
                column_list=column_list,
                sample_data="(See column samples above)"
            )
            
            # Call LLM
            response = ollama_service.generate_response(
                prompt=prompt,
                json_mode=True,
                task_type="planning", # Use planning temp (0.5) for some creativity
                max_tokens=1024
            )
            
            # Parse response
            try:
                annotations = json.loads(response)
                # Cleanup if wrapped in other keys (sometimes LLMs nest)
                if "response" in annotations:
                    annotations = annotations["response"]
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON annotation for {profile.name}")
                annotations = {
                    "table_description": f"Table containing {profile.name} data",
                    "column_annotations": {}
                }
                
            return annotations
            
        except Exception as e:
            logger.error(f"Error annotating table {profile.name}: {str(e)}")
            return {
                "table_description": f"Table containing {profile.name} data",
                "column_annotations": {}
            }

    def enrich_schema(self, profile: TableProfile, annotations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge technical profile with semantic annotations.
        """
        enriched = {
            "table_name": profile.name,
            "description": annotations.get("table_description", ""),
            "row_count": profile.row_count,
            "primary_key": profile.primary_key,
            "columns": {}
        }
        
        col_annotations = annotations.get("column_annotations", {})
        
        for col_name, col_profile in profile.columns.items():
            meta = col_annotations.get(col_name, {})
            enriched["columns"][col_name] = {
                "type": col_profile.dtype,
                "description": meta.get("description", ""),
                "synonyms": meta.get("synonyms", []),
                "stats": {
                    "null_pct": col_profile.null_percentage,
                    "unique": col_profile.unique_count,
                    "min": col_profile.min_value,
                    "max": col_profile.max_value
                },
                "samples": col_profile.sample_values
            }
            
        return enriched

# Singleton instance
semantic_annotator = SemanticAnnotator()
