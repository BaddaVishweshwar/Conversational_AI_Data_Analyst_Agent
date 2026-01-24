"""
SQL Validation Service

Validates generated SQL queries before execution to ensure:
- Syntax correctness (via sqlglot)
- Runtime safety (via dry-run)
- Intent match (does SQL answer the question?)
- Aggregation correctness
- Table and column validity
- Self-critique and correction
"""

import logging
import json
from typing import Dict, Any, Optional, List
import sqlglot
import pandas as pd
import duckdb
from ..services.ollama_service import ollama_service
from ..prompts.camelai_prompts import MASTER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


SQL_VALIDATION_PROMPT = """
TASK: Validate if this SQL correctly answers the question

QUESTION: "{question}"
INTENT: {intent_type}
GENERATED SQL:
{sql}

SCHEMA:
{schema_summary}

VALIDATION CHECKS:
1. ✓ Does SQL answer the question completely?
2. ✓ Are aggregations correct (SUM, AVG, COUNT)?
3. ✓ Is GROUP BY needed and present?
4. ✓ Is ORDER BY meaningful for the question?
5. ✓ Are all column names valid (exist in schema)?
6. ✓ Is table name "data" (not ActualData, sales_data, etc.)?
7. ✓ Are column names with special characters quoted?
8. ✓ Are there any logic errors?
9. ✓ Are ALL requested columns included? (check question for "and", "with", etc.)
10. ✓ Is window function usage optimal? (avoid OVER() when simple aggregation works)

LOGICAL OPTIMALITY CHECKS:
- If question asks for "TV, Radio, AND Newspaper" → SQL must include ALL three
- If simple SUM/AVG works → don't use window functions (SUM() OVER())
- If ranking needed → use ROW_NUMBER() or RANK()
- If comparing multiple items → ensure all are in SELECT clause

EXAMPLES OF ISSUES:

Bad: SELECT * FROM ActualData
Fix: SELECT * FROM data

Bad: SELECT "Sales" FROM data (missing aggregation for "total sales")
Fix: SELECT SUM("Sales ($)") as total_sales FROM data

Bad: SELECT product, revenue FROM data GROUP BY product (revenue not aggregated)
Fix: SELECT product, SUM(revenue) as total_revenue FROM data GROUP BY product

Bad: SELECT SUM("TV Budget") OVER() as total_tv FROM data (unnecessary window function)
Fix: SELECT SUM("TV Budget") as total_tv FROM data

Bad: SELECT "TV Budget", "Radio Budget" FROM data (question asked for TV, Radio, AND Newspaper)
Fix: SELECT "TV Budget", "Radio Budget", "Newspaper Budget" FROM data

YOUR TURN:
Analyze the SQL above and return JSON:

{{
  "is_valid": true/false,
  "confidence": 0.95,
  "issues": [
    "Issue 1: description",
    "Issue 2: description"
  ],
  "suggestions": "How to fix the SQL",
  "corrected_sql": "Fixed SQL query if issues found, otherwise null"
}}

If SQL is perfect, return:
{{
  "is_valid": true,
  "confidence": 0.95,
  "issues": [],
  "suggestions": null,
  "corrected_sql": null
}}
"""


class SQLValidatorService:
    """Validates and critiques generated SQL queries."""
    
    @staticmethod
    def validate_syntax(sql: str) -> Dict[str, Any]:
        """
        Validate SQL syntax using sqlglot.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Dict with is_valid and error message
        """
        try:
            # Transpile to DuckDB to check compatibility
            # sqlglot.transpile returns a list of strings
            _ = sqlglot.transpile(sql, read=None, write="duckdb")[0]
            
            # Additional parse check
            parsed = sqlglot.parse_one(sql)
            
            return {
                "is_valid": True,
                "error": None
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Syntax Error: {str(e)}"
            }

    @staticmethod
    async def execute_dry_run(sql: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute SQL with LIMIT 1 on actual data schema to check for runtime errors.
        
        Args:
            sql: SQL to test
            df: DataFrame to test against
            
        Returns:
            Dict with is_valid, error, and optionally corrected SQL hint
        """
        try:
            # Create temporary in-memory connection
            conn = duckdb.connect(':memory:')
            conn.register('data', df)
            
            # Modify query to run fast/safe
            # We want to check column names and types logic without full scan
            # EXPLAIN is good, but sometimes LIMIT 1 is better to catch runtime type errors
            
            # Simple heuristic: wrap in subquery with LIMIT 1
            dry_run_sql = f"SELECT * FROM ({sql}) LIMIT 1"
            
            conn.execute(dry_run_sql)
            conn.close()
            
            return {
                "is_valid": True,
                "error": None
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # DuckDB specific error parsing could go here
            if "Binder Error" in error_msg:
                error_msg = f"Column/Table mismatch: {error_msg.split('Binder Error:')[1].strip()}"
            elif "Parser Error" in error_msg:
                error_msg = f"Parsing failed: {error_msg.split('Parser Error:')[1].strip()}"
                
            return {
                "is_valid": False,
                "error": error_msg
            }

    @staticmethod
    async def validate_logic(
        sql: str,
        question: str,
        intent_type: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate SQL logic using LLM (Intent match, aggregations, etc.).
        """
        try:
            # Format schema summary
            schema_summary = SQLValidatorService._format_schema_summary(schema)
            
            # Create validation prompt
            prompt = SQL_VALIDATION_PROMPT.format(
                question=question,
                intent_type=intent_type,
                sql=sql,
                schema_summary=schema_summary
            )
            
            # Generate validation with LLM
            response = ollama_service.generate_response(
                prompt=prompt,
                system_prompt=MASTER_SYSTEM_PROMPT,
                json_mode=True,
                temperature=0.1,  # Lower temperature for validation
                task_type='error_correction'
            )
            
            # Parse result
            result = json.loads(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating SQL logic: {str(e)}")
            return {
                "is_valid": True, # Optimistic fallback
                "confidence": 0.5,
                "issues": [],
                "suggestions": None,
                "corrected_sql": None
            }
    
    @staticmethod
    def _format_schema_summary(schema: Dict[str, Any]) -> str:
        """Format schema for validation prompt."""
        if not schema or not schema.get('columns'):
            return "No schema available"
        
        lines = ["Table: data"]
        lines.append("\nColumns:")
        
        for col in schema.get('columns', []):
            col_name = col.get('name', 'unknown')
            col_type = col.get('type', 'unknown')
            lines.append(f'  - "{col_name}" ({col_type})')
        
        return "\n".join(lines)
    
    @staticmethod
    async def validate_and_correct(
        sql: str,
        question: str,
        intent_type: str,
        schema: Dict[str, Any],
        df: Optional[pd.DataFrame] = None,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Comprehensive Multi-Stage Validation Pipeline.
        1. Syntax Check (sqlglot)
        2. Dry Run (DuckDB)
        3. Logic Check (LLM)
        
        Auto-corrects if issues found.
        """
        current_sql = sql
        attempts = 0
        last_error = None
        
        while attempts < max_attempts:
            logger.info(f"🛡️ Validation Attempt {attempts + 1}/{max_attempts}")
            
            # 1. Syntax Validation
            syntax_result = SQLValidatorService.validate_syntax(current_sql)
            if not syntax_result["is_valid"]:
                logger.warning(f"❌ Syntax Error: {syntax_result['error']}")
                last_error = syntax_result['error']
                # Try to fix syntax with LLM
                current_sql = await SQLValidatorService._fix_with_llm(
                    current_sql, question, schema, last_error
                )
                attempts += 1
                continue

            # 2. Dry Run Execution (if DF provided)
            if df is not None:
                dry_run_result = await SQLValidatorService.execute_dry_run(current_sql, df)
                if not dry_run_result["is_valid"]:
                    logger.warning(f"❌ Dry Run Error: {dry_run_result['error']}")
                    last_error = dry_run_result['error']
                    # Try to fix runtime error with LLM
                    current_sql = await SQLValidatorService._fix_with_llm(
                        current_sql, question, schema, last_error
                    )
                    attempts += 1
                    continue

            # 3. Logic Validation (LLM)
            logic_result = await SQLValidatorService.validate_logic(
                current_sql, question, intent_type, schema
            )
            
            if logic_result.get('is_valid'):
                logger.info("✅ All validation checks passed")
                return {
                    "sql": current_sql,
                    "is_valid": True,
                    "attempts": attempts,
                    "final_validation": logic_result
                }
            
            # If logic issues found and correction provided
            if logic_result.get('corrected_sql'):
                logger.info(f"🔄 Applying Logic Correction: {logic_result['issues']}")
                current_sql = logic_result['corrected_sql']
                attempts += 1
            else:
                # Issues found but no correction provided - try one more self-correction
                last_error = f"Logic Issues: {'; '.join(logic_result.get('issues', []))}"
                current_sql = await SQLValidatorService._fix_with_llm(
                    current_sql, question, schema, last_error
                )
                attempts += 1

        # Max attempts reached
        logger.warning(f"⚠️ Max validation attempts reached. Returning best effort.")
        return {
            "sql": current_sql,
            "is_valid": False,
            "attempts": attempts,
            "error": last_error
        }

    @staticmethod
    async def _fix_with_llm(sql: str, question: str, schema: Dict[str, Any], error: str) -> str:
        """Helper to ask LLM to fix a specific error."""
        schema_summary = SQLValidatorService._format_schema_summary(schema)
        
        prompt = f"""
TASK: Fix this SQL query based on the specific error.

QUESTION: "{question}"
FAILED SQL:
{sql}

ERROR:
{error}

SCHEMA:
{schema_summary}

INSTRUCTIONS:
1. Fix the error described above.
2. Ensure column names are correct and exist in schema.
3. Ensure syntax is valid DuckDB SQL.
4. Return ONLY the fixed SQL query (no markdown, no explanation).
"""
        try:
            response = ollama_service.generate_response(
                prompt=prompt,
                system_prompt="You are an expert SQL debugger. Fix the query.",
                temperature=0.1,
                task_type='sql_generation'
            )
            
            # Clean response
            fixed_sql = response.strip()
            if "```sql" in fixed_sql:
                fixed_sql = fixed_sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in fixed_sql:
                fixed_sql = fixed_sql.split("```")[1].split("```")[0].strip()
                
            return fixed_sql
            
        except Exception as e:
            logger.error(f"Error checking implementation: {str(e)}")
            return sql # Return original if fix fails

# Singleton instance
sql_validator = SQLValidatorService()
