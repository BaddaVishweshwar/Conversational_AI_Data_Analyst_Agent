"""
Base classes and data models for the multi-agent analytics pipeline
"""
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class IntentType(str, Enum):
    """Query intent categories"""
    DESCRIPTIVE = "DESCRIPTIVE"  # What happened?
    DIAGNOSTIC = "DIAGNOSTIC"    # Why did it happen?
    COMPARATIVE = "COMPARATIVE"  # A vs B
    TREND = "TREND"              # Over time
    PREDICTIVE = "PREDICTIVE"    # Forecast
    PRESCRIPTIVE = "PRESCRIPTIVE" # Recommendations
    DISTRIBUTION = "DISTRIBUTION" # Spread/Frequency
    CORRELATION = "CORRELATION"  # Relationship


class ColumnType(str, Enum):
    """Column data types"""
    NUMERIC = "NUMERIC"
    CATEGORICAL = "CATEGORICAL"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"
    TEXT = "TEXT"


class ChartType(str, Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    TABLE = "table"
    KPI = "kpi"


# Agent Response Models

class IntentResult(BaseModel):
    """Result from Intent Classification Agent"""
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    required_operations: List[str] = Field(default_factory=list)
    time_dimension_required: bool = False
    comparison_required: bool = False


class ColumnMetadata(BaseModel):
    """Metadata for a single column"""
    name: str
    type: ColumnType
    missing_percentage: float
    unique_count: int
    sample_values: List[Any] = Field(default_factory=list)
    is_aggregatable: bool = False
    is_groupable: bool = False
    
    # Enhanced Profiling Stats (Optional as they might not apply to all types)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_value: Optional[float] = None
    std_dev: Optional[float] = None



class SchemaAnalysis(BaseModel):
    """Result from Schema Analyzer Agent"""
    columns: Dict[str, ColumnMetadata]
    total_rows: int
    numeric_columns: List[str] = Field(default_factory=list)
    categorical_columns: List[str] = Field(default_factory=list)
    datetime_columns: List[str] = Field(default_factory=list)
    potential_relationships: List[Dict[str, str]] = Field(default_factory=list)
    data_quality_score: float = Field(ge=0.0, le=1.0)


class QueryRequirements(BaseModel):
    """Result from Query Understanding Agent"""
    required_columns: List[str]
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    aggregations: List[str] = Field(default_factory=list)
    groupby_columns: List[str] = Field(default_factory=list)
    time_range: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    limit: Optional[int] = None
    validation_errors: List[str] = Field(default_factory=list)


class AnalysisPlanStep(BaseModel):
    """Single step in analysis plan"""
    step_number: int
    operation: str  # filter, aggregate, sort, limit, etc.
    description: str
    columns_involved: List[str]
    expected_output: str


class AnalysisPlan(BaseModel):
    """Result from Analysis Planner Agent"""
    steps: List[AnalysisPlanStep]
    sql_query: str
    supporting_queries: List[Dict[str, str]] = Field(default_factory=list) # List of {name: str, query: str}
    python_code: Optional[str] = None
    expected_columns: List[str]
    validation_passed: bool = True
    validation_errors: List[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    """Result from Execution Engine"""
    success: bool
    data: List[Dict[str, Any]] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    row_count: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)  # All computed metrics
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: int = 0
    error: Optional[str] = None


class VizConfig(BaseModel):
    """Result from Visualization Selector Agent"""
    chart_type: ChartType
    x_axis: Optional[str] = None
    y_axis: Optional[List[str]] = None
    title: str = ""
    description: Optional[str] = None # Added description for the chart
    validation_passed: bool = True
    rejection_reason: Optional[str] = None


class Insights(BaseModel):
    """Result from Insight Generator Agent"""
    direct_answer: str
    what_data_shows: List[str]
    why_it_happened: List[str]
    business_implications: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    data_sufficiency: Literal["sufficient", "partial", "insufficient"] = "sufficient"



class InterpretationResult(BaseModel):
    """Structured interpretation of data findings (Pre-LLM)"""
    title: str
    main_finding: str
    outliers: List[str] = Field(default_factory=list)
    trends: List[str] = Field(default_factory=list)
    top_contributors: List[str] = Field(default_factory=list)
    correlations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    """
    Final wrapper for all agents' outputs.
    This is what the wrapper service returns to the API.
    """
    intent: IntentResult
    schema_analysis: Optional[SchemaAnalysis] = None
    query_requirements: QueryRequirements
    analysis_plan: AnalysisPlan
    execution_result: ExecutionResult
    interpretation: Optional[InterpretationResult] = None
    visualization: Optional[List[VizConfig]] = None # Changed to List
    insights: Insights
    reasoning_steps: List[str]
    total_time_ms: int = 0
