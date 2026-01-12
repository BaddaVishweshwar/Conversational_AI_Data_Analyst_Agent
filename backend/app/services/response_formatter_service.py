"""
Response Formatter Service

Formats analysis results into CamelAI-style structured responses with
understanding, approach, exploratory steps, SQL, visualizations, and insights.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ResponseFormatterService:
    """Service to format final analysis response in CamelAI structure."""
    
    @staticmethod
    def format_final_response(
        query: str,
        understanding: str,
        approach: str,
        exploratory_results: List[Dict[str, Any]],
        main_sql: str,
        sql_explanation: str,
        query_results: Dict[str, Any],
        visualizations: List[Dict[str, Any]],
        insights: Dict[str, Any],
        python_charts: List[Dict[str, Any]] = None,
        intent: Optional[Dict[str, Any]] = None,
        schema_analysis: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Format complete analysis response.
        
        Args:
            query: Original user question
            understanding: What the user is asking for
            approach: How the analysis will be conducted
            exploratory_results: Results from exploratory queries
            main_sql: Main SQL query
            sql_explanation: Explanation of the SQL
            query_results: Results from main query
            visualizations: List of visualization configs
            insights: Insights dictionary with summary, findings, analysis, recommendations
            python_charts: List of generated chart images
            intent: Intent classification result (optional)
            schema_analysis: Schema analysis result (optional)
            execution_time_ms: Total execution time (optional)
            
        Returns:
            Formatted response dictionary
        """
        try:
            # Merge python_charts into visualizations
            merged_visualizations = []
            for i, viz in enumerate(visualizations):
                merged_viz = viz.copy()
                # If we have a corresponding python chart with base64 image, add it
                if python_charts and i < len(python_charts):
                    python_chart = python_charts[i]
                    if python_chart.get('image'):
                        # Extract base64 from data:image/png;base64,xxx format
                        image_data = python_chart.get('image', '')
                        if image_data.startswith('data:image/png;base64,'):
                            merged_viz['image_base64'] = image_data.split(',')[1]
                        else:
                            merged_viz['image_base64'] = image_data
                merged_visualizations.append(merged_viz)
            
            response = {
                # User question
                'query': query,
                
                # Understanding and approach
                'understanding': understanding,
                'approach': approach,
                
                # Intent classification (if available)
                'intent': ResponseFormatterService._format_intent(intent) if intent else None,
                
                # Exploratory analysis
                'exploratory_steps': ResponseFormatterService._format_exploratory_steps(exploratory_results),
                
                # Main SQL query
                'sql_query': {
                    'query': main_sql,
                    'explanation': sql_explanation,
                    'formatted': ResponseFormatterService._format_sql(main_sql)
                },
                
                # Query results
                'results': {
                    'data': query_results.get('data', []),
                    'columns': query_results.get('columns', []),
                    'row_count': query_results.get('row_count', 0),
                    'execution_time_ms': query_results.get('execution_time_ms', 0)
                },
                
                # Visualizations (merged with base64 images)
                'visualizations': merged_visualizations,
                'python_charts': python_charts or [],
                'primary_visualization': 0 if merged_visualizations else None,
                
                # Insights and analysis
                'insights': {
                    'summary': insights.get('summary', ''),
                    'key_findings': insights.get('key_findings', []),
                    'detailed_analysis': insights.get('detailed_analysis', ''),
                    'recommendations': insights.get('recommendations', None)
                },
                
                # Metadata
                'metadata': {
                    'total_execution_time_ms': execution_time_ms,
                    'exploratory_queries_count': len(exploratory_results),
                    'visualizations_count': len(merged_visualizations),
                    'schema_columns': len(schema_analysis.get('columns', [])) if schema_analysis else 0
                },
                
                # Success flag
                'success': True
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return ResponseFormatterService._format_error_response(query, str(e))
    
    @staticmethod
    def _format_intent(intent: Dict[str, Any]) -> Dict[str, Any]:
        """Format intent classification result."""
        return {
            'primary_intent': intent.get('primary_intent', 'unknown'),
            'confidence': intent.get('confidence', 0.0),
            'requires_aggregation': intent.get('requires_aggregation', False),
            'requires_time_series': intent.get('requires_time_series', False),
            'requires_comparison': intent.get('requires_comparison', False)
        }
    
    @staticmethod
    def _format_exploratory_steps(exploratory_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format exploratory query results."""
        formatted_steps = []
        
        for result in exploratory_results:
            step = {
                'question': result.get('sub_question', 'N/A'),
                'sql': result.get('sql', ''),
                'finding': result.get('finding', ''),
                'data_preview': result.get('data', [])[:5] if result.get('data') else []
            }
            formatted_steps.append(step)
        
        return formatted_steps
    
    @staticmethod
    def _format_sql(sql: str) -> str:
        """Format SQL for better readability."""
        try:
            # Basic SQL formatting (can be enhanced with sqlparse library)
            formatted = sql.strip()
            
            # Add newlines after major keywords
            keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'WITH']
            for keyword in keywords:
                formatted = formatted.replace(f' {keyword} ', f'\n{keyword} ')
            
            return formatted
        except Exception as e:
            logger.error(f"Error formatting SQL: {str(e)}")
            return sql
    
    @staticmethod
    def _format_error_response(query: str, error: str) -> Dict[str, Any]:
        """Format error response."""
        return {
            'query': query,
            'success': False,
            'error': {
                'message': 'An error occurred while processing your query',
                'details': error,
                'suggestions': [
                    'Try rephrasing your question',
                    'Check if column names are correct',
                    'Ensure your data contains the requested information'
                ]
            }
        }
    
    @staticmethod
    def format_streaming_update(
        stage: str,
        status: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format streaming update for progressive result display.
        
        Args:
            stage: Current stage (planning, exploration, execution, insights, visualization)
            status: Status message (in_progress, completed, failed)
            data: Optional data for this stage
            
        Returns:
            Streaming update dictionary
        """
        return {
            'type': 'streaming_update',
            'stage': stage,
            'status': status,
            'data': data,
            'timestamp': None  # Can add timestamp if needed
        }
    
    @staticmethod
    def format_exploratory_finding(
        sub_question: str,
        sql: str,
        result_data: List[Dict[str, Any]],
        finding_summary: str
    ) -> Dict[str, Any]:
        """Format a single exploratory query finding."""
        return {
            'sub_question': sub_question,
            'sql': sql,
            'data': result_data[:10],  # Limit to 10 rows
            'row_count': len(result_data),
            'finding': finding_summary
        }
    
    @staticmethod
    def format_visualization_config(
        chart_type: str,
        config: Dict[str, Any],
        purpose: str = ""
    ) -> Dict[str, Any]:
        """Format visualization configuration."""
        return {
            'type': chart_type,
            'config': {
                'x_axis': config.get('x_axis'),
                'y_axis': config.get('y_axis'),
                'title': config.get('title', ''),
                'x_label': config.get('x_label', ''),
                'y_label': config.get('y_label', ''),
                'color_scheme': config.get('color_scheme', 'blue'),
                'sort': config.get('sort', 'none'),
                'limit': config.get('limit', None)
            },
            'purpose': purpose
        }
    
    @staticmethod
    def format_insights_structure(
        summary: str,
        key_findings: List[str],
        detailed_analysis: str,
        recommendations: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format insights in structured format."""
        return {
            'summary': summary,
            'key_findings': key_findings,
            'detailed_analysis': detailed_analysis,
            'recommendations': recommendations
        }


# Singleton instance
response_formatter_service = ResponseFormatterService()
