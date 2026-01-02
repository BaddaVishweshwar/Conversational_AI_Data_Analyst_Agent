"""
Insight Generator Agent

Generates structured, fact-based insights with anti-hallucination guardrails.
"""
import ollama
from typing import Dict, Any, List
import json
import re
import logging
from ..config import settings
from . import Insights, ExecutionResult, IntentResult, InterpretationResult

logger = logging.getLogger(__name__)


class InsightGeneratorAgent:
    """
    Generates 4-section insights:
    
    1. DIRECT ANSWER (1-2 sentences)
    2. WHAT THE DATA SHOWS (facts only)
    3. WHY THIS HAPPENED (patterns, drivers)
    4. BUSINESS IMPLICATIONS (actions)
    
    ANTI-HALLUCINATION RULES:
    - Only cite metrics from execution_result
    - No invented percentages or numbers
    - If data insufficient, say "Cannot determine from available data"
    """
    
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model_name = settings.OLLAMA_MODEL
    
    def generate(
        self,
        query: str,
        execution_result: ExecutionResult,
        intent: IntentResult,
        interpretation: InterpretationResult,
        conversation_history: List[Dict[str, str]] = []
    ) -> Insights:
        """
        Generate structured insights with statistical grounding
        
        Args:
            query: Natural language query
            execution_result: Execution results with data and metrics
            intent: Query intent
            interpretation: Statistical interpretation findings
            conversation_history: Recent conversation history
            
        Returns:
            Insights with 4-section structure
        """
        
        if not execution_result.success or not execution_result.data:
            logger.warning("No data available for insight generation")
            return Insights(
                direct_answer="No data available to answer this question.",
                what_data_shows=["The query did not return any results."],
                why_it_happened=["This could be due to filters excluding all data or an empty dataset."],
                business_implications=["Review the query filters and dataset to ensure data is available."],
                confidence=0.0,
                data_sufficiency="insufficient"
            )
        
        # Limit data for context (avoid token overflow)
        limited_data = execution_result.data[:10]
        
        # Extract all metrics from execution result
        metrics_summary = self._extract_metrics(execution_result)
        

        # Format intermediate results
        supporting_context = ""
        if execution_result.intermediate_results:
            supporting_context = "CONTEXT FROM SUPPORTING QUERIES:\n"
            for name, data in execution_result.intermediate_results.items():
                supporting_context += f"- {name}: {json.dumps(data[:3], default=str)}\n"

        # Format history
        history_str = ""
        if conversation_history:
            history_str = "PREVIOUS CONVERSATION (Use for comparison context):\n"
            for msg in conversation_history[-3:]: 
                history_str += f"- {msg['role'].upper()}: {msg['content']}\n"
        
        prompt = f"""You are an Expert Senior Business Analyst & Strategy Consultant (ex-McKinsey/Bain). 
Your goal is to provide executive-level insights that answer the user's business question directly, backed by data.

USER QUERY: "{query}"
INTENT: {intent.intent.value}

{history_str}

STATISTICAL FINDINGS (Use these to drive 'Why' and 'Implications'):
- Main Finding: {interpretation.main_finding}
- Outliers: {", ".join(interpretation.outliers)}
- Top Contributors: {", ".join(interpretation.top_contributors)}
- Trends: {", ".join(interpretation.trends) if interpretation.trends else "None detected"}

DATA RESULTS (first 10 rows):
{json.dumps(limited_data, indent=2, default=str)}

 {supporting_context}

COMPUTED METRICS:
{json.dumps(metrics_summary, indent=2, default=str)}

TOTAL ROWS: {execution_result.row_count}

CRITICAL RULES:
1. **Direct Answer First**: Start with a clear, direct answer to the user's question.
2. **Data-Driven**: NEVER invent numbers. ONLY use metrics from the provided data.
3. **Strategic Tone**: Use professional, executive terminology (e.g., "driven by", "accounting for", "represents", "year-over-year").
4. **Structure**: Output strictly in the requested JSON format.

OUTPUT FORMAT (JSON):
{{
    "direct_answer": "A concise (2-3 sentences) executive summary answering the question directly.",
    "what_data_shows": [
        "Key Finding 1 (e.g., 'Revenue peaked in Q3 at $1.2M')",
        "Key Finding 2 (e.g., 'Product A accounts for 45% of total volume')",
        "Key Finding 3"
    ],
    "why_it_happened": [
        "Potential driver 1 (infer from data patterns if possible, e.g., 'Seasonality appears to be a factor...')",
        "Potential driver 2 (e.g., 'High correlation between X and Y suggests...')"
    ],
    "business_implications": [
        "Strategic Recommendation 1 (e.g., 'Focus marketing efforts on Q3 to capitalize on seasonality')",
        "Strategic Recommendation 2 (e.g., 'Investigate underperformance in Region X')"
    ],
    "confidence": 0.0-1.0,
    "data_sufficiency": "sufficient|partial|insufficient"
}}

Respond with ONLY the JSON, no other text."""

        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={"temperature": 0.2, "num_predict": 2048}
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
            
            # Validate insights against execution results
            validation_passed, validation_warnings = self._validate_insights(
                result_data, 
                execution_result
            )
            
            if validation_warnings:
                logger.warning(f"⚠️ Insight validation warnings: {validation_warnings}")
            
            insights = Insights(
                direct_answer=result_data.get("direct_answer", "Analysis complete."),
                what_data_shows=result_data.get("what_data_shows", []),
                why_it_happened=result_data.get("why_it_happened", []),
                business_implications=result_data.get("business_implications", []),
                confidence=float(result_data.get("confidence", 0.7)),
                data_sufficiency=result_data.get("data_sufficiency", "sufficient")
            )
            
            logger.info(f"✅ Insights generated: {len(insights.what_data_shows)} facts, "
                       f"{len(insights.business_implications)} recommendations")
            
            return insights
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            # Fallback to basic insights
            return self._fallback_insights(query, execution_result)
    
    def _extract_metrics(self, execution_result: ExecutionResult) -> Dict[str, Any]:
        """Extract all metrics from execution result"""
        metrics = {}
        
        # Add explicit metrics
        if execution_result.metrics:
            metrics.update(execution_result.metrics)
        
        # Calculate basic metrics from data
        if execution_result.data:
            data = execution_result.data
            metrics["row_count"] = len(data)
            
            # For each numeric column, calculate basic stats
            if data:
                first_row = data[0]
                for col, value in first_row.items():
                    if isinstance(value, (int, float)):
                        values = [row.get(col, 0) for row in data if isinstance(row.get(col), (int, float))]
                        if values:
                            metrics[f"{col}_sum"] = sum(values)
                            metrics[f"{col}_avg"] = sum(values) / len(values)
                            metrics[f"{col}_min"] = min(values)
                            metrics[f"{col}_max"] = max(values)
        
        return metrics
    
    def _validate_insights(
        self, 
        insights_data: Dict[str, Any], 
        execution_result: ExecutionResult
    ) -> tuple:
        """
        Validate that insights don't contain hallucinated metrics
        
        Returns:
            (validation_passed, warnings)
        """
        warnings = []
        
        # Extract all text from insights
        all_text = insights_data.get("direct_answer", "")
        all_text += " ".join(insights_data.get("what_data_shows", []))
        all_text += " ".join(insights_data.get("why_it_happened", []))
        all_text += " ".join(insights_data.get("business_implications", []))
        
        # Extract all numbers from insights
        numbers_in_insights = re.findall(r'\b\d+(?:\.\d+)?%?\b', all_text)
        
        # Extract all numbers from execution results
        data_str = json.dumps(execution_result.data, default=str)
        metrics_str = json.dumps(execution_result.metrics, default=str)
        numbers_in_data = re.findall(r'\b\d+(?:\.\d+)?\b', data_str + metrics_str)
        
        # Check if insight numbers are grounded in data
        # This is a simple heuristic - not perfect but catches obvious hallucinations
        for num in numbers_in_insights:
            clean_num = num.replace('%', '')
            if clean_num not in numbers_in_data:
                # Check if it's a rounded version
                try:
                    num_val = float(clean_num)
                    # Check if any data number is close (within 10%)
                    found_close = False
                    for data_num in numbers_in_data:
                        try:
                            data_val = float(data_num)
                            if abs(num_val - data_val) / max(data_val, 1) < 0.1:
                                found_close = True
                                break
                        except:
                            pass
                    
                    if not found_close:
                        warnings.append(f"Number '{num}' in insights may not be from data")
                except:
                    pass
        
        validation_passed = len(warnings) == 0
        return validation_passed, warnings
    
    def _fallback_insights(
        self, 
        query: str, 
        execution_result: ExecutionResult
    ) -> Insights:
        """Generate simple fallback insights"""
        
        row_count = execution_result.row_count
        columns = execution_result.columns
        
        direct_answer = f"Found {row_count} results for your query."
        
        what_data_shows = [
            f"The query returned {row_count} rows",
            f"Data includes {len(columns)} columns: {', '.join(columns[:5])}"
        ]
        
        # Try to extract first numeric value
        if execution_result.data and execution_result.data[0]:
            first_row = execution_result.data[0]
            for col, value in first_row.items():
                if isinstance(value, (int, float)):
                    what_data_shows.append(f"{col}: {value}")
                    break
        
        why_it_happened = [
            "Analysis based on available data in the dataset"
        ]
        
        business_implications = [
            "Review the detailed results for further insights",
            "Consider additional filters or groupings for deeper analysis"
        ]
        
        logger.info(f"⚠️ Using fallback insights")
        
        return Insights(
            direct_answer=direct_answer,
            what_data_shows=what_data_shows,
            why_it_happened=why_it_happened,
            business_implications=business_implications,
            confidence=0.5,
            data_sufficiency="partial"
        )


# Singleton instance
insight_generator = InsightGeneratorAgent()
