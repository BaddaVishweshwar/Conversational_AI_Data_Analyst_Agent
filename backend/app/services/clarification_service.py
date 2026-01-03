"""
Ambiguity Detection and Clarification Service

Detects ambiguous queries and generates clarifying questions.
"""

import logging
from typing import Dict, Any, List, Optional
import json
from ..services.ollama_service import ollama_service

logger = logging.getLogger(__name__)


AMBIGUITY_DETECTION_PROMPT = """
TASK: Determine if this question is ambiguous or needs clarification

USER QUESTION: "{question}"

SCHEMA:
{schema_info}

COMMON AMBIGUITIES:
1. Multiple date columns (which to use for time range?)
2. Multiple similar columns (which metric to analyze?)
3. Unclear time range ("recent" = last week? month? year?)
4. Vague terms ("top" = top 5? 10? 20?)
5. Missing context (compare to what? filter by what?)

DECISION CRITERIA:
- If question is clear and specific → NOT ambiguous
- If question has vague terms or multiple interpretations → AMBIGUOUS

EXAMPLES:

Clear: "Show me sales for the last 30 days"
→ NOT ambiguous (specific time range)

Ambiguous: "Show me recent sales"
→ AMBIGUOUS (what is "recent"?)

Clear: "Top 10 products by revenue"
→ NOT ambiguous (specific number and metric)

Ambiguous: "Show me top products"
→ AMBIGUOUS (how many? by what metric?)

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
  "reason": "question is clear and specific"
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
            response = ollama_service.generate_response(
                prompt=prompt,
                json_mode=True,
                temperature=0.3  # Lower temperature for consistent detection
            )
            
            # Parse result
            result = json.loads(response)
            
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
