"""
Insights Generator Service - Structured Business Insights

This service generates structured, executive-level business insights from query results.
Instead of plain text, it returns a rich JSON structure with:
- Direct answer to the user's question
- Key findings with specific metrics
- Root cause analysis
- Business implications and recommendations
- Confidence score
"""

import json
import logging
from typing import Dict, Any, List, Optional
from ..services.ollama_service import ollama_service

logger = logging.getLogger(__name__)


STRUCTURED_INSIGHTS_PROMPT = """You are a professional business analyst providing executive-level insights.

Analyze the query results and provide structured insights in the following JSON format:

{
    "direct_answer": "A clear, concise answer to the user's question (1-2 sentences max)",
    "what_data_shows": [
        "Key finding 1 with specific numbers",
        "Key finding 2 with specific numbers",
        "Key finding 3 with specific numbers"
    ],
    "why_it_happened": [
        "Root cause or context 1",
        "Root cause or context 2"
    ],
    "business_implications": [
        "Strategic recommendation 1",
        "Strategic recommendation 2",
        "Strategic recommendation 3"
    ],
    "confidence": 0.95
}

**Guidelines:**
1. **direct_answer**: Answer the exact question asked. Be specific and quantitative.
   - Good: "Total revenue is $1.2M across 5 products"
   - Bad: "The data shows various revenue amounts"

2. **what_data_shows**: List 2-5 key findings with actual numbers from the data
   - Include percentages, comparisons, trends
   - Be specific: "Product A generated $450K (37.5% of total)"
   - Highlight outliers, top performers, notable patterns

3. **why_it_happened**: Provide 1-3 contextual explanations or hypotheses
   - Consider seasonality, market trends, business events
   - Be analytical but acknowledge when speculating
   - Example: "Q4 spike likely due to holiday shopping season"

4. **business_implications**: Give 2-4 actionable recommendations
   - Focus on strategic actions, not just observations
   - Be specific: "Increase inventory for Product A by 25%"
   - Prioritize high-impact suggestions

5. **confidence**: Your confidence in this analysis (0.0 to 1.0)
   - 0.9-1.0: High confidence, clear data, strong patterns
   - 0.7-0.9: Good confidence, some assumptions made
   - 0.5-0.7: Moderate confidence, limited data or unclear patterns
   - Below 0.5: Low confidence, insufficient data

**Important:**
- Return ONLY valid JSON, no markdown formatting
- Use actual numbers from the data
- Be concise but insightful
- If data is insufficient for a section, use empty arrays []
"""


class InsightsGeneratorService:
    """Service for generating structured business insights"""
    
    def should_generate_insights(self, user_question: str) -> bool:
        """
        Determine if the user is asking for insights, analysis, or recommendations.
        
        Args:
            user_question: The user's natural language question
            
        Returns:
            True if insights should be generated, False otherwise
        """
        question_lower = user_question.lower()
        
        # Keywords that indicate user wants insights/analysis
        insight_keywords = [
            'insight', 'insights', 'analyze', 'analysis', 'recommend', 'recommendation',
            'suggestions', 'suggest', 'why', 'explain', 'implication', 'implications',
            'what does this mean', 'what should', 'advice', 'strategy', 'strategic',
            'business impact', 'actionable', 'next steps', 'what to do',
            'interpret', 'interpretation', 'conclusion', 'conclusions'
        ]
        
        # Check if any insight keyword is in the question
        return any(keyword in question_lower for keyword in insight_keywords)
    
    async def generate_structured_insights(
        self,
        data: List[Dict[str, Any]],
        user_question: str,
        intent: str = "DESCRIPTIVE",
        sql_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured insights from query results.
        
        Args:
            data: Query result data
            user_question: Original user question
            intent: Query intent (DESCRIPTIVE, TREND, COMPARATIVE, etc.)
            sql_query: The SQL query that was executed
            
        Returns:
            Structured insights dictionary with all categories
        """
        try:
            if not data or len(data) == 0:
                return self._empty_insights("No data available to analyze")
            
            # Prepare data summary
            data_summary = self._create_data_summary(data)
            
            # Build the prompt
            user_prompt = f"""**User Question:** {user_question}

**Query Intent:** {intent}

**Data Summary:**
- Total rows: {len(data)}
- Columns: {', '.join(data[0].keys())}
{data_summary}

**Sample Data (first 10 rows):**
{json.dumps(data[:10], default=str, indent=2)}

Analyze this data and provide structured insights in the JSON format specified in the system prompt.
"""
            
            # Generate insights using LLM
            response = await ollama_service.generate(
                system_prompt=STRUCTURED_INSIGHTS_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse JSON response
            try:
                insights = json.loads(response)
                
                # Validate structure
                if not self._validate_insights_structure(insights):
                    logger.warning("Invalid insights structure, using fallback")
                    return self._fallback_insights(data, user_question)
                
                # Ensure confidence is in valid range
                insights['confidence'] = max(0.0, min(1.0, insights.get('confidence', 0.7)))
                
                logger.info(f"Generated structured insights with confidence {insights['confidence']}")
                return insights
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse insights JSON: {e}")
                logger.debug(f"Raw response: {response[:500]}")
                return self._fallback_insights(data, user_question)
            
        except Exception as e:
            logger.error(f"Error generating structured insights: {str(e)}", exc_info=True)
            return self._empty_insights(f"Error: {str(e)}")
    
    def _create_data_summary(self, data: List[Dict[str, Any]]) -> str:
        """Create a statistical summary of the data"""
        if not data:
            return "No data"
        
        summary_parts = []
        
        # Analyze each column
        for col in data[0].keys():
            values = [row[col] for row in data if row.get(col) is not None]
            
            if not values:
                continue
            
            # Numeric columns
            if isinstance(values[0], (int, float)):
                try:
                    min_val = min(values)
                    max_val = max(values)
                    avg_val = sum(values) / len(values)
                    summary_parts.append(
                        f"- {col}: min={min_val:,.2f}, max={max_val:,.2f}, avg={avg_val:,.2f}"
                    )
                except:
                    pass
            
            # Categorical columns
            else:
                unique_count = len(set(str(v) for v in values))
                summary_parts.append(f"- {col}: {unique_count} unique values")
        
        return "\n".join(summary_parts)
    
    def _validate_insights_structure(self, insights: Dict[str, Any]) -> bool:
        """Validate that insights have the required structure"""
        required_keys = ['direct_answer', 'what_data_shows', 'why_it_happened', 
                        'business_implications', 'confidence']
        
        if not all(key in insights for key in required_keys):
            return False
        
        # Check types
        if not isinstance(insights['direct_answer'], str):
            return False
        if not isinstance(insights['what_data_shows'], list):
            return False
        if not isinstance(insights['why_it_happened'], list):
            return False
        if not isinstance(insights['business_implications'], list):
            return False
        if not isinstance(insights['confidence'], (int, float)):
            return False
        
        return True
    
    def _fallback_insights(self, data: List[Dict[str, Any]], question: str) -> Dict[str, Any]:
        """Generate basic fallback insights when LLM fails"""
        row_count = len(data)
        columns = list(data[0].keys()) if data else []
        
        # Try to extract a simple answer
        direct_answer = f"Found {row_count} results"
        
        # Basic findings
        findings = [f"Query returned {row_count} rows with {len(columns)} columns"]
        
        # Check for numeric columns
        for col in columns[:3]:  # First 3 columns
            values = [row[col] for row in data if isinstance(row.get(col), (int, float))]
            if values:
                findings.append(f"{col}: ranges from {min(values):,.2f} to {max(values):,.2f}")
        
        return {
            "direct_answer": direct_answer,
            "what_data_shows": findings,
            "why_it_happened": [],
            "business_implications": ["Review the data for actionable patterns"],
            "confidence": 0.5
        }
    
    
    def generate_simple_answer(self, data: List[Dict[str, Any]], user_question: str) -> str:
        """
        Generate a simple, direct answer without detailed insights.
        Used when user just wants data, not analysis.
        
        Args:
            data: Query result data
            user_question: Original user question
            
        Returns:
            Simple string answer
        """
        if not data or len(data) == 0:
            return "No results found."
        
        row_count = len(data)
        
        # For single value results (like "what is total revenue?")
        if row_count == 1 and len(data[0]) == 1:
            value = list(data[0].values())[0]
            if isinstance(value, (int, float)):
                return f"{value:,.2f}"
            return str(value)
        
        # For simple counts
        if row_count == 1:
            return f"Found {row_count} result"
        
        # For lists
        return f"Found {row_count} results"
    
    def _empty_insights(self, reason: str) -> Dict[str, Any]:
        """Return empty insights structure"""
        return {
            "direct_answer": reason,
            "what_data_shows": [],
            "why_it_happened": [],
            "business_implications": [],
            "confidence": 0.0
        }


# Global instance
insights_generator_service = InsightsGeneratorService()
