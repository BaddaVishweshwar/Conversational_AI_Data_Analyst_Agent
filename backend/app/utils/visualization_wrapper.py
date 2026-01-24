"""
Visualization Wrapper for V4 Pipeline

This module adds chart generation to V4 query results.
It wraps the existing V4 pipeline and generates visualizations
using the visualization_service.
"""

import logging
from typing import Dict, Any
from ..services.visualization_service import visualization_service

logger = logging.getLogger(__name__)


def add_visualization_to_response(
    response: Dict[str, Any],
    user_question: str
) -> Dict[str, Any]:
    """
    Add visualization to V4 response.
    
    Args:
        response: V4 analytics response
        user_question: Original user question
        
    Returns:
        Enhanced response with visualization image
    """
    try:
        logger.info("=== VISUALIZATION WRAPPER CALLED ===")
        
        # Check if we have data to visualize
        data = response.get('data', [])
        logger.info(f"Data rows: {len(data)}")
        
        if not data or len(data) == 0:
            logger.warning("No data to visualize")
            return response
        
        # Get intent and visualization config
        intent = response.get('intent', 'DESCRIPTIVE')
        viz_config = response.get('visualization', {})
        
        # If visualization is None, create a default one
        if viz_config is None:
            viz_config = {}
            logger.info("Visualization config was None, creating default")
        
        chart_type = viz_config.get('chart_type', 'bar')
        logger.info(f"Chart type: {chart_type}, Intent: {intent}")
        
        # Don't generate chart for table type
        if chart_type == 'table':
            logger.info("Chart type is table, skipping visualization")
            return response
        
        logger.info(f"Generating {chart_type} visualization for query")
        
        # Generate chart
        viz_result = visualization_service.generate_chart(
            data=data,
            columns=list(data[0].keys()),
            chart_type=chart_type,
            title=user_question
        )
        
        logger.info(f"Visualization result: success={viz_result['success']}")
        
        if viz_result['success']:
            # Add chart image to response
            response['python_chart'] = viz_result['image']
            if response.get('visualization') is None:
                response['visualization'] = {}
            response['visualization']['image'] = viz_result['image']
            response['visualization']['chart_type'] = chart_type
            logger.info(f"✅ Added {chart_type} visualization to response (length: {len(viz_result['image'])})")
        else:
            logger.warning(f"Visualization failed: {viz_result.get('error')}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error adding visualization: {e}", exc_info=True)
        return response
