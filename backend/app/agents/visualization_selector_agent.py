import ollama
import json
import logging
from typing import Dict, Any, List, Optional
from ..config import settings
from . import VizConfig, ChartType, IntentResult, ExecutionResult
from ..services.ollama_service import ollama_service

logger = logging.getLogger(__name__)

class VisualizationSelectorAgent:
    """
    Intelligent chart type selection using LLM.
    Selects the best visualization based on data shape, intent, and column types.
    """
    def __init__(self):
        self.model_name = settings.OLLAMA_MODEL

    async def select(
        self,
        intent: IntentResult,
        execution_result: ExecutionResult,
        query: str
    ) -> List[VizConfig]:
        """
        Select 2-3 appropriate visualizations using LLM
        """
        
        if not execution_result.success or not execution_result.data:
            return [VizConfig(chart_type=ChartType.TABLE, title=query, validation_passed=True)]

        data = execution_result.data
        columns = execution_result.columns
        row_count = len(data)
        
        # Prepare context for LLM
        sample_data = json.dumps(data[:3], indent=2, default=str)
        
        prompt = f"""You are a Data Visualization Expert (Enterprise Style). 
Choose 2-3 COMPLEMENTARY charts to visualize this data effectively.
1. Primary Chart: The best single view.
2. KPI Cards: If appropriate (big numbers).
3. Secondary Chart: data from a different angle (e.g., distribution vs trend).

USER QUERY: "{query}"
INTENT: {intent.intent.value}

DATA COLUMNS: {', '.join(columns)}
ROW COUNT: {row_count}

SAMPLE DATA:
{sample_data}

CHART TYPES AVAILABLE:
- "bar": for comparing categories (x=category, y=metric)
- "line": for trends over time (x=date, y=metric) (REQUIRES date/time column)
- "pie": for parts of a whole (x=category, y=metric) (only for < 8 categories)
- "scatter": for correlation between 2 metrics (x=metric, y=metric)
- "histogram": for distribution (x=bin, y=frequency)
- "kpi": for single big number (use only if 1 row)
- "metric_card": for summary stats (total, avg)
- "table": fallback

RULES:
1. Return a LIST of visualizations.
2. If intent is TREND, Primary MUST be "line".
3. Always verify columns exist.

OUTPUT FORMAT (JSON):
{{
    "visualizations": [
        {{
            "chart_type": "bar",
            "x_axis": "column_for_x",
            "y_axis": ["column_for_y"],
            "title": "Sales by Region",
            "description": "Shows regional performance",
            "reason": "Primary comparison view"
        }},
        {{
            "chart_type": "metric_card",
            "title": "Total Sales",
            "x_axis": "total_sales" 
        }}
    ]
}}

Respond with ONLY the JSON."""

        try:
            response = await ollama_service.generate_response(
                prompt=prompt,
                task_type='visualization'
            )
            
            result_text = response.strip()
            
            # Clean JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            start = result_text.find("{")
            end = result_text.rfind("}")
            if start != -1 and end != -1:
                result_text = result_text[start:end+1]
                
            config_data = json.loads(result_text)
            viz_list = config_data.get("visualizations", [])
            
            results = []
            chart_type_map = {
                "bar": ChartType.BAR,
                "line": ChartType.LINE,
                "pie": ChartType.PIE,
                "scatter": ChartType.SCATTER,
                "histogram": ChartType.HISTOGRAM,
                "kpi": ChartType.KPI,
                "metric_card": ChartType.KPI, # Map metric_card to KPI for now
                "table": ChartType.TABLE
            }

            for v in viz_list:
                ctype_str = v.get("chart_type", "table").lower()
                ctype = chart_type_map.get(ctype_str, ChartType.TABLE)
                
                # Check columns
                x = v.get("x_axis")
                ys = v.get("y_axis", [])
                
                # Basic validation (loose) - if column missing, default to table
                valid = True
                if x and x not in columns and ctype != ChartType.KPI: 
                     valid = False
                for y in ys:
                    if y not in columns: valid = False
                
                if not valid:
                    ctype = ChartType.TABLE

                results.append(VizConfig(
                    chart_type=ctype,
                    x_axis=x,
                    y_axis=ys,
                    title=v.get("title", ""),
                    description=v.get("description", ""),
                    validation_passed=True,
                    rejection_reason=v.get("reason")
                ))

            if not results:
                 return [VizConfig(chart_type=ChartType.TABLE, title=query, validation_passed=True)]
            
            return results
            
        except Exception as e:
            logger.error(f"Visualization selection failed: {e}")
            return [VizConfig(
                chart_type=ChartType.TABLE,
                title=query,
                validation_passed=True,
                rejection_reason="Error in selection"
            )]

# Singleton
visualization_selector = VisualizationSelectorAgent()
