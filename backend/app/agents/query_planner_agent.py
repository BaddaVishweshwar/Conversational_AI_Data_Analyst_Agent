"""
Query Planner Agent

Breaks down complex user questions into 3-5 exploratory sub-questions
before generating SQL. This enables comprehensive, multi-faceted analysis.
"""
import json
import logging
from typing import Dict, Any, List
import pandas as pd

from ..services.ollama_service import ollama_service
from ..services.prompt_templates import QUERY_PLANNING_PROMPT, OLLAMA_CONFIGS
from ..agents.schema_analyzer_agent import SchemaAnalyzerAgent
from ..agents import SchemaAnalysis

logger = logging.getLogger(__name__)


class QueryPlanningResult:
    """Result from query planning"""
    def __init__(
        self,
        understanding: str,
        approach: str,
        sub_questions: List[str],
        expected_visualizations: List[str]
    ):
        self.understanding = understanding
        self.approach = approach
        self.sub_questions = sub_questions
        self.expected_visualizations = expected_visualizations


class QueryPlannerAgent:
    """
    Plans comprehensive data analysis by breaking down questions into sub-questions.
    
    Flow:
    1. Receive user question + enriched schema
    2. Call LLM with planning prompt
    3. Parse structured JSON response
    4. Return planning result
    """
    
    def __init__(self):
        self.client = ollama_service.client
        self.model_name = ollama_service.model_name
        self.config = OLLAMA_CONFIGS["planning"]
    
    def plan(
        self,
        query: str,
        schema_analysis: SchemaAnalysis,
        df: pd.DataFrame,
        conversation_history: str = ""
    ) -> QueryPlanningResult:
        """
        Plan a comprehensive analysis approach.
        
        Args:
            query: User's natural language question
            schema_analysis: Rich schema metadata
            df: DataFrame for sample data
            conversation_history: Previous Q&A context
        
        Returns:
            QueryPlanningResult with understanding, approach, and sub-questions
        """
        logger.info(f"📋 Planning analysis for: '{query}'")
        
        try:
            # Generate enriched schema prompt
            enriched_schema = SchemaAnalyzerAgent.get_enriched_schema_prompt(schema_analysis, df)
            
            # Format sample data
            sample_data = self._format_sample_data(df)
            
            # Build prompt
            prompt = QUERY_PLANNING_PROMPT.format(
                enriched_schema=enriched_schema,
                sample_data=sample_data,
                row_count=schema_analysis.total_rows,
                conversation_history=conversation_history or "No previous context",
                user_question=query
            )
            
            # Call LLM
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options=self.config
            )
            
            # Parse JSON response
            result_text = response['response'].strip()
            result_data = self._extract_json(result_text)
            
            # Validate and construct result
            planning_result = QueryPlanningResult(
                understanding=result_data.get("understanding", "User wants to analyze the data"),
                approach=result_data.get("approach", "Basic analysis"),
                sub_questions=result_data.get("sub_questions", [
                    "What is the overall data volume?",
                    "What are the key patterns?"
                ]),
                expected_visualizations=result_data.get("expected_visualizations", ["table"])
            )
            
            logger.info(f"✅ Analysis plan created with {len(planning_result.sub_questions)} sub-questions")
            return planning_result
            
        except Exception as e:
            logger.error(f"Query planning failed: {e}")
            # Fallback planning
            return QueryPlanningResult(
                understanding=f"Analyze: {query}",
                approach="Direct analysis",
                sub_questions=["What does the data show?"],
                expected_visualizations=["table"]
            )
    
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response using robust utility"""
        from ...utils.json_extractor import extract_json_from_llm_response
        
        fallback = {
            "understanding": "Analyzing data",
            "approach": "Direct analysis",
            "sub_questions": ["What does the data show?"],
            "expected_visualizations": ["table"]
        }
        
        return extract_json_from_llm_response(text, fallback=fallback)
    
    def _format_sample_data(self, df: pd.DataFrame, max_rows: int = 5) -> str:
        """Format sample data as markdown table"""
        if df is None or df.empty:
            return "No sample data available"
        
        sample = df.head(max_rows)
        headers = list(sample.columns)
        
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["-------" for _ in headers]) + "|")
        
        for _, row in sample.iterrows():
            row_str = " | ".join(str(v)[:50] for v in row.values)  # Limit cell length
            lines.append(f"| {row_str} |")
        
        return "\n".join(lines)


# Singleton instance
query_planner = QueryPlannerAgent()
