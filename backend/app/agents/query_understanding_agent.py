"""
Query Understanding Agent

Extracts structured requirements from natural language queries.
"""
import ollama
from typing import Dict, Any, List
import json
import logging
from ..config import settings
from . import QueryRequirements, SchemaAnalysis, IntentResult

logger = logging.getLogger(__name__)


class QueryUnderstandingAgent:
    """
    Extracts structured requirements from natural language:
    - Required columns
    - Filters needed
    - Aggregations requested
    - Time ranges
    - Grouping dimensions
    - Sort order
    """
    
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model_name = settings.OLLAMA_MODEL
    
    def understand(
        self, 
        query: str, 
        schema_analysis: SchemaAnalysis,
        intent: IntentResult
    ) -> QueryRequirements:
        """
        Extract structured requirements from query
        
        Args:
            query: Natural language query
            schema_analysis: Schema metadata
            intent: Classified intent
            
        Returns:
            QueryRequirements with validated column references
        """
        
        # Build schema context
        available_columns = list(schema_analysis.columns.keys())
        numeric_cols = schema_analysis.numeric_columns
        categorical_cols = schema_analysis.categorical_columns
        datetime_cols = schema_analysis.datetime_columns
        
        prompt = f"""You are a query understanding expert. Extract structured requirements from this query.

QUERY: "{query}"
INTENT: {intent.intent.value}

AVAILABLE COLUMNS:
- Numeric: {', '.join(numeric_cols)}
- Categorical: {', '.join(categorical_cols)}
- Datetime: {', '.join(datetime_cols)}

TASK: Extract what the user wants to do with the data.

OUTPUT FORMAT (JSON):
{{
    "required_columns": ["Actual_Column_1", "Actual_Column_2"],
    "filters": [
        {{"column": "Actual_Column_1", "operator": "=", "value": "Value"}}
    ],
    "aggregations": ["SUM(Actual_Column_2)", "AVG(Actual_Column_3)"], 
    "groupby_columns": ["Actual_Category_Column"],
    "time_range": {{"start": "2024-01-01", "end": "2024-12-31"}},
    "sort_by": "Actual_Column_2 DESC",
    "limit": 10,
    "validation_errors": []
}}

RULES:
1. **CRITICAL**: ONLY use columns from the AVAILABLE COLUMNS list above. 
2. **NO HALLUCINATIONS**: Do NOT use 'category_col', 'region', or 'product' unless they are in the list.
3. **GROUPING**: If NO categorical columns exist in the list, leave "groupby_columns" EMPTY ([]). Do NOT invent a grouping column.
4. **AGGREGATION**: If no grouping possible, just request global aggregations (SUM, AVG).
5. Infer aggregations: "total"->SUM, "average"->AVG.

Respond with ONLY the JSON."""

        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 1024}
            )
            
            # Parse JSON response
            result_text = response['response'].strip()
            
            # Extract JSON if wrapped in markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # Robust extraction: find first { and last }
            first_brace = result_text.find("{")
            last_brace = result_text.rfind("}")
            if first_brace != -1 and last_brace != -1:
                result_text = result_text[first_brace:last_brace+1]
            
            result_data = json.loads(result_text)
            
            # Validate and FILTER column references
            validation_errors = []
            required_cols_raw = result_data.get("required_columns", [])
            groupby_cols_raw = result_data.get("groupby_columns", [])
            
            # Filter to only valid columns
            required_cols = [col for col in required_cols_raw if col in available_columns]
            groupby_cols = [col for col in groupby_cols_raw if col in available_columns]
            
            # Track what was filtered out
            for col in required_cols_raw:
                if col not in available_columns:
                    validation_errors.append(f"Column '{col}' not found in schema")
            
            for col in groupby_cols_raw:
                if col not in available_columns:
                    validation_errors.append(f"Groupby column '{col}' not found in schema")
            
            # If all columns were filtered out, use fallback
            if not required_cols and not groupby_cols:
                logger.warning("All extracted columns were invalid, using fallback")
                return self._fallback_understanding(query, schema_analysis, intent)
            
            requirements = QueryRequirements(
                required_columns=required_cols,
                filters=result_data.get("filters", []),
                aggregations=result_data.get("aggregations", []),
                groupby_columns=groupby_cols,
                time_range=result_data.get("time_range"),
                sort_by=result_data.get("sort_by"),
                limit=result_data.get("limit"),
                validation_errors=validation_errors
            )
            
            if validation_errors:
                logger.warning(f"⚠️ Filtered out invalid columns: {validation_errors}")
                logger.info(f"✅ Using valid columns: required={required_cols}, groupby={groupby_cols}")
            else:
                logger.info(f"✅ Query understood: {len(required_cols)} columns, "
                          f"{len(groupby_cols)} groupby dimensions")
            
            return requirements
            
        except Exception as e:
            logger.error(f"Query understanding failed: {e}")
            # Fallback to basic requirements
            return self._fallback_understanding(query, schema_analysis, intent)
    
    def _fallback_understanding(
        self, 
        query: str, 
        schema_analysis: SchemaAnalysis,
        intent: IntentResult
    ) -> QueryRequirements:
        """Simple rule-based fallback"""
        query_lower = query.lower()
        
        # Try to detect columns mentioned in query
        required_cols = []
        for col in schema_analysis.columns.keys():
            if col.lower() in query_lower:
                required_cols.append(col)
        
        # If no columns detected, use all numeric for aggregation
        if not required_cols:
            required_cols = schema_analysis.numeric_columns[:3]  # Limit to 3
        
        # Detect aggregations
        aggregations = []
        if any(word in query_lower for word in ['total', 'sum']):
            aggregations = [f"SUM({col})" for col in schema_analysis.numeric_columns[:1]]
        elif any(word in query_lower for word in ['average', 'avg', 'mean']):
            aggregations = [f"AVG({col})" for col in schema_analysis.numeric_columns[:1]]
        elif any(word in query_lower for word in ['count', 'number of']):
            aggregations = ["COUNT(*)"]
        
        # Detect groupby
        groupby_cols = []
        if intent.intent.value in ['COMPARATIVE', 'TREND']:
            # Use first categorical or datetime column
            if schema_analysis.categorical_columns:
                groupby_cols = [schema_analysis.categorical_columns[0]]
            elif schema_analysis.datetime_columns:
                groupby_cols = [schema_analysis.datetime_columns[0]]
        
        logger.info(f"⚠️ Using fallback query understanding")
        
        return QueryRequirements(
            required_columns=required_cols,
            filters=[],
            aggregations=aggregations,
            groupby_columns=groupby_cols,
            time_range=None,
            sort_by=None,
            limit=None,
            validation_errors=[]
        )


    async def analyze_query(
        self,
        user_question: str,
        schema_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Alias for V4 compatibility - converts to the understand() method format.
        
        Args:
            user_question: The user's question
            schema_context: Schema information from RAG
            
        Returns:
            Dictionary with intent and analysis (V4 format)
        """
        # For now, return a simple fallback response
        # This allows the V4 pipeline to continue working
        return {
            "intent": "DESCRIPTIVE",
            "confidence": 0.7,
            "entities": {
                "metrics": [],
                "dimensions": [],
                "time_period": None,
                "filters": []
            },
            "answerable": True,
            "required_columns": [],
            "ambiguities": [],
            "clarification_needed": False,
            "interpretation": user_question,
            "original_question": user_question
        }


# Singleton instance
query_understanding_agent = QueryUnderstandingAgent()
