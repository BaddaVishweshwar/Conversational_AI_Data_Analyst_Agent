"""
Enhanced Exploration Agent

Executes 2-3 exploratory queries to understand data before main analysis.
Uses enhanced prompts with rich context.
"""

import logging
import json
from typing import Dict, Any, List
import pandas as pd
from ..services.ollama_service import ollama_service
from ..prompts.enhanced_prompts import (
    EXPLORATORY_QUERY_PROMPT_TEMPLATE,
    format_schema_for_prompt,
    format_sample_data_for_prompt
)

logger = logging.getLogger(__name__)


class EnhancedExplorationAgent:
    """Agent for executing exploratory queries with enhanced prompting."""
    
    async def explore(
        self,
        sub_questions: List[str],
        df: pd.DataFrame,
        enriched_schema: Dict[str, Any],
        max_queries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Execute exploratory queries based on sub-questions.
        
        Args:
            sub_questions: List of exploratory sub-questions
            df: DataFrame to query
            enriched_schema: Enriched schema with samples and statistics
            max_queries: Maximum number of exploratory queries to execute
            
        Returns:
            List of exploratory results with findings
        """
        logger.info(f"Starting exploratory analysis with {len(sub_questions)} sub-questions")
        
        exploratory_results = []
        previous_findings = []
        
        # Limit to max_queries
        for i, sub_question in enumerate(sub_questions[:max_queries]):
            try:
                logger.info(f"Exploratory query {i+1}/{min(len(sub_questions), max_queries)}: {sub_question}")
                
                # Generate SQL for this sub-question
                sql_result = await self._generate_exploratory_sql(
                    sub_question=sub_question,
                    enriched_schema=enriched_schema,
                    previous_findings=previous_findings
                )
                
                if not sql_result or not sql_result.get('sql'):
                    logger.warning(f"Failed to generate SQL for sub-question: {sub_question}")
                    continue
                
                sql = sql_result['sql']
                explanation = sql_result.get('explanation', '')
                
                # Execute the query
                execution_result = self._execute_exploratory_query(sql, df)
                
                if execution_result['success']:
                    # Generate finding summary
                    finding = self._summarize_finding(
                        sub_question=sub_question,
                        data=execution_result['data'],
                        explanation=explanation
                    )
                    
                    result = {
                        'sub_question': sub_question,
                        'sql': sql,
                        'explanation': explanation,
                        'data': execution_result['data'],
                        'row_count': len(execution_result['data']),
                        'finding': finding,
                        'success': True
                    }
                    
                    exploratory_results.append(result)
                    previous_findings.append(finding)
                    
                    logger.info(f"✅ Exploratory query {i+1} completed: {finding}")
                else:
                    logger.warning(f"Exploratory query {i+1} failed: {execution_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error in exploratory query {i+1}: {str(e)}")
                continue
        
        logger.info(f"Exploratory analysis complete: {len(exploratory_results)} successful queries")
        return exploratory_results
    
    async def _generate_exploratory_sql(
        self,
        sub_question: str,
        enriched_schema: Dict[str, Any],
        previous_findings: List[str]
    ) -> Dict[str, Any]:
        """Generate SQL for an exploratory sub-question."""
        try:
            # Format schema and sample data
            schema_details = format_schema_for_prompt(enriched_schema)
            sample_data = format_sample_data_for_prompt(
                enriched_schema.get('sample_data', [])
            )
            
            # Format previous findings
            findings_text = "\\n".join([f"- {f}" for f in previous_findings]) if previous_findings else "None yet"
            
            # Create prompt
            prompt = EXPLORATORY_QUERY_PROMPT_TEMPLATE.format(
                sub_question=sub_question,
                schema_details=schema_details,
                sample_data=sample_data,
                previous_findings=findings_text
            )
            
            # Generate with LLM
            response = await ollama_service.generate_response(
                prompt=prompt,
                json_mode=True,
                task_type='exploratory'
            )
            
            # Parse JSON response
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Error generating exploratory SQL: {str(e)}")
            return {}
    
    def _execute_exploratory_query(
        self,
        sql: str,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Execute an exploratory SQL query."""
        try:
            import duckdb
            
            # Execute with DuckDB
            conn = duckdb.connect(':memory:')
            conn.register('data', df)
            
            result = conn.execute(sql).fetchall()
            columns = [desc[0] for desc in conn.description]
            
            # Convert to list of dictionaries
            data = [dict(zip(columns, row)) for row in result]
            
            conn.close()
            
            return {
                'success': True,
                'data': data,
                'columns': columns,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error executing exploratory query: {str(e)}")
            return {
                'success': False,
                'data': [],
                'columns': [],
                'error': str(e)
            }
    
    def _summarize_finding(
        self,
        sub_question: str,
        data: List[Dict[str, Any]],
        explanation: str
    ) -> str:
        """Generate a 1-2 sentence summary of the finding."""
        try:
            if not data:
                return "No data found for this query."
            
            # Simple heuristic-based summary
            row_count = len(data)
            
            if row_count == 1:
                # Single metric result
                first_row = data[0]
                if len(first_row) == 1:
                    key, value = list(first_row.items())[0]
                    return f"{key}: {value}"
                else:
                    return f"Found single result: {first_row}"
            
            elif row_count <= 10:
                # Small result set - list key values
                if 'count' in str(data[0]).lower():
                    return f"Found {row_count} categories/groups in the data."
                else:
                    return f"Query returned {row_count} rows of data."
            
            else:
                # Large result set
                return f"Dataset contains {row_count} distinct values/records for this dimension."
            
        except Exception as e:
            logger.error(f"Error summarizing finding: {str(e)}")
            return "Finding summary unavailable."


# Singleton instance
enhanced_exploration_agent = EnhancedExplorationAgent()
