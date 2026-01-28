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
from ..agents.insight_generator_agent import insight_generator
from ..agents.data_interpretation_agent import data_interpretation_agent
# NEW: Enterprise-Grade Agents
from ..agents.query_planner_agent import query_planner
from ..agents.exploration_agent import exploration_agent
from ..agents.vibe_analysis_agent import vibe_agent # NEW Vibe Agent
from ..services.vector_service import vector_service # NEW Vector Service
from ..agents import (
    AnalysisResponse, ExecutionResult, IntentResult, 
    SchemaAnalysis, QueryRequirements, AnalysisPlan, VizConfig, Insights, InterpretationResult,
    AnalysisPlanStep, ChartType # Added needed imports
)

logger = logging.getLogger(__name__)


class AnalyticsServiceV2:
    """
    Multi-agent pipeline orchestrator (Enterprise-Grade):
    
    User Query
       ↓
    1. Intent Classification
       ↓
    2. Schema Analysis (cached, now with samples + stats)
       ↓
    3. Query Planning (NEW - breaks down question)
       ↓
    4. Exploration (NEW - runs 2-3 preliminary queries)
       ↓
    5. Query Understanding
       ↓
    6. Analysis Planning (informed by exploration)
       ↓
    7. Deterministic Execution
       ↓
    8. Data Interpretation
       ↓
    9. Visualization Selection
       ↓
    10. Insight Generation (uses ALL context)
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
                # NEW: Store schema in Vector DB for grounding
                try:
                    schema_text = schema_analyzer.get_enriched_schema_prompt(schema_analysis, df)
                    col_meta = [col.dict() for col in schema_analysis.columns.values()]
                    vector_service.store_schema_context(str(dataset.id), schema_text, col_meta)
                    logger.info(f"✅ Schema stored in Vector DB for dataset {dataset.id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store schema in Vector DB: {e}")
                
                reasoning_steps.append(f"Schema analyzed: {len(schema_analysis.numeric_columns)} numeric, "
                                     f"{len(schema_analysis.categorical_columns)} categorical columns")

            # --- DISABLED VIBE PIPELINE (CAUSING ERRORS) ---
            # Use standard multi-agent pipeline instead
            # logger.info("🚀 Switching to Vibe Agent Pipeline...")
            # vibe_result = vibe_agent.analyze(query, df, str(dataset.id), vibe_history)
            # if vibe_result.get("action") == "error":
            #     raise Exception(vibe_result.get("error", "Unknown Vibe Error"))
            
            # --- STANDARD V2 PIPELINE (RELIABLE) ---
            
            # (Legacy Steps 3-9 are now unreachable due to the return above)
            
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
            
            # Step 3.5: Query Planning (NEW - Enterprise Grade)
            logger.info("Step 3.5/10: Planning comprehensive analysis...")
            planning_result = query_planner.plan(
                query=resolved_query,
                schema_analysis=schema_analysis,
                df=df,
                conversation_history="\n".join([f"{h.get('role', 'user')}: {h.get('content', '')}" for h in history[-3:]])
            )
            reasoning_steps.append(f"Analysis approach: {planning_result.approach}")
            logger.info(f"✅ Planning complete: {len(planning_result.sub_questions)} sub-questions")
            
            # Step 4: Exploration (NEW - Enterprise Grade)
            logger.info("Step 4/10: Running exploratory analysis...")
            exploration_results = exploration_agent.explore(
                sub_questions=planning_result.sub_questions,
                df=df,
                schema_analysis=schema_analysis,
                max_queries=3
            )
            
            # Convert to dict for serialization
            exploration_dicts = [exp.to_dict() for exp in exploration_results]
            
            for i, exp in enumerate(exploration_results, 1):
                reasoning_steps.append(f"Exploration {i}: {exp.finding}")
            logger.info(f"✅ Exploration complete: {len(exploration_results)} queries executed")

            # Steps 4-6: Planning & Execution Loop (with Retry)
            execution_result = None
            last_exec_error = None
            MAX_RETRIES = 2
            
            for attempt in range(MAX_RETRIES + 1):
                logger.info(f"Step 5/10: Creating main analysis plan (Attempt {attempt+1})...")
                
                # Step 5: Analysis Planning (now informed by exploration)
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
                logger.info(f"Step 6/10: Executing main query (Attempt {attempt+1})...")
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
            logger.info("Step 7/10: Selecting visualization...")
            visualizations = visualization_selector.select(
                intent=intent,
                execution_result=execution_result,
                query=query
            )
            
            reasoning_steps.append(f"Visualizations selected: {len(visualizations)} charts")
            
            # Step 8: Data Interpretation (Reasoning Layer)
            logger.info("Step 8/10: Interpreting data...")
            interpretation = data_interpretation_agent.interpret(
                execution_result=execution_result,
                intent=intent
            )
            reasoning_steps.append(f"Data interpretation: {interpretation.main_finding}")

            # Step 9: Insight Generation (with ALL context - Enterprise Grade)
            logger.info("Step 9/10: Generating executive insights...")
            insights = insight_generator.generate(
                query=query,
                execution_result=execution_result,
                intent=intent,
                interpretation=interpretation,
                exploration_findings=exploration_dicts,  # NEW: Pass exploration context
                conversation_history=history
            )
            
            reasoning_steps.append(f"Insights generated with {insights.confidence:.0%} confidence")
            
            # Build final response (Enterprise-Grade structure)
            total_time = int((time.time() - start_time) * 1000)
            
            response = AnalysisResponse(
                # NEW: Enterprise fields
                understanding=planning_result.understanding,
                approach=planning_result.approach,
                exploratory_steps=exploration_dicts,
                # EXISTING
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
            logger.info(f"Summary: {len(exploration_results)} explorations, {len(execution_result.data)} result rows, {len(visualizations)} charts")
            
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
            interpretation=InterpretationResult(
                title="Error",
                main_finding=error,
                outliers=[],
                trends=[],
                top_contributors=[],
                correlations=[],
                warnings=[error]
            ),
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
