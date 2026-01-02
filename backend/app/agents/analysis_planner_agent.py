"""
Analysis Planner Agent

Generates validated, step-by-step analysis plans with SQL and Python code.
"""
import ollama
from typing import Dict, Any, List
import json
import re
import logging
from ..config import settings
from . import AnalysisPlan, AnalysisPlanStep, QueryRequirements, SchemaAnalysis, IntentResult

logger = logging.getLogger(__name__)


class AnalysisPlannerAgent:
    """
    Generates execution plans:
    1. Step-by-step analysis plan
    2. SQL query for data extraction
    3. Optional Python code for visualization
    
    Each step includes:
    - Operation type (filter, aggregate, sort)
    - Columns involved
    - Expected output schema
    """
    
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model_name = settings.OLLAMA_MODEL
    
    def plan(
        self,
        query: str,
        requirements: QueryRequirements,
        schema_analysis: SchemaAnalysis,
        intent: IntentResult,
        sample_data: List[Dict[str, Any]]
    ) -> AnalysisPlan:
        """
        Generate analysis plan
        
        Args:
            query: Natural language query
            requirements: Extracted requirements
            schema_analysis: Schema metadata
            intent: Query intent
            sample_data: Sample rows for context
            
        Returns:
            AnalysisPlan with steps, SQL, and optional Python code
        """
        
        # Build context
        schema_desc = self._format_schema(schema_analysis)
        sample_desc = json.dumps(sample_data[:3], indent=2, default=str)
        
        # Extract actual column names for the prompt
        actual_columns = list(schema_analysis.columns.keys())
        columns_list = ", ".join(actual_columns)
        
        prompt = f"""You are a Senior Data Analyst. Create a step-by-step analysis plan.

USER QUERY: "{query}"
INTENT: {intent.intent.value}

DATASET SCHEMA:
{schema_desc}

AVAILABLE COLUMNS (USE ONLY THESE): {columns_list}

SAMPLE DATA:
{sample_desc}

REQUIREMENTS:
- Required columns: {', '.join(requirements.required_columns)}
- Aggregations: {', '.join(requirements.aggregations)}
- Group by: {', '.join(requirements.groupby_columns)}
- Filters: {requirements.filters}

⚠️ CRITICAL SCHEMA RULES:
1. You MUST ONLY use columns from this list: {columns_list}
2. DO NOT invent, assume, or hallucinate column names like "region", "product", "category", etc.
3. If the query mentions a concept not in the schema, use the closest available column
4. VERIFY every column name against the available columns before using it
5. If no suitable column exists, create a simple query using available columns

EXAMPLE (for reference):
If schema has columns: TV, Radio, Newspaper, Sales
- ✅ CORRECT: SELECT TV, SUM(Sales) FROM data GROUP BY TV
- ❌ WRONG: SELECT region, SUM(Sales) FROM data GROUP BY region (region doesn't exist!)
- ✅ CORRECT: SELECT * FROM data LIMIT 10 (when unsure, show all data)

TASK: Generate a complete analysis plan using ONLY the available columns.

OUTPUT FORMAT (JSON):
{{
    "steps": [
        {{
            "step_number": 1,
            "operation": "filter|aggregate|sort|limit",
            "description": "Filter dataset to last 12 months",
            "columns_involved": ["date", "sales"],
            "expected_output": "Filtered dataset with 1000 rows"
        }}
    ],
    "sql_query": "SELECT ... FROM data ...",
    "python_code": "# Optional visualization code using matplotlib\\nax.bar(...)",
    "expected_columns": ["region", "total_sales"]
}}

SQL RULES:
1. Table name is ALWAYS 'data'
2. Use DuckDB syntax
3. LIMIT results to 500 rows max
4. Use proper aggregation functions (SUM, AVG, COUNT, etc.)
5. Include GROUP BY if aggregating
6. Use ORDER BY for sorting
7. ONLY use columns from this list: {columns_list}
8. If unsure, use SELECT * FROM data LIMIT 100

PYTHON RULES (for visualization):
1. DataFrame is available as 'df'
2. Matplotlib axis is available as 'ax'
3. DO NOT create new figures or axes
4. Use ax.bar(), ax.plot(), ax.scatter(), etc.
5. Set title, labels, and formatting
6. If no visualization needed, set python_code to empty string

ANALYSIS PLAN RULES:
1. Break down into clear steps
2. Each step should be atomic (one operation)
3. Steps should be in logical order
4. Specify columns involved in each step
5. ONLY use columns that exist in the schema: {columns_list}

Respond with ONLY the JSON, no other text."""

        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 2048}
            )
            
            # Parse JSON response
            result_text = response['response'].strip()
            
            # Extract JSON if wrapped in markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # Robust extraction: find start of JSON
            start_brace = result_text.find("{")
            start_bracket = result_text.find("[")
            
            start_index = -1
            end_index = -1
            
            if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
                start_index = start_brace
                end_index = result_text.rfind("}")
            elif start_bracket != -1:
                start_index = start_bracket
                end_index = result_text.rfind("]")
            
            if start_index != -1 and end_index != -1:
                result_text = result_text[start_index:end_index+1]
            
            try:
                result_data = json.loads(result_text)
            except json.JSONDecodeError as e:
                # Try to recover if "Extra data" (e.g. multiple JSON blocks)
                if e.msg.startswith("Extra data"):
                    try:
                        # Extract up to the error position
                        result_data = json.loads(result_text[:e.pos])
                    except Exception:
                        raise e # Re-raise original if recovery fails
                else:
                    raise e
            
            # Handle list output (steps only) -> Trigger fallback
            if isinstance(result_data, list):
                logger.warning("Model returned list instead of object, triggering fallback plan")
                return self._fallback_plan(query, requirements, schema_analysis)
            
            # Parse steps
            steps = []
            for step_data in result_data.get("steps", []):
                step = AnalysisPlanStep(
                    step_number=step_data.get("step_number", len(steps) + 1),
                    operation=step_data.get("operation", "unknown"),
                    description=step_data.get("description", ""),
                    columns_involved=step_data.get("columns_involved", []),
                    expected_output=step_data.get("expected_output", "")
                )
                steps.append(step)
            
            sql_query = result_data.get("sql_query", "")
            python_code = result_data.get("python_code", "")
            expected_columns = result_data.get("expected_columns", [])
            
            # Validate SQL
            validation_errors = self._validate_sql(sql_query, schema_analysis)
            
            # Validate Python code if present
            if python_code:
                python_validation = self._validate_python(python_code)
                validation_errors.extend(python_validation)
            
            plan = AnalysisPlan(
                steps=steps,
                sql_query=sql_query,
                python_code=python_code if python_code else None,
                expected_columns=expected_columns,
                validation_passed=(len(validation_errors) == 0),
                validation_errors=validation_errors
            )
            
            if validation_errors:
                logger.warning(f"⚠️ Plan validation errors: {validation_errors}")
            else:
                logger.info(f"✅ Analysis plan created: {len(steps)} steps, SQL generated")
            
            return plan
            
        except Exception as e:
            logger.error(f"Analysis planning failed: {e}")
            # Fallback to simple plan
            return self._fallback_plan(query, requirements, schema_analysis)
    
    def _format_schema(self, schema_analysis: SchemaAnalysis) -> str:
        """Format schema for prompt"""
        lines = []
        for col_name, col_meta in schema_analysis.columns.items():
            lines.append(f"  - {col_name}: {col_meta.type.value} "
                        f"(missing: {col_meta.missing_percentage}%, "
                        f"unique: {col_meta.unique_count})")
        return "\n".join(lines)
    
    def _validate_sql(self, sql: str, schema_analysis: SchemaAnalysis) -> List[str]:
        """Validate SQL query"""
        errors = []
        
        if not sql or not sql.strip():
            errors.append("SQL query is empty")
            return errors
        
        sql_upper = sql.upper()
        
        # Check for forbidden keywords
        forbidden = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in forbidden:
            if keyword in sql_upper:
                errors.append(f"Forbidden keyword: {keyword}")
        
        # Check if uses 'data' table
        if 'FROM DATA' not in sql_upper and 'FROM "DATA"' not in sql_upper:
            errors.append("SQL must query FROM data table")
        
        # Check if columns exist in schema - ENHANCED VALIDATION
        available_columns = set(schema_analysis.columns.keys())
        
        # Extract potential column references from SQL
        # Look for patterns like: SELECT col, GROUP BY col, WHERE col, ORDER BY col
        import re
        
        # Find all word-like tokens that could be column names
        # This is a simple heuristic - matches identifiers
        potential_cols = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', sql)
        
        # Filter out SQL keywords and common functions
        sql_keywords = {
            'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'LIMIT', 'OFFSET',
            'AS', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'USING',
            'SUM', 'AVG', 'COUNT', 'MIN', 'MAX', 'DISTINCT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
            'DATA', 'ASC', 'DESC', 'HAVING', 'CAST', 'ROUND', 'FLOOR', 'CEIL'
        }
        
        # Check each potential column
        invalid_columns = []
        for col in potential_cols:
            col_upper = col.upper()
            # Skip if it's a SQL keyword
            if col_upper in sql_keywords:
                continue
            # Skip if it's a number
            if col.isdigit():
                continue
            # Check if column exists in schema (case-insensitive)
            if not any(col.lower() == schema_col.lower() for schema_col in available_columns):
                # This might be a column reference
                invalid_columns.append(col)
        
        # Report invalid columns that appear multiple times (more likely to be actual column references)
        from collections import Counter
        col_counts = Counter(invalid_columns)
        for col, count in col_counts.items():
            if count >= 1:  # If used at least once and not in schema
                errors.append(f"Query validation failed: Groupby column '{col}' not found in schema")
        
        return errors
    
    def _validate_python(self, code: str) -> List[str]:
        """Validate Python code for safety"""
        errors = []
        
        # Check for dangerous operations
        dangerous_patterns = [
            r'import\s+os',
            r'import\s+sys',
            r'import\s+subprocess',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__',
            r'open\s*\(',
            r'file\s*\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                errors.append(f"Dangerous operation detected: {pattern}")
        
        return errors
    
    def _fallback_plan(
        self,
        query: str,
        requirements: QueryRequirements,
        schema_analysis: SchemaAnalysis
    ) -> AnalysisPlan:
        """Generate simple fallback plan"""
        
        # Validate columns against schema
        valid_cols = set(schema_analysis.columns.keys())
        
        # Safe strict mode for finding columns
        clean_aggs = []
        for agg in requirements.aggregations:
            # Check if any valid column is substring of agg
            # e.g. SUM(Sales) -> Sales in valid_cols
            is_valid = False
            for col in valid_cols:
                if col in agg:
                    is_valid = True
                    break
            if is_valid:
                clean_aggs.append(agg)
        
        clean_groupby = [col for col in requirements.groupby_columns if col in valid_cols]
        clean_required = [col for col in requirements.required_columns if col in valid_cols]
        
        sql = "SELECT * FROM data LIMIT 100"
        
        if clean_aggs and clean_groupby:
            agg_str = ', '.join(clean_aggs)
            group_str = ', '.join(clean_groupby)
            sql = f"SELECT {group_str}, {agg_str} FROM data GROUP BY {group_str} LIMIT 100"
        elif clean_required:
            cols_str = ', '.join(clean_required[:10])
            sql = f"SELECT {cols_str} FROM data LIMIT 100"
        
        steps = [
            AnalysisPlanStep(
                step_number=1,
                operation="select",
                description="Extract data from dataset",
                columns_involved=clean_required[:5] if clean_required else [],
                expected_output="Result dataset"
            )
        ]
        
        logger.info(f"⚠️ Using fallback analysis plan with validated schema")
        
        return AnalysisPlan(
            steps=steps,
            sql_query=sql,
            python_code=None,
            expected_columns=clean_required[:5],
            validation_passed=True,
            validation_errors=[]
        )


# Singleton instance
analysis_planner = AnalysisPlannerAgent()
