"""
SQL Correction Agent - Fix Failed SQL Queries

This agent analyzes SQL errors and generates corrected queries.
Implements intelligent error parsing and 3-attempt retry logic.
"""

from typing import Dict, Any, Optional
import logging
import re
from ..services.ollama_service import ollama_service
from ..services.anthropic_service import anthropic_service
from ..config import settings
from ..prompts.sql_system_prompts import SQL_CORRECTION_SYSTEM_PROMPT
from ..prompts.chain_of_thought_templates import COT_SQL_CORRECTION_TEMPLATE

logger = logging.getLogger(__name__)


class SQLCorrectionAgent:
    """Agent for correcting failed SQL queries"""
    
    def __init__(self):
        """Initialize SQL correction agent"""
        self.system_prompt = SQL_CORRECTION_SYSTEM_PROMPT
    
    async def correct_sql(
        self,
        failed_sql: str,
        error_message: str,
        original_question: str,
        schema: Dict[str, Any],
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Correct a failed SQL query based on error message.
        
        Args:
            failed_sql: The SQL that failed
            error_message: Error message from DuckDB
            original_question: Original user question
            schema: Dataset schema
            attempt: Current attempt number
            
        Returns:
            Dictionary with corrected SQL and metadata
        """
        try:
            logger.info(f"Attempting SQL correction (attempt {attempt})")
            logger.debug(f"Error: {error_message}")
            
            # Parse error type
            error_type = self._parse_error_type(error_message)
            logger.info(f"Error type identified: {error_type}")
            
            # Build schema context
            schema_context = self._format_schema(schema)
            
            # Build correction prompt using CoT template
            correction_prompt = COT_SQL_CORRECTION_TEMPLATE.format(
                question=original_question,
                failed_sql=failed_sql,
                error_message=error_message,
                schema=schema_context
            )
            
            # Generate corrected SQL
            if settings.USE_ANTHROPIC:
                corrected_sql = await anthropic_service.generate_response(
                    prompt=correction_prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.1,
                    task_type='error_correction',
                    max_tokens=1500
                )
            else:
                corrected_sql = await ollama_service.generate_response( # Fixed: use generate_response adapter if available or generate
                    prompt=correction_prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.1,
                    task_type='error_correction',
                    max_tokens=1500
                ) if hasattr(ollama_service, 'generate_response') else await ollama_service.generate(
                    system_prompt=self.system_prompt,
                    user_prompt=correction_prompt,
                    temperature=0.1,
                    task_type='error_correction', 
                    max_tokens=1500
                )
                
                if isinstance(corrected_sql, dict) and 'response' in corrected_sql:
                     corrected_sql = corrected_sql['response']
            
            # Clean up response
            corrected_sql = self._extract_sql(corrected_sql)
            
            # Validate correction
            if not corrected_sql or corrected_sql.strip() == failed_sql.strip():
                logger.warning("Correction produced same SQL or empty result")
                return {
                    "success": False,
                    "sql": None,
                    "error": "Failed to generate different SQL",
                    "error_type": error_type,
                    "attempt": attempt
                }
            
            logger.info(f"SQL corrected successfully (attempt {attempt})")
            
            return {
                "success": True,
                "sql": corrected_sql,
                "error_type": error_type,
                "changes_made": self._describe_changes(failed_sql, corrected_sql),
                "attempt": attempt
            }
            
        except Exception as e:
            logger.error(f"Error in SQL correction: {str(e)}")
            return {
                "success": False,
                "sql": None,
                "error": str(e),
                "error_type": "unknown",
                "attempt": attempt
            }
    
    def _parse_error_type(self, error_message: str) -> str:
        """
        Parse DuckDB error message to identify error type.
        
        Args:
            error_message: Error message string
            
        Returns:
            Error type string
        """
        error_lower = error_message.lower()
        
        # Column not found
        if 'column' in error_lower and ('not found' in error_lower or 'does not exist' in error_lower):
            return 'column_not_found'
        
        # Syntax error
        if 'syntax error' in error_lower or 'parser error' in error_lower:
            return 'syntax_error'
        
        # Type mismatch
        if 'type' in error_lower and ('mismatch' in error_lower or 'cannot' in error_lower):
            return 'type_mismatch'
        
        # Aggregation error
        if 'group by' in error_lower or 'aggregate' in error_lower:
            return 'aggregation_error'
        
        # Ambiguous column
        if 'ambiguous' in error_lower:
            return 'ambiguous_column'
        
        # Division by zero
        if 'division by zero' in error_lower:
            return 'division_by_zero'
        
        # Invalid function
        if 'function' in error_lower and ('not found' in error_lower or 'does not exist' in error_lower):
            return 'invalid_function'
        
        return 'unknown_error'
    
    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """Format schema for prompt."""
        if isinstance(schema, dict) and 'relevant_columns' in schema:
            columns = schema['relevant_columns'][:20]
        elif isinstance(schema, dict) and 'columns' in schema:
            columns = schema['columns'][:20]
        else:
            return "Schema information not available"
        
        formatted = []
        for col in columns:
            if isinstance(col, dict):
                col_name = col.get('column_name', col.get('name', 'unknown'))
                col_type = col.get('data_type', col.get('type', 'unknown'))
                formatted.append(f'  - "{col_name}" ({col_type})')
            else:
                formatted.append(f'  - "{col}"')
        
        return "\n".join(formatted)
    
    def _extract_sql(self, text: str) -> str:
        """Extract SQL from LLM response."""
        # Remove markdown code blocks
        text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        
        # Find SQL query
        sql_pattern = r'(WITH|SELECT|INSERT|UPDATE|DELETE)\s+.*?(?:;|$)'
        matches = re.findall(sql_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            sql = matches[0].strip()
            # Remove trailing semicolon if present
            if sql.endswith(';'):
                sql = sql[:-1]
            return sql
        
        # Fallback: return cleaned text
        return text.strip()
    
    def _describe_changes(self, old_sql: str, new_sql: str) -> str:
        """Describe what changed between old and new SQL."""
        if old_sql == new_sql:
            return "No changes"
        
        changes = []
        
        # Check for column name changes
        old_cols = set(re.findall(r'"([^"]+)"', old_sql))
        new_cols = set(re.findall(r'"([^"]+)"', new_sql))
        
        added_cols = new_cols - old_cols
        removed_cols = old_cols - new_cols
        
        if added_cols:
            changes.append(f"Added columns: {', '.join(added_cols)}")
        if removed_cols:
            changes.append(f"Removed columns: {', '.join(removed_cols)}")
        
        # Check for GROUP BY changes
        if 'GROUP BY' in new_sql and 'GROUP BY' not in old_sql:
            changes.append("Added GROUP BY clause")
        elif 'GROUP BY' not in new_sql and 'GROUP BY' in old_sql:
            changes.append("Removed GROUP BY clause")
        
        # Check for HAVING changes
        if 'HAVING' in new_sql and 'HAVING' not in old_sql:
            changes.append("Added HAVING clause")
        
        # Check for ORDER BY changes
        if 'ORDER BY' in new_sql and 'ORDER BY' not in old_sql:
            changes.append("Added ORDER BY clause")
        
        if not changes:
            return "SQL structure modified"
        
        return "; ".join(changes)


# Global instance
sql_correction_agent = SQLCorrectionAgent()
