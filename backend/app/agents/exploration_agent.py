"""
Exploration Agent

Runs 2-3 preliminary SQL queries to understand the data before main analysis.
Provides context that informs better SQL generation and insights.
"""
import json
import logging
from typing import Dict, Any, List
import pandas as pd
import duckdb

from ..services.ollama_service import ollama_service
from ..services.prompt_templates import EXPLORATION_SQL_PROMPT, OLLAMA_CONFIGS
from ..agents.schema_analyzer_agent import SchemaAnalyzerAgent
from ..agents import SchemaAnalysis

logger = logging.getLogger(__name__)


class ExplorationResult:
    """Result from a single exploratory query"""
    def __init__(
        self,
        question: str,
        sql: str,
        result: Any,
        finding: str,
        execution_time_ms: float = 0
    ):
        self.question = question
        self.sql = sql
        self.result = result
        self.finding = finding
        self.execution_time_ms = execution_time_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        return {
            "question": self.question,
            "sql": self.sql,
            "result": self.result,
            "finding": self.finding,
            "execution_time_ms": self.execution_time_ms
        }


class ExplorationAgent:
    """
    Generates and executes exploratory SQL queries.
    
    Flow for each sub-question:
    1. Generate simple SQL using LLM
    2. Execute SQL against DataFrame
    3. Analyze result and create finding summary
    4. Return structured ExplorationResult
    """
    
    def __init__(self):
        self.client = ollama_service.client
        self.model_name = ollama_service.model_name
        self.config = OLLAMA_CONFIGS["exploration"]
    
    def explore(
        self,
        sub_questions: List[str],
        df: pd.DataFrame,
        schema_analysis: SchemaAnalysis,
        max_queries: int = 3
    ) -> List[ExplorationResult]:
        """
        Run exploratory queries for each sub-question.
        
        Args:
            sub_questions: List of exploratory questions from planner
            df: DataFrame to query
            schema_analysis: Rich schema metadata
            max_queries: Maximum number of queries to run
        
        Returns:
            List of ExplorationResult objects
        """
        logger.info(f"🔍 Running {min(len(sub_questions), max_queries)} exploratory queries")
        
        results = []
        for i, question in enumerate(sub_questions[:max_queries]):
            try:
                result = self._explore_question(question, df, schema_analysis)
                results.append(result)
                logger.info(f"✅ Exploration {i+1}/{max_queries}: {result.finding}")
            except Exception as e:
                logger.error(f"Exploration query {i+1} failed: {e}")
                # Add fallback result
                results.append(ExplorationResult(
                    question=question,
                    sql="-- Failed to generate",
                    result=None,
                    finding=f"Unable to explore: {str(e)[:100]}"
                ))
        
        return results
    
    def _explore_question(
        self,
        question: str,
        df: pd.DataFrame,
        schema_analysis: SchemaAnalysis
    ) -> ExplorationResult:
        """Generate SQL and execute for a single exploratory question"""
        import time
        
        # Generate enriched schema context
        schema_context = SchemaAnalyzerAgent.get_enriched_schema_prompt(schema_analysis, df)
        sample_data = self._format_sample_data(df)
        column_list = ", ".join(schema_analysis.columns.keys())
        
        # Build prompt
        prompt = EXPLORATION_SQL_PROMPT.format(
            schema_context=schema_context,
            sample_data=sample_data,
            column_list=column_list,
            exploration_question=question
        )
        
        # Generate SQL
        response = self.client.generate(
            model=self.model_name,
            prompt=prompt,
            options=self.config
        )
        
        # Parse response
        result_text = response['response'].strip()
        result_data = self._extract_json(result_text)
        
        sql = result_data.get("sql", "SELECT COUNT(*) FROM data")
        explanation = result_data.get("explanation", "Basic query")
        
        # Execute SQL
        start_time = time.time()
        try:
            conn = duckdb.connect(':memory:')
            conn.register('data', df)
            query_result = conn.execute(sql).fetchall()
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Format result
            if query_result:
                if len(query_result) == 1 and len(query_result[0]) == 1:
                    # Single value
                    formatted_result = query_result[0][0]
                    finding = f"{explanation}: {formatted_result}"
                else:
                    # Multiple rows/columns
                    formatted_result = query_result[:5]  # Limit to 5 rows
                    finding = f"{explanation} (returned {len(query_result)} rows)"
            else:
                formatted_result = None
                finding = f"{explanation}: No results"
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"Exploration SQL execution failed: {e}")
            formatted_result = None
            finding = f"Query failed: {str(e)[:100]}"
            execution_time_ms = 0
        
        return ExplorationResult(
            question=question,
            sql=sql,
            result=formatted_result,
            finding=finding,
            execution_time_ms=execution_time_ms
        )
    
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response using robust utility"""
        from ...utils.json_extractor import extract_json_from_llm_response
        
        fallback = {
            "sql": "SELECT COUNT(*) FROM data",
            "explanation": "Basic query",
            "expected_rows": 1
        }
        
        return extract_json_from_llm_response(text, fallback=fallback)
    
    def _format_sample_data(self, df: pd.DataFrame, max_rows: int = 3) -> str:
        """Format sample data as markdown table"""
        if df is None or df.empty:
            return "No sample data"
        
        sample = df.head(max_rows)
        headers = list(sample.columns)
        
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["-------" for _ in headers]) + "|")
        
        for _, row in sample.iterrows():
            row_str = " | ".join(str(v)[:30] for v in row.values)
            lines.append(f"| {row_str} |")
        
        return "\n".join(lines)


# Singleton instance
exploration_agent = ExplorationAgent()
