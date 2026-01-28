"""
Response Structure Enforcer

Ensures all responses follow Enterprise-style executive format:
1. Executive Answer
2. Key Findings
3. Supporting Data
4. Visualizations
5. Explanation (what/why/meaning)
6. Business Implications
7. Recommendations
8. Assumptions & Limitations
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ResponseStructureEnforcer:
    """Enforces strict Enterprise-style response structure."""
    
    @staticmethod
    def enforce_structure(
        question: str,
        sql_query: str,
        results: List[Dict[str, Any]],
        insights: Dict[str, Any],
        visualizations: List[Dict[str, Any]],
        data_quality: Optional[Dict[str, Any]] = None,
        exploratory_steps: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Enforce strict response structure.
        
        Returns Enterprise-formatted response with all required sections.
        """
        try:
            # Build structured response
            structured_response = {
                # 1. Executive Answer (1-2 sentences)
                "executive_answer": ResponseStructureEnforcer._extract_executive_answer(insights),
                
                # 2. Key Findings (3-5 bullets with numbers)
                "key_findings": ResponseStructureEnforcer._extract_key_findings(insights, results),
                
                # 3. Supporting Data
                "supporting_data": {
                    "table": results[:100],  # Limit to 100 rows
                    "row_count": len(results),
                    "sql_query": sql_query
                },
                
                # 4. Visualizations
                "visualizations": visualizations,
                
                # 5. Explanation (what/why/meaning)
                "explanation": {
                    "what_happened": ResponseStructureEnforcer._extract_what(insights, results),
                    "why_it_happened": ResponseStructureEnforcer._extract_why(insights),
                    "business_meaning": ResponseStructureEnforcer._extract_meaning(insights)
                },
                
                # 6. Business Implications
                "business_implications": ResponseStructureEnforcer._extract_implications(insights),
                
                # 7. Recommendations
                "recommendations": ResponseStructureEnforcer._extract_recommendations(insights),
                
                # 8. Assumptions & Limitations
                "assumptions": ResponseStructureEnforcer._extract_assumptions(question, sql_query),
                "limitations": ResponseStructureEnforcer._extract_limitations(data_quality, results),
                
                # Metadata
                "confidence": insights.get('confidence', 0.85),
                "data_quality_score": data_quality.get('quality_score', 100) if data_quality else 100,
                
                # Reasoning process (thoughts)
                "reasoning_process": exploratory_steps or []
            }
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Error enforcing response structure: {str(e)}")
            # Return minimal structure on error
            return {
                "executive_answer": "Analysis completed successfully.",
                "key_findings": ["Data retrieved and processed."],
                "supporting_data": {"table": results, "row_count": len(results)},
                "error": str(e)
            }
    
    @staticmethod
    def _extract_executive_answer(insights: Dict[str, Any]) -> str:
        """Extract 1-2 sentence executive summary."""
        return insights.get('summary', insights.get('direct_answer', 'Analysis completed successfully.'))
    
    @staticmethod
    def _extract_key_findings(insights: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
        """Extract 3-5 key findings with specific numbers."""
        findings = insights.get('insights', insights.get('key_findings', insights.get('what_data_shows', [])))
        
        if not findings:
            # Generate basic finding from results
            if results:
                return [f"Retrieved {len(results)} rows of data"]
            return ["Data analysis completed"]
        
        # Ensure we have 3-5 findings
        if isinstance(findings, list):
            return findings[:5]  # Max 5
        return [str(findings)]
    
    @staticmethod
    def _extract_what(insights: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
        """Extract what the data shows."""
        what = insights.get('what_data_shows', insights.get('detailed_analysis', ''))
        
        if isinstance(what, list):
            return '. '.join(what)
        
        if not what and results:
            return f"The data contains {len(results)} rows showing the requested information."
        
        return str(what) if what else "Data retrieved successfully."
    
    @staticmethod
    def _extract_why(insights: Dict[str, Any]) -> str:
        """Extract why it happened."""
        why = insights.get('why_it_happened', insights.get('why_it_happens', ''))
        
        if isinstance(why, list):
            return '. '.join(why)
        
        return str(why) if why else "Analysis based on available data patterns."
    
    @staticmethod
    def _extract_meaning(insights: Dict[str, Any]) -> str:
        """Extract business meaning."""
        meaning = insights.get('business_meaning', insights.get('business_implications', ''))
        
        if isinstance(meaning, list):
            return '. '.join(meaning[:3])  # Max 3
        
        return str(meaning) if meaning else "Results provide insights for data-driven decision making."
    
    @staticmethod
    def _extract_implications(insights: Dict[str, Any]) -> List[str]:
        """Extract business implications."""
        implications = insights.get('business_implications', insights.get('implications', []))
        
        if isinstance(implications, str):
            return [implications]
        
        if isinstance(implications, list):
            return implications[:3]  # Max 3
        
        return ["Consider these findings in strategic planning"]
    
    @staticmethod
    def _extract_recommendations(insights: Dict[str, Any]) -> List[str]:
        """Extract actionable recommendations."""
        recs = insights.get('recommendations', insights.get('next_steps', []))
        
        if isinstance(recs, str):
            return [recs]
        
        if isinstance(recs, list):
            return recs[:3]  # Max 3
        
        return ["Review findings and determine next steps"]
    
    @staticmethod
    def _extract_assumptions(question: str, sql_query: str) -> List[str]:
        """Extract assumptions made."""
        assumptions = []
        
        # Check for common assumptions
        if "LIMIT" in sql_query.upper():
            assumptions.append("Results are limited to prevent overwhelming output")
        
        if "WHERE" not in sql_query.upper() and "GROUP BY" not in sql_query.upper():
            assumptions.append("All available data is included without filtering")
        
        if not assumptions:
            assumptions.append("Data is assumed to be accurate and up-to-date")
        
        return assumptions
    
    @staticmethod
    def _extract_limitations(data_quality: Optional[Dict[str, Any]], results: List[Dict[str, Any]]) -> List[str]:
        """Extract limitations."""
        limitations = []
        
        # Data quality limitations
        if data_quality:
            if data_quality.get('quality_score', 100) < 80:
                limitations.append(f"Data quality score is {data_quality['quality_score']}/100")
            
            if data_quality.get('warnings'):
                limitations.append("Data quality warnings present (see details)")
        
        # Result size limitations
        if len(results) == 0:
            limitations.append("No data matched the query criteria")
        elif len(results) < 10:
            limitations.append(f"Small dataset ({len(results)} rows) may limit statistical significance")
        
        if not limitations:
            limitations.append("Analysis based on available data snapshot")
        
        return limitations


# Singleton instance
response_structure_enforcer = ResponseStructureEnforcer()
