"""
Plotly Visualization Service

Generates interactive Plotly visualizations instead of static matplotlib charts.
Provides professional, interactive charts with hover, zoom, and pan capabilities.
"""

import logging
import json
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

logger = logging.getLogger(__name__)


class PlotlyService:
    """Generates interactive Plotly visualizations."""
    
    @staticmethod
    def generate_chart(
        data: List[Dict[str, Any]],
        chart_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate interactive Plotly chart.
        
        Args:
            data: Query results
            chart_type: Type of chart (bar, line, scatter, pie, etc.)
            config: Chart configuration (x_axis, y_axis, title, etc.)
            
        Returns:
            Plotly JSON configuration
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            if df.empty:
                return {"success": False, "error": "No data to visualize"}
            
            # Generate chart based on type
            if chart_type == "bar":
                fig = PlotlyService._create_bar_chart(df, config)
            elif chart_type == "line":
                fig = PlotlyService._create_line_chart(df, config)
            elif chart_type == "scatter":
                fig = PlotlyService._create_scatter_chart(df, config)
            elif chart_type == "pie":
                fig = PlotlyService._create_pie_chart(df, config)
            elif chart_type == "heatmap":
                fig = PlotlyService._create_heatmap(df, config)
            else:
                # Default to bar chart
                fig = PlotlyService._create_bar_chart(df, config)
            
            # Apply professional styling
            PlotlyService._apply_professional_theme(fig)
            
            # Return JSON
            return {
                "success": True,
                "plotly_json": fig.to_json(),
                "chart_type": chart_type
            }
            
        except Exception as e:
            logger.error(f"Error generating Plotly chart: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _create_bar_chart(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create interactive bar chart."""
        x_col = config.get('x_axis', df.columns[0])
        y_col_raw = config.get('y_axis', df.columns[1] if len(df.columns) > 1 else df.columns[0])
        y_col = y_col_raw[0] if isinstance(y_col_raw, list) and y_col_raw else y_col_raw if not isinstance(y_col_raw, list) else df.columns[1]
        title = config.get('title', 'Bar Chart')
        
        fig = go.Figure(data=[
            go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker=dict(
                    color=df[y_col] if pd.api.types.is_numeric_dtype(df[y_col]) else None,
                    colorscale='Viridis',
                    showscale=True
                ),
                hovertemplate='<b>%{x}</b><br>%{y:,.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        
        return fig
    
    @staticmethod
    def _create_line_chart(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create interactive line chart."""
        x_col = config.get('x_axis', df.columns[0])
        y_col_raw = config.get('y_axis', df.columns[1] if len(df.columns) > 1 else df.columns[0])
        y_col = y_col_raw[0] if isinstance(y_col_raw, list) and y_col_raw else y_col_raw if not isinstance(y_col_raw, list) else df.columns[1]
        title = config.get('title', 'Line Chart')
        
        fig = go.Figure(data=[
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='lines+markers',
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>%{y:,.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        
        return fig
    
    @staticmethod
    def _create_scatter_chart(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create interactive scatter plot."""
        x_col = config.get('x_axis', df.columns[0])
        y_col = config.get('y_axis', df.columns[1] if len(df.columns) > 1 else df.columns[0])
        title = config.get('title', 'Scatter Plot')
        
        fig = go.Figure(data=[
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='markers',
                marker=dict(
                    size=10,
                    color=df[y_col] if pd.api.types.is_numeric_dtype(df[y_col]) else None,
                    colorscale='Viridis',
                    showscale=True
                ),
                hovertemplate='<b>X:</b> %{x}<br><b>Y:</b> %{y:,.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        
        return fig
    
    @staticmethod
    def _create_pie_chart(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create interactive pie chart."""
        labels_col = config.get('x_axis', df.columns[0])
        values_col = config.get('y_axis', df.columns[1] if len(df.columns) > 1 else df.columns[0])
        title = config.get('title', 'Pie Chart')
        
        fig = go.Figure(data=[
            go.Pie(
                labels=df[labels_col],
                values=df[values_col],
                hovertemplate='<b>%{label}</b><br>%{value:,.2f}<br>%{percent}<extra></extra>',
                textposition='inside',
                textinfo='percent+label'
            )
        ])
        
        fig.update_layout(title=title)
        
        return fig
    
    @staticmethod
    def _create_heatmap(df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create interactive heatmap."""
        title = config.get('title', 'Heatmap')
        
        # Use numeric columns only
        numeric_df = df.select_dtypes(include=['number'])
        
        fig = go.Figure(data=[
            go.Heatmap(
                z=numeric_df.values,
                x=numeric_df.columns,
                y=list(range(len(numeric_df))),
                colorscale='Viridis',
                hovertemplate='<b>Column:</b> %{x}<br><b>Row:</b> %{y}<br><b>Value:</b> %{z:,.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(title=title)
        
        return fig
    
    @staticmethod
    def _apply_professional_theme(fig: go.Figure):
        """Apply professional styling to chart."""
        fig.update_layout(
            template='plotly_white',
            hovermode='closest',
            font=dict(family='Arial, sans-serif', size=12),
            title_font=dict(size=16, family='Arial, sans-serif'),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=60, r=40, t=80, b=60)
        )


# Singleton instance
plotly_service = PlotlyService()
