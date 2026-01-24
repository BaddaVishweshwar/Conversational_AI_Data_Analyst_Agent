"""
Ambiguity Detection and Clarification Service

Detects ambiguous queries and generates clarifying questions.
"""

import logging
import re
import asyncio
import json
from typing import Dict, Any, List, Optional
from ..services.ollama_service import ollama_service
from ..utils.json_extractor import extract_json_from_llm_response

logger = logging.getLogger(__name__)


AMBIGUITY_DETECTION_PROMPT = """
TASK: Determine if this question is ambiguous or needs clarification

USER QUESTION: "{question}"

SCHEMA:
{schema_info}

INSTRUCTIONS:
You are a helpful data analyst helper. Your goal is to avoid annoying the user with questions if a reasonable default assumption can be made.

CRITICAL RULES For "AMBIGUOUS":
1.  ONLY return "is_ambiguous": true if it is IMPOSSIBLE to answer the question without more info.
2.  DO NOT ask for a time range if none is specified. DEFAULT TO "ALL TIME" or "OVERALL".
3.  DO NOT ask which columns to use if the user mentioned specific columns (e.g. "Sales vs Newspaper").
4.  DO NOT ask for "top 5 or 10" if vague. DEFAULT TO TOP 10.
5.  DO NOT ask for "sum or average". DEFAULT TO SUM for metrics, COUNT for categories.

EXAMPLES of NOT AMBIGUOUS (Apply Defaults):
- "Show me sales" -> Default to Total Sales over all time.
- "Compare TV vs Sales" -> Default to Scatter plot / Correlation of TV vs Sales.
- "Sales by Radio" -> Default to Sales vs Radio spend.
- "Top products" -> Default to Top 10 products by count/sales.

EXAMPLES of AMBIGUOUS (Must Ask):
- "Compare sales vs spend" -> (If schema has TV, Radio, Newspaper spend columns, we don't know which ONE or ALL).
- "How did we do?" -> (Too vague, no metrics specified).

YOUR TURN:
Analyze the question above.

Return JSON:
{{
  "is_ambiguous": true/false,
  "reason": "why it's ambiguous or why it's clear",
  "clarification_needed": "specific question to ask user",
  "options": ["option1", "option2", "option3"]
}}

If NOT ambiguous, return:
{{
  "is_ambiguous": false,
  "reason": "Using defaults: All time, relevant columns."
}}
"""


class ClarificationService:
    """Detects ambiguous queries and generates clarifying questions."""
    
    @staticmethod
    async def check_for_ambiguity(
        question: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if a question needs clarification.
        
        Args:
            question: User's natural language question
            schema: Dataset schema information
            
        Returns:
            Ambiguity check result with clarification if needed
        """
        try:
            # Format schema info
            schema_info = ClarificationService._format_schema_brief(schema)
            
            # Create prompt
            prompt = AMBIGUITY_DETECTION_PROMPT.format(
                question=question,
                schema_info=schema_info
            )
            
            # Generate with LLM
            # Wrap synchronous call in to_thread
            response = await asyncio.to_thread(
                ollama_service.generate_response,
                prompt=prompt,
                json_mode=True,
                temperature=0.3
            )
            
            # Parse result
            result = extract_json_from_llm_response(response)
            if not isinstance(result, dict):
                raise ValueError(f"Ambiguity check returned non-dict: {type(result)}")
            
            logger.info(f"Ambiguity check: {result.get('is_ambiguous', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking ambiguity: {str(e)}")
            # Default to not ambiguous on error
            return {
                "is_ambiguous": False,
                "reason": "Unable to check for ambiguity"
            }
    
    @staticmethod
    def _format_schema_brief(schema: Dict[str, Any]) -> str:
        """Format schema for ambiguity detection."""
        if not schema or not schema.get('columns'):
            return "No schema available"
        
        lines = ["Available columns:"]
        for col in schema.get('columns', [])[:10]:  # Limit to 10 columns
            col_name = col.get('name', 'unknown')
            col_type = col.get('type', 'unknown')
            lines.append(f"  - {col_name} ({col_type})")
        
        return "\n".join(lines)


# Singleton instance
clarification_service = ClarificationService()
