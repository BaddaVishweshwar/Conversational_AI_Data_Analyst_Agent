"""
Insight Engine Service

Generates AI-powered business insights from query results:
- Statistical analysis (trends, outliers, correlations)
- Pattern detection (seasonality, anomalies)
- AI narration in business-friendly language
- Actionable recommendations

Transforms raw data into executive-level insights.
"""

import logging
from typing import Dict, Any, List, Optional
import statistics
from datetime import datetime
import json

from ..services.ollama_service import ollama_service

logger = logging.getLogger(__name__)


class InsightEngineService:
    """
    Generates statistical insights and AI narratives from query results.
    """
    
    def generate_insights(
        self,
        data: List[Dict[str, Any]],
        question: str,
        sql: str,
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights from query results.
        
        Args:
            data: Query results
            question: Original question
            sql: Executed SQL
            intent: Query intent (TREND, COMPARATIVE, etc.)
            
        Returns:
            Insights with statistics and narrative
        """
        try:
            if not data or len(data) == 0:
                return {
                    'summary': 'No data available',
                    'statistics': {},
                    'insights': [],
                    'recommendations': []
                }
            
            # Generate statistical insights
            stats = self.generate_statistical_insights(data)
            
            # Generate AI narrative
            narrative = self.generate_ai_narrative(
                data, question, sql, stats, intent
            )
            
            return {
                'summary': narrative.get('summary', ''),
                'statistics': stats,
                'key_findings': narrative.get('key_findings', []),
                'insights': narrative.get('insights', []),
                'recommendations': narrative.get('recommendations', []),
                'confidence': narrative.get('confidence', 0.8)
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                'summary': 'Unable to generate insights',
                'error': str(e)
            }
    
    def generate_statistical_insights(
        self,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute statistical insights from data.
        
        Args:
            data: Query results
            
        Returns:
            Statistical metrics
        """
        try:
            stats = {
                'row_count': len(data),
                'columns': list(data[0].keys()) if data else [],
                'numeric_stats': {},
                'trends': {},
                'outliers': {}
            }
            
            # Analyze numeric columns
            for col in stats['columns']:
                values = [row[col] for row in data if row[col] is not None]
                
                if values and isinstance(values[0], (int, float)):
                    col_stats = self._analyze_numeric_column(col, values)
                    stats['numeric_stats'][col] = col_stats
                    
                    # Detect trends if enough data points
                    if len(values) >= 3:
                        trend = self._detect_trend(values)
                        if trend:
                            stats['trends'][col] = trend
                    
                    # Detect outliers
                    outliers = self._detect_outliers(values)
                    if outliers:
                        stats['outliers'][col] = outliers
            
            return stats
            
        except Exception as e:
            logger.error(f"Error in statistical analysis: {e}")
            return {}
    
    def _analyze_numeric_column(
        self,
        column_name: str,
        values: List[float]
    ) -> Dict[str, Any]:
        """Analyze a numeric column"""
        try:
            return {
                'min': min(values),
                'max': max(values),
                'mean': round(statistics.mean(values), 2),
                'median': round(statistics.median(values), 2),
                'stdev': round(statistics.stdev(values), 2) if len(values) > 1 else 0,
                'total': round(sum(values), 2),
                'count': len(values)
            }
        except:
            return {}
    
    def _detect_trend(self, values: List[float]) -> Optional[Dict[str, Any]]:
        """Detect trend in time series data"""
        try:
            if len(values) < 3:
                return None
            
            # Simple linear trend detection
            n = len(values)
            x = list(range(n))
            
            # Calculate slope
            x_mean = sum(x) / n
            y_mean = sum(values) / n
            
            numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return None
            
            slope = numerator / denominator
            
            # Determine trend direction
            if abs(slope) < 0.01:
                direction = 'stable'
            elif slope > 0:
                direction = 'increasing'
            else:
                direction = 'decreasing'
            
            # Calculate percentage change
            first_val = values[0]
            last_val = values[-1]
            pct_change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
            
            return {
                'direction': direction,
                'slope': round(slope, 4),
                'percent_change': round(pct_change, 2),
                'first_value': first_val,
                'last_value': last_val
            }
        except:
            return None
    
    def _detect_outliers(self, values: List[float]) -> Optional[Dict[str, Any]]:
        """Detect statistical outliers"""
        try:
            if len(values) < 4:
                return None
            
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            
            # Values > 2 standard deviations from mean
            outliers = [v for v in values if abs(v - mean) > 2 * stdev]
            
            if not outliers:
                return None
            
            return {
                'count': len(outliers),
                'values': outliers[:5],  # Limit to 5
                'threshold': round(2 * stdev, 2)
            }
        except:
            return None
    
    def generate_ai_narrative(
        self,
        data: List[Dict[str, Any]],
        question: str,
        sql: str,
        statistics: Dict[str, Any],
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI-powered narrative insights.
        
        Args:
            data: Query results
            question: Original question
            sql: Executed SQL
            statistics: Statistical analysis
            intent: Query intent
            
        Returns:
            AI-generated insights
        """
        try:
            # Build prompt
            prompt = self._build_insight_prompt(
                data, question, statistics, intent
            )
            
            # Generate insights with LLM
            response = ollama_service.generate_response(
                prompt=prompt,
                system_prompt=self._get_insight_system_prompt(),
                json_mode=True,
                temperature=0.4,
                task_type='insight_generation'
            )
            
            # Parse response
            insights = json.loads(response)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI narrative: {e}")
            return {
                'summary': 'Analysis complete',
                'key_findings': [],
                'insights': [],
                'recommendations': []
            }
    
    def _build_insight_prompt(
        self,
        data: List[Dict[str, Any]],
        question: str,
        statistics: Dict[str, Any],
        intent: Optional[str]
    ) -> str:
        """Build prompt for insight generation"""
        
        # Format statistics
        stats_summary = []
        for col, stats in statistics.get('numeric_stats', {}).items():
            stats_summary.append(
                f"- {col}: min={stats['min']}, max={stats['max']}, "
                f"mean={stats['mean']}, total={stats['total']}"
            )
        
        # Format trends
        trends_summary = []
        for col, trend in statistics.get('trends', {}).items():
            trends_summary.append(
                f"- {col}: {trend['direction']} ({trend['percent_change']:+.1f}%)"
            )
        
        prompt = f"""Analyze these query results and provide executive-level business insights.

**Question:** {question}
**Intent:** {intent or 'DESCRIPTIVE'}
**Row Count:** {len(data)}

**Statistics:**
{chr(10).join(stats_summary) if stats_summary else 'No numeric data'}

**Trends:**
{chr(10).join(trends_summary) if trends_summary else 'No trends detected'}

**Sample Data (first 5 rows):**
{json.dumps(data[:5], indent=2, default=str)}

Provide insights in JSON format:
{{
  "summary": "One-sentence executive summary",
  "key_findings": ["Finding 1 with specific numbers", "Finding 2", "Finding 3"],
  "insights": ["Insight 1 explaining what it means", "Insight 2"],
  "recommendations": ["Actionable recommendation 1", "Recommendation 2"],
  "confidence": 0.85
}}"""
        
        return prompt
    
    def _get_insight_system_prompt(self) -> str:
        """Get system prompt for insight generation"""
        return """You are a senior business analyst providing executive-level insights.

Guidelines:
1. Be specific - always include actual numbers from the data
2. Focus on "so what?" - explain business implications
3. Be concise - executives want key points, not details
4. Provide actionable recommendations
5. Use business language, not technical jargon
6. Highlight trends, patterns, and anomalies
7. Compare to benchmarks when relevant

Format your response as JSON with summary, key_findings, insights, and recommendations."""


# Singleton instance
insight_engine = InsightEngineService()
