"""
Visualization Selector Agent

Intelligent chart type selection based on intent and data characteristics.
"""
import logging
from typing import Dict, Any, List
from . import VizConfig, ChartType, IntentType, IntentResult, ExecutionResult

logger = logging.getLogger(__name__)


class VisualizationSelectorAgent:
    """
    Maps intent + data type → chart type with validation rules.
    
    Mapping rules:
    - TREND + datetime column → Line chart
    - COMPARATIVE + 2-5 categories → Bar chart
    - DESCRIPTIVE + single metric → KPI card
    - Distribution analysis → Histogram
    - Correlation → Scatter plot
    
    Validation:
    - Reject pie charts for >7 categories
    - Reject line charts without time dimension
    - Reject scatter plots with <10 points
    """
    
    @staticmethod
    def select(
        intent: IntentResult,
        execution_result: ExecutionResult,
        query: str
    ) -> VizConfig:
        """
        Select appropriate visualization
        
        Args:
            intent: Query intent
            execution_result: Execution results with data
            query: Original query for context
            
        Returns:
            VizConfig with chart type and configuration
        """
        
        if not execution_result.success or not execution_result.data:
            logger.warning("No data available for visualization")
            return VizConfig(
                chart_type=ChartType.TABLE,
                title=query,
                validation_passed=True
            )
        
        data = execution_result.data
        columns = execution_result.columns
        row_count = len(data)
        
        # Analyze data structure
        numeric_cols = []
        categorical_cols = []
        datetime_cols = []
        
        if data:
            first_row = data[0]
            for col in columns:
                value = first_row.get(col)
                if isinstance(value, (int, float)):
                    numeric_cols.append(col)
                elif isinstance(value, str):
                    # Check if datetime-like
                    if any(word in col.lower() for word in ['date', 'time', 'year', 'month']):
                        datetime_cols.append(col)
                    else:
                        categorical_cols.append(col)
        
        # Select chart type based on intent and data
        chart_type, rejection_reason = VisualizationSelectorAgent._select_chart_type(
            intent=intent.intent,
            numeric_cols=numeric_cols,
            categorical_cols=categorical_cols,
            datetime_cols=datetime_cols,
            row_count=row_count,
            query=query
        )
        
        # Determine axes
        x_axis, y_axis = VisualizationSelectorAgent._determine_axes(
            chart_type=chart_type,
            columns=columns,
            numeric_cols=numeric_cols,
            categorical_cols=categorical_cols,
            datetime_cols=datetime_cols
        )
        
        viz_config = VizConfig(
            chart_type=chart_type,
            x_axis=x_axis,
            y_axis=y_axis,
            title=query[:100],  # Truncate long queries
            validation_passed=(rejection_reason is None),
            rejection_reason=rejection_reason
        )
        
        logger.info(f"✅ Visualization selected: {chart_type.value} "
                   f"(x={x_axis}, y={y_axis})")
        
        return viz_config
    
    @staticmethod
    def _select_chart_type(
        intent: IntentType,
        numeric_cols: List[str],
        categorical_cols: List[str],
        datetime_cols: List[str],
        row_count: int,
        query: str
    ) -> tuple:
        """Select chart type with validation"""
        
        query_lower = query.lower()
        
        # TREND intent → Line chart (if datetime available)
        if intent == IntentType.TREND:
            if datetime_cols:
                return ChartType.LINE, None
            else:
                return ChartType.TABLE, "TREND query requires time dimension"
        
        # COMPARATIVE intent → Bar chart
        if intent == IntentType.COMPARATIVE:
            if categorical_cols and numeric_cols:
                # Check category count
                if row_count > 20:
                    return ChartType.TABLE, "Too many categories for bar chart (>20)"
                return ChartType.BAR, None
            else:
                return ChartType.TABLE, "COMPARATIVE requires categorical and numeric columns"
        
        # PREDICTIVE/PRESCRIPTIVE → Usually table with recommendations
        if intent in [IntentType.PREDICTIVE, IntentType.PRESCRIPTIVE]:
            return ChartType.TABLE, None
        
        # DESCRIPTIVE or DIAGNOSTIC → Depends on data structure
        
        # Single metric → KPI card
        if len(numeric_cols) == 1 and len(categorical_cols) == 0 and row_count == 1:
            return ChartType.KPI, None
        
        # Pie chart for small categorical breakdown
        if len(categorical_cols) == 1 and len(numeric_cols) == 1:
            if row_count <= 7:
                if any(word in query_lower for word in ['distribution', 'breakdown', 'share', 'percentage']):
                    return ChartType.PIE, None
        
        # Bar chart for categorical + numeric
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            if row_count <= 20:
                return ChartType.BAR, None
            else:
                return ChartType.TABLE, "Too many rows for bar chart (>20)"
        
        # Scatter plot for two numeric columns
        if len(numeric_cols) >= 2 and len(categorical_cols) == 0:
            if row_count >= 10:
                if any(word in query_lower for word in ['correlation', 'relationship', 'scatter']):
                    return ChartType.SCATTER, None
        
        # Line chart for time series
        if datetime_cols and numeric_cols:
            return ChartType.LINE, None
        
        # Default to table
        return ChartType.TABLE, None
    
    @staticmethod
    def _determine_axes(
        chart_type: ChartType,
        columns: List[str],
        numeric_cols: List[str],
        categorical_cols: List[str],
        datetime_cols: List[str]
    ) -> tuple:
        """Determine x and y axes based on chart type"""
        
        x_axis = None
        y_axis = None
        
        if chart_type == ChartType.TABLE:
            # No axes for table
            return None, None
        
        if chart_type == ChartType.KPI:
            # KPI shows single value
            if numeric_cols:
                y_axis = [numeric_cols[0]]
            return None, y_axis
        
        if chart_type in [ChartType.BAR, ChartType.PIE]:
            # X = categorical, Y = numeric
            if categorical_cols:
                x_axis = categorical_cols[0]
            elif datetime_cols:
                x_axis = datetime_cols[0]
            elif columns:
                x_axis = columns[0]
            
            if numeric_cols:
                y_axis = [numeric_cols[0]]
            
            return x_axis, y_axis
        
        if chart_type == ChartType.LINE:
            # X = datetime or categorical, Y = numeric
            if datetime_cols:
                x_axis = datetime_cols[0]
            elif categorical_cols:
                x_axis = categorical_cols[0]
            elif columns:
                x_axis = columns[0]
            
            if numeric_cols:
                y_axis = numeric_cols  # Can have multiple lines
            
            return x_axis, y_axis
        
        if chart_type == ChartType.SCATTER:
            # X = first numeric, Y = second numeric
            if len(numeric_cols) >= 2:
                x_axis = numeric_cols[0]
                y_axis = [numeric_cols[1]]
            
            return x_axis, y_axis
        
        # Default
        return x_axis, y_axis


# Singleton instance
visualization_selector = VisualizationSelectorAgent()
