"""
Analytics Service V2 - Multi-Agent Pipeline Orchestrator

Coordinates all agents to deliver production-grade analytics.
"""
import time
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from ..models import Dataset
from ..services.data_service import data_service
from ..agents.intent_classifier_agent import intent_classifier
from ..agents.schema_analyzer_agent import schema_analyzer
from ..agents.query_understanding_agent import query_understanding_agent
from ..agents.analysis_planner_agent import analysis_planner
from ..agents.visualization_selector_agent import visualization_selector
from ..agents.insight_generator_agent import insight_generator
from ..agents.data_interpretation_agent import data_interpretation_agent
from ..agents import (
    AnalysisResponse, ExecutionResult, IntentResult, 
    SchemaAnalysis, QueryRequirements, AnalysisPlan, VizConfig, Insights, InterpretationResult
)

logger = logging.getLogger(__name__)


class AnalyticsServiceV2:
    """
    Multi-agent pipeline orchestrator:
    
    User Query
       ↓
    1. Intent Classification
       ↓
    2. Schema Analysis (cached)
       ↓
    3. Query Understanding
       ↓
    4. Analysis Planning
       ↓
    5. Plan Validation
       ↓
    6. Deterministic Execution
       ↓
    7. Visualization Selection
       ↓
    8. Insight Generation
       ↓
    Final Response
    """
    
    # Cache schema analysis to avoid re-analyzing same dataset
    _schema_cache: Dict[int, SchemaAnalysis] = {}
    
    def analyze(
        self,
        query: str,
        dataset: Dataset,
        df: pd.DataFrame,
        connection: Any = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """
        Execute full multi-agent analytics pipeline
        
        Args:
            query: Natural language query
            dataset: Dataset model
            df: DataFrame (if file-based)
            connection: Database connection (if DB-based)
            context: Conversation history context
            
        Returns:
            AnalysisResponse with all pipeline outputs
        """
        start_time = time.time()
        reasoning_steps = []
        
        logger.info(f"🚀 Starting multi-agent analysis for: '{query}'")
        
        try:
            # Step 0: Context Resolution (Deep Query Understanding)
            from ..agents.query_resolver_agent import query_resolver
            
            resolved_query = query
            if context and context.get('history'):
                logger.info("Step 0/8: Resolving query context...")
                resolution = query_resolver.resolve_query(query, context)
                resolved_query = resolution['resolved_query']
                if resolution['is_followup']:
                    reasoning_steps.append(f"Context resolved: '{query}' → '{resolved_query}'")
                    logger.info(f"Context resolved: '{query}' → '{resolved_query}'")
                else:
                    reasoning_steps.append(f"Query understood as new topic: '{resolved_query}'")

            # Step 1: Intent Classification
            logger.info("Step 1/8: Classifying intent...")
            intent = intent_classifier.classify(resolved_query, dataset.schema)
            reasoning_steps.append(f"Intent classified as {intent.intent.value} with {intent.confidence:.0%} confidence")
            
            # Step 2: Schema Analysis (with caching)
            logger.info("Step 2/8: Analyzing schema...")
            if dataset.id in self._schema_cache:
                schema_analysis = self._schema_cache[dataset.id]
                reasoning_steps.append("Schema analysis retrieved from cache")
            else:
                schema_analysis = schema_analyzer.analyze(df, dataset.schema)
                self._schema_cache[dataset.id] = schema_analysis
                reasoning_steps.append(f"Schema analyzed: {len(schema_analysis.numeric_columns)} numeric, "
                                     f"{len(schema_analysis.categorical_columns)} categorical columns")
            
            # Step 3: Query Understanding
            logger.info("Step 3/8: Understanding query requirements...")
            requirements = query_understanding_agent.understand(resolved_query, schema_analysis, intent)
            
            if requirements.validation_errors:
                # Return early if query has validation errors
                logger.error(f"Query validation failed: {requirements.validation_errors}")
                return self._create_error_response(
                    query=query,
                    error=f"Query validation failed: {'; '.join(requirements.validation_errors)}",
                    intent=intent,
                    schema_analysis=schema_analysis
                )
            
            reasoning_steps.append(f"Identified {len(requirements.required_columns)} required columns, "
                                 f"{len(requirements.aggregations)} aggregations")
            
            # Prepare history for agents
            history = context.get('history', []) if context else []

            # Steps 4-6: Planning & Execution Loop (with Retry)
            execution_result = None
            last_exec_error = None
            MAX_RETRIES = 2
            
            for attempt in range(MAX_RETRIES + 1):
                logger.info(f"Step 4/8: Creating analysis plan (Attempt {attempt+1})...")
                
                # Step 4: Analysis Planning
                plan = analysis_planner.plan(
                    query=resolved_query,
                    requirements=requirements,
                    schema_analysis=schema_analysis,
                    intent=intent,
                    sample_data=dataset.sample_data,
                    error_context=last_exec_error,
                    conversation_history=history
                )
                
                if not plan.validation_passed:
                    last_exec_error = f"Plan validation failed: {'; '.join(plan.validation_errors)}"
                    logger.warning(f"Plan validation failed (Attempt {attempt+1}): {last_exec_error}")
                    reasoning_steps.append(f"Plan validation failed: {last_exec_error}. Retrying...")
                    continue
                
                if attempt == 0:
                    reasoning_steps.append(f"Analysis plan created with {len(plan.steps)} steps")
                else:
                    reasoning_steps.append(f"Refined analysis plan (Attempt {attempt+1})")
                
                # Step 6: Deterministic Execution
                logger.info(f"Step 6/8: Executing query (Attempt {attempt+1})...")
                exec_start = time.time()
                
                # Execute Main Query
                execution_raw = data_service.execute_sql_query(
                    sql_query=plan.sql_query,
                    df=df,
                    connection=connection
                )
                
                # Execute Supporting Queries (if main succeeded)
                intermediate_results = {}
                if execution_raw["success"] and plan.supporting_queries:
                    logger.info(f"Executing {len(plan.supporting_queries)} supporting queries...")
                    for sq in plan.supporting_queries:
                        sq_name = sq.get("name", "Unknown")
                        sq_sql = sq.get("query", "")
                        if sq_sql:
                            sq_res = data_service.execute_sql_query(sq_sql, df, connection)
                            if sq_res["success"]:
                                intermediate_results[sq_name] = sq_res["data"]
                                logger.info(f"Supporting query '{sq_name}' executed: {len(sq_res['data'])} rows")
                            else:
                                logger.warning(f"Supporting query '{sq_name}' failed: {sq_res['error']}")
                
                exec_time = int((time.time() - exec_start) * 1000)
                
                if execution_raw["success"]:
                    # Success
                    execution_result = ExecutionResult(
                        success=True,
                        data=execution_raw["data"],
                        columns=execution_raw["columns"],
                        row_count=len(execution_raw["data"]),
                        metrics={},
                        intermediate_results=intermediate_results,
                        execution_time_ms=exec_time,
                        error=None
                    )
                    reasoning_steps.append(f"Query executed successfully in {exec_time}ms")
                    if intermediate_results:
                        reasoning_steps.append(f"Executed {len(intermediate_results)} supporting queries for context")
                    break
                else:
                    # Failure - Loop back
                    last_exec_error = execution_raw['error']
                    logger.warning(f"Execution failed: {last_exec_error}. Retrying...")
                    reasoning_steps.append(f"Execution failed: {last_exec_error}. Retrying with query correction...")
            
            if not execution_result:
                logger.error(f"Analysis failed after {MAX_RETRIES + 1} attempts. Last error: {last_exec_error}")
                return self._create_error_response(
                    query=query,
                    error=f"Query execution failed: {last_exec_error}",
                    intent=intent,
                    schema_analysis=schema_analysis
                )
            
            # Step 7: Visualization Selection
            logger.info("Step 7/8: Selecting visualization...")
            visualizations = visualization_selector.select(
                intent=intent,
                execution_result=execution_result,
                query=query
            )
            
            reasoning_steps.append(f"Visualizations selected: {len(visualizations)} charts")
            
            # Step 7.5: Data Interpretation (Reasoning Layer)
            logger.info("Step 7.5/8: Interpreting data...")
            interpretation = data_interpretation_agent.interpret(
                execution_result=execution_result,
                intent=intent
            )
            reasoning_steps.append(f"Data interpretation: {interpretation.main_finding}")

            # Step 8: Insight Generation
            logger.info("Step 8/8: Generating insights...")
            insights = insight_generator.generate(
                query=query,
                execution_result=execution_result,
                intent=intent,
                interpretation=interpretation,
                conversation_history=history
            )
            
            reasoning_steps.append(f"Insights generated with {insights.confidence:.0%} confidence")
            
            # Build final response
            total_time = int((time.time() - start_time) * 1000)
            
            response = AnalysisResponse(
                intent=intent,
                schema_analysis=schema_analysis,
                query_requirements=requirements,
                analysis_plan=plan,
                execution_result=execution_result,
                interpretation=interpretation,
                visualization=visualizations,
                insights=insights,
                reasoning_steps=reasoning_steps,
                total_time_ms=total_time
            )
            
            logger.info(f"✅ Analysis complete in {total_time}ms")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Analysis pipeline failed: {e}", exc_info=True)
            return self._create_error_response(
                query=query,
                error=f"Analysis pipeline error: {str(e)}",
                intent=None,
                schema_analysis=None
            )
    
    def _create_error_response(
        self,
        query: str,
        error: str,
        intent: Optional[IntentResult],
        schema_analysis: Optional[SchemaAnalysis]
    ) -> AnalysisResponse:
        """Create error response"""
        
        from ..agents import IntentType, ChartType
        
        # Default intent if not classified
        if intent is None:
            intent = IntentResult(
                intent=IntentType.DESCRIPTIVE,
                confidence=0.0,
                required_operations=[],
                time_dimension_required=False,
                comparison_required=False
            )
        
        # Empty execution result
        execution_result = ExecutionResult(
            success=False,
            data=[],
            columns=[],
            row_count=0,
            metrics={},
            intermediate_results={},
            execution_time_ms=0,
            error=error
        )
        
        # Error insights
        insights = Insights(
            direct_answer=f"Unable to complete analysis: {error}",
            what_data_shows=["The query could not be executed successfully."],
            why_it_happened=[error],
            business_implications=["Review the query and dataset to resolve the issue."],
            confidence=0.0,
            data_sufficiency="insufficient"
        )
        
        # Table visualization for errors
        visualization = [VizConfig(
            chart_type=ChartType.TABLE,
            title=query,
            validation_passed=False,
            rejection_reason=error
        )]
        
        # Empty plan
        plan = AnalysisPlan(
            steps=[],
            sql_query="",
            python_code=None,
            expected_columns=[],
            validation_passed=False,
            validation_errors=[error]
        )
        
        # Empty requirements
        requirements = QueryRequirements(
            required_columns=[],
            filters=[],
            aggregations=[],
            groupby_columns=[],
            time_range=None,
            sort_by=None,
            limit=None,
            validation_errors=[error]
        )
        
        return AnalysisResponse(
            intent=intent,
            schema_analysis=schema_analysis,
            query_requirements=requirements,
            analysis_plan=plan,
            execution_result=execution_result,
            visualization=visualization,
            insights=insights,
            reasoning_steps=[f"Error: {error}"],
            total_time_ms=0
        )
    
    @classmethod
    def clear_schema_cache(cls, dataset_id: Optional[int] = None):
        """Clear schema cache for a specific dataset or all datasets"""
        if dataset_id:
            cls._schema_cache.pop(dataset_id, None)
        else:
            cls._schema_cache.clear()


# Singleton instance
analytics_service_v2 = AnalyticsServiceV2()
