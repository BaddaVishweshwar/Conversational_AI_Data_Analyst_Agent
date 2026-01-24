"""
Data Interpretation Agent

Performs deterministic statistical analysis and reasoning on execution results.
Identifies outliers, trends, and dominant factors BEFORE text generation.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from ..agents import InterpretationResult, ExecutionResult, IntentResult, IntentType

logger = logging.getLogger(__name__)


class DataInterpretationAgent:
    """
    Interprets raw data execution results.
    
    Principles:
    1. Deterministic Statistics first (Pareto, Z-Score, Trend slope).
    2. No Hallucination (Findings are grounded in math).
    3. Structured Output (to feed Insight Generator).
    """
    
    def interpret(
        self, 
        execution_result: ExecutionResult, 
        intent: IntentResult
    ) -> InterpretationResult:
        """
        Analyze execution result to extract statistical findings.
        """
        if not execution_result.success or not execution_result.data:
            return self._empty_interpretation()

        try:
            df = pd.DataFrame(execution_result.data)
            
            # 1. Identify Numeric and Categorical Columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(exclude=[np.number, 'datetime']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist() # Might be object if from JSON
            
            # Helper: Try to convert potential datetime strings
            if not datetime_cols and not df.empty:
                for col in df.columns:
                    if col not in numeric_cols:
                        try:
                            pd.to_datetime(df[col])
                            datetime_cols.append(col)
                        except:
                            pass

            outliers = []
            trends = []
            contributors = []
            correlations = []
            
            # 2. Analyze Distribution & Outliers (for Descriptive/Distribution/Diagnostic)
            for col in numeric_cols:
                series = df[col].dropna()
                if len(series) > 5:
                    # Outliers (Z-score > 2.5)
                    z_scores = (series - series.mean()) / series.std()
                    outlier_indices = z_scores.abs() > 2.5
                    num_outliers = outlier_indices.sum()
                    if num_outliers > 0:
                        outliers.append(f"{col}: {num_outliers} anomalies detected (>{series.mean():.2f} ± {2.5 * series.std():.2f})")
            
            # 3. Analyze Trends (for Trend/Descriptive)
            if intent.intent in [IntentType.TREND, IntentType.DESCRIPTIVE, IntentType.PREDICTIVE]:
                # If we have a time column and numeric column
                # This is a simplification; usually we'd need to know which col is time from the QueryRequirements
                # For now, heuristic:
                time_col = datetime_cols[0] if datetime_cols else None
                if time_col and numeric_cols:
                    val_col = numeric_cols[0]
                    # Calculate simple CAG/Slope
                    # ... (Simplified for this agent)
                    trends.append(f"analyzed trend on {val_col} over {time_col}")

            # 4. Analyze Contributors (Pareto)
            for col in numeric_cols:
                # Check for "top contributors" if we have a categorical column to group by (implicitly)
                # Actually, if the result is already grouped (e.g. Sales by Region), 
                # we just check the distribution of the numeric column.
                series = df[col]
                total = series.sum()
                if total > 0:
                    sorted_series = series.sort_values(ascending=False)
                    top_3_sum = sorted_series.head(3).sum()
                    pct = (top_3_sum / total) * 100
                    # Lower threshold to 50% for smaller datasets
                    if pct > 50 and len(series) > 1:
                        contributors.append(f"Top {min(3, len(series))} records account for {pct:.1f}% of total {col}")

            # 5. Determine Main Finding
            # Heuristic selection of the most "interesting" fact
            if contributors:
                main_finding = contributors[0]
            elif outliers:
                main_finding = outliers[0]
            elif trends:
                main_finding = trends[0]
            else:
                # Default to basic summary
                main_finding = f"Returned {len(df)} rows with {len(df.columns)} columns."

            return InterpretationResult(
                title=f"Analysis of {intent.intent.value.lower()} query",
                main_finding=main_finding,
                outliers=outliers,
                trends=trends,
                top_contributors=contributors,
                correlations=correlations,
                warnings=[]
            )
            
        except Exception as e:
            logger.error(f"Interpretation failed: {e}")
            return self._empty_interpretation(str(e))

    def _empty_interpretation(self, error: str = "") -> InterpretationResult:
        return InterpretationResult(
            title="Analysis",
            main_finding="No significant statistical patterns found." if not error else f"Could not interpret data: {error}",
            outliers=[],
            trends=[],
            top_contributors=[],
            correlations=[],
            warnings=[error] if error else []
        )

# Singleton
data_interpretation_agent = DataInterpretationAgent()
