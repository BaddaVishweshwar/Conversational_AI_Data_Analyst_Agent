from typing import Dict, Any, Optional
from .gemini_service import gemini_service
from .ollama_service import ollama_service
import logging

logger = logging.getLogger(__name__)

class AIService:
    """Unified AI service with Gemini -> Ollama fallback logic"""
    
    def generate_analysis_plan(
        self, 
        natural_query: str, 
        schema: Dict[str, Any],
        sample_data: list,
        related_expertise: list = []
    ) -> Dict[str, Any]:
        """Try Gemini first, then Ollama if Gemini fails"""
        # Try Gemini
        result = gemini_service.generate_analysis_plan(natural_query, schema, sample_data, related_expertise)
        if result.get("success"):
            logger.info("✅ Gemini generated analysis plan")
            return result
        
        # Fallback to Ollama
        logger.warning(f"⚠️ Gemini failed: {result.get('error')}. Falling back to Ollama.")
        return ollama_service.generate_analysis_plan(natural_query, schema, sample_data, related_expertise)

    def generate_eda_report(
        self,
        schema: Dict[str, Any],
        sample_data: list
    ) -> Dict[str, Any]:
        """Try Gemini first, then Ollama if Gemini fails"""
        # Try Gemini
        result = gemini_service.generate_eda_report(schema, sample_data)
        if result.get("success"):
            logger.info("✅ Gemini generated EDA report")
            return result
        
        # Fallback to Ollama
        logger.warning(f"⚠️ Gemini EDA failed: {result.get('error')}. Falling back to Ollama.")
        return ollama_service.generate_eda_report(schema, sample_data)

    def generate_insights(
        self,
        query: str,
        result_data: list,
        chart_type: Optional[str] = None
    ) -> str:
        """Try Gemini first, then Ollama if Gemini fails"""
        # Try Gemini
        insights = gemini_service.generate_insights(query, result_data, chart_type)
        if "Unable to generate insights" not in insights:
            logger.info("✅ Gemini generated insights")
            return insights
        
        # Fallback to Ollama
        logger.warning("⚠️ Gemini insights failed. Falling back to Ollama.")
        return ollama_service.generate_insights(query, result_data, chart_type)

ai_service = AIService()
