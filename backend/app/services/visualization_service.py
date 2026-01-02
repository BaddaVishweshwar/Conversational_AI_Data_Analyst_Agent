import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Dict, Any, List, Optional
import io
import base64
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10


class VisualizationService:
    """Service for generating matplotlib visualizations"""
    
    @staticmethod
    def generate_chart(
        data: List[Dict],
        columns: List[str],
        chart_type: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate matplotlib chart and return as base64 image"""
        
        try:
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == "bar":
                VisualizationService._create_bar_chart(df, columns, ax, title)
            elif chart_type == "line":
                VisualizationService._create_line_chart(df, columns, ax, title)
            elif chart_type == "pie":
                VisualizationService._create_pie_chart(df, columns, ax, title)
            elif chart_type == "scatter":
                VisualizationService._create_scatter_chart(df, columns, ax, title)
            else:
                # Default to bar chart
                VisualizationService._create_bar_chart(df, columns, ax, title)
            
            # Convert plot to base64 image
            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            
            return {
                "success": True,
                "image": f"data:image/png;base64,{image_base64}",
                "type": chart_type,
                "error": None
            }
            
        except Exception as e:
            plt.close('all')
            return {
                "success": False,
                "image": None,
                "type": chart_type,
                "error": str(e)
            }
            
    @staticmethod
    def generate_custom_chart(
        data: List[Dict],
        python_code: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute AI-generated Python code to create a matplotlib chart"""
        try:
            df = pd.DataFrame(data)
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Local context for execution
            local_vars = {
                'df': df,
                'plt': plt,
                'sns': sns,
                'ax': ax,
                'title': title
            }
            
            # Execute the code
            # We assume the code uses 'df' as input and 'ax' for plotting
            exec(python_code, {}, local_vars)
            
            # Convert plot to base64 image
            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            
            return {
                "success": True,
                "image": f"data:image/png;base64,{image_base64}",
                "error": None
            }
        except Exception as e:
            import traceback
            plt.close('all')
            print(f"Python viz error: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "image": None,
                "error": str(e)
            }
    
    @staticmethod
    def _create_bar_chart(df: pd.DataFrame, columns: List[str], ax, title: Optional[str]):
        """Create a bar chart"""
        if len(columns) >= 2:
            x_col = columns[0]
            y_col = columns[1]
            
            # Sort by y value for better visualization
            df_sorted = df.sort_values(by=y_col, ascending=False)
            
            # Create bar chart
            bars = ax.bar(range(len(df_sorted)), df_sorted[y_col], color='steelblue', alpha=0.8)
            ax.set_xticks(range(len(df_sorted)))
            ax.set_xticklabels(df_sorted[x_col], rotation=45, ha='right')
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            ax.set_title(title or f'{y_col.replace("_", " ").title()} by {x_col.replace("_", " ").title()}')
            
            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=9)
            
            ax.grid(axis='y', alpha=0.3)
    
    @staticmethod
    def _create_line_chart(df: pd.DataFrame, columns: List[str], ax, title: Optional[str]):
        """Create a line chart"""
        if len(columns) >= 2:
            x_col = columns[0]
            
            # Plot each numeric column
            for col in columns[1:]:
                ax.plot(df[x_col], df[col], marker='o', label=col.replace('_', ' ').title(), linewidth=2)
            
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel('Value')
            ax.set_title(title or 'Trend Analysis')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Rotate x-axis labels if needed
            if len(df) > 10:
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    @staticmethod
    def _create_pie_chart(df: pd.DataFrame, columns: List[str], ax, title: Optional[str]):
        """Create a pie chart"""
        if len(columns) >= 2:
            labels_col = columns[0]
            values_col = columns[1]
            
            # Create pie chart
            colors = sns.color_palette('husl', len(df))
            wedges, texts, autotexts = ax.pie(
                df[values_col],
                labels=df[labels_col],
                autopct='%1.1f%%',
                colors=colors,
                startangle=90
            )
            
            # Improve text readability
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(9)
                autotext.set_weight('bold')
            
            ax.set_title(title or f'Distribution of {values_col.replace("_", " ").title()}')
    
    @staticmethod
    def _create_scatter_chart(df: pd.DataFrame, columns: List[str], ax, title: Optional[str]):
        """Create a scatter plot"""
        if len(columns) >= 2:
            x_col = columns[0]
            y_col = columns[1]
            
            ax.scatter(df[x_col], df[y_col], alpha=0.6, s=100, color='steelblue')
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            ax.set_title(title or f'{y_col.replace("_", " ").title()} vs {x_col.replace("_", " ").title()}')
            ax.grid(True, alpha=0.3)


# Singleton instance
visualization_service = VisualizationService()
