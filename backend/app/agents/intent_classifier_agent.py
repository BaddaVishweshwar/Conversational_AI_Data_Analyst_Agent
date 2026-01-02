"""
Intent Classification Agent

Classifies user queries into analytical intent categories to drive the entire pipeline.
"""
import ollama
from typing import Dict, Any
import json
import logging
from ..config import settings
from . import IntentType, IntentResult

logger = logging.getLogger(__name__)


class IntentClassifierAgent:
    """
    Classifies queries into intent categories:
    - DESCRIPTIVE: What happened? (e.g., "Show me sales by region")
    - DIAGNOSTIC: Why did it happen? (e.g., "Why did sales drop?")
    - COMPARATIVE: A vs B (e.g., "Compare Q1 vs Q2")
    - TREND: Over time (e.g., "Show revenue trend")
    - PREDICTIVE: Forecast (e.g., "Predict next month")
    - PRESCRIPTIVE: Recommendations (e.g., "What should we do?")
    """
    
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model_name = settings.OLLAMA_MODEL
    
    def classify(self, query: str, schema: Dict[str, Any]) -> IntentResult:
        """
        Classify query intent
        
        Args:
            query: Natural language query
            schema: Dataset schema for context
            
        Returns:
            IntentResult with intent type, confidence, and requirements
        """
        
        # Check for datetime columns to inform intent
        has_datetime = any('date' in col.lower() or 'time' in col.lower() 
                          for col in schema.keys())
        
        prompt = f"""You are an intent classification expert. Classify this query into ONE category.

QUERY: "{query}"

DATASET COLUMNS: {', '.join(schema.keys())}
HAS TIME DIMENSION: {has_datetime}

INTENT CATEGORIES:
1. DESCRIPTIVE - Shows what happened (e.g., "total sales", "top products", "list customers")
2. DIAGNOSTIC - Explains why (e.g., "why did X drop", "what caused Y", "reasons for Z")
3. COMPARATIVE - Compares entities (e.g., "A vs B", "compare regions", "difference between")
4. TREND - Shows change over time (e.g., "trend", "over time", "growth", "monthly")
5. PREDICTIVE - Forecasts future (e.g., "predict", "forecast", "next month")
6. PRESCRIPTIVE - Recommends actions (e.g., "what should we do", "recommend", "suggest")

CLASSIFICATION RULES:
- If query mentions "trend", "over time", "monthly", "growth" → TREND
- If query asks "why", "reason", "cause" → DIAGNOSTIC
- If query has "vs", "compare", "difference" → COMPARATIVE
- If query asks "predict", "forecast" → PREDICTIVE
- If query asks "recommend", "should", "suggest" → PRESCRIPTIVE
- Otherwise → DESCRIPTIVE

OUTPUT FORMAT (JSON):
{{
    "intent": "DESCRIPTIVE|DIAGNOSTIC|COMPARATIVE|TREND|PREDICTIVE|PRESCRIPTIVE",
    "confidence": 0.0-1.0,
    "required_operations": ["operation1", "operation2"],
    "time_dimension_required": true/false,
    "comparison_required": true/false,
    "reasoning": "brief explanation"
}}

Respond with ONLY the JSON, no other text."""

        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 512}
            )
            
            # Parse JSON response
            result_text = response['response'].strip()
            
            # Extract JSON if wrapped in markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result_data = json.loads(result_text)
            
            # Validate intent type
            intent_str = result_data.get("intent", "DESCRIPTIVE")
            try:
                intent = IntentType[intent_str]
            except KeyError:
                logger.warning(f"Invalid intent '{intent_str}', defaulting to DESCRIPTIVE")
                intent = IntentType.DESCRIPTIVE
            
            intent_result = IntentResult(
                intent=intent,
                confidence=float(result_data.get("confidence", 0.8)),
                required_operations=result_data.get("required_operations", []),
                time_dimension_required=result_data.get("time_dimension_required", False),
                comparison_required=result_data.get("comparison_required", False)
            )
            
            logger.info(f"✅ Intent classified: {intent.value} (confidence: {intent_result.confidence:.2f})")
            return intent_result
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Fallback to rule-based classification
            return self._fallback_classification(query, has_datetime)
    
    def _fallback_classification(self, query: str, has_datetime: bool) -> IntentResult:
        """Rule-based fallback classification"""
        query_lower = query.lower()
        
        # Simple keyword matching
        if any(word in query_lower for word in ['trend', 'over time', 'growth', 'monthly', 'yearly']):
            intent = IntentType.TREND
            time_required = True
        elif any(word in query_lower for word in ['why', 'reason', 'cause', 'explain']):
            intent = IntentType.DIAGNOSTIC
            time_required = False
        elif any(word in query_lower for word in ['vs', 'versus', 'compare', 'difference', 'between']):
            intent = IntentType.COMPARATIVE
            time_required = False
        elif any(word in query_lower for word in ['predict', 'forecast', 'future', 'next']):
            intent = IntentType.PREDICTIVE
            time_required = True
        elif any(word in query_lower for word in ['recommend', 'should', 'suggest', 'advice']):
            intent = IntentType.PRESCRIPTIVE
            time_required = False
        else:
            intent = IntentType.DESCRIPTIVE
            time_required = False
        
        logger.info(f"⚠️ Using fallback classification: {intent.value}")
        
        return IntentResult(
            intent=intent,
            confidence=0.6,  # Lower confidence for fallback
            required_operations=["aggregate"] if intent == IntentType.DESCRIPTIVE else [],
            time_dimension_required=time_required,
            comparison_required=(intent == IntentType.COMPARATIVE)
        )


# Singleton instance
intent_classifier = IntentClassifierAgent()
