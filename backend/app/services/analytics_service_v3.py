"""
Analytics Service V3 - Enhanced Multi-Agent Pipeline

CamelAI-grade multi-agent system with:
- Enhanced prompting with rich context
- Exploratory query phase (2-3 preliminary queries)
- Context enrichment (samples + statistics)
- Executive-level insight generation
- Multi-visualization selection
- Comprehensive response formatting
"""

import time
import logging
import json
from typing import Dict, Any, List, Optional
import pandas as pd

from ..models import Dataset
from ..services.ollama_service import ollama_service
from ..services.context_enrichment_service import context_enrichment_service
from ..services.response_formatter_service import response_formatter_service
from ..agents.enhanced_exploration_agent import enhanced_exploration_agent
from ..prompts.camelai_prompts import (
    MASTER_SYSTEM_PROMPT,
    SQL_GENERATION_PROMPT,
    INSIGHT_PROMPT,
    VISUALIZATION_PROMPT,
    format_schema_with_samples,
    format_conversation_history
)
from ..prompts.enhanced_prompts import (
    format_exploratory_findings_for_prompt
)


logger = logging.getLogger(__name__)


class AnalyticsServiceV3:
    """
    Enhanced Multi-Agent Pipeline (CamelAI-Grade):
    
    User Query
       ↓
    1. Context Enrichment (samples + statistics)
       ↓
    2. Planning (break down into sub-questions)
       ↓
    3. Exploratory Queries (2-3 preliminary queries)
       ↓
    4. Main SQL Generation (informed by exploration)
       ↓
    5. Query Execution
       ↓
    6. Multi-Visualization Selection (2-3 charts)
       ↓
    7. Executive Insight Generation
       ↓
    8. Response Formatting (CamelAI structure)
    """
    
    # Cache enriched schemas
    _schema_cache: Dict[int, Dict[str, Any]] = {}
    
    async def analyze(
        self,
        query: str,
        dataset: Dataset,
        df: pd.DataFrame,
        connection: Any = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute full enhanced multi-agent analytics pipeline.
        
        Args:
            query: Natural language query
            dataset: Dataset model
            df: DataFrame
            connection: Database connection (optional)
            context: Conversation history context
            
        Returns:
            Formatted analysis response
        """
        start_time = time.time()
        
        logger.info(f"🚀 Starting enhanced multi-agent analysis for: '{query}'")
        
        try:
            # Step 1: Context Enrichment
            logger.info("Step 1/8: Enriching schema context...")
            enriched_schema = await self._get_enriched_schema(dataset.id, df, dataset.table_name)
            
            # Step 2: Planning Phase
            logger.info("Step 2/8: Creating analysis plan...")
            planning_result = await self._create_analysis_plan(
                query=query,
                enriched_schema=enriched_schema,
                context=context
            )
            
            understanding = planning_result.get('understanding', query)
            approach = planning_result.get('approach', 'Analyzing data to answer your question')
            sub_questions = planning_result.get('sub_questions', [])
            
            logger.info(f"✅ Plan created: {len(sub_questions)} exploratory sub-questions")
            
            # Step 3: Exploratory Queries
            logger.info("Step 3/8: Running exploratory analysis...")
            exploratory_results = enhanced_exploration_agent.explore(
                sub_questions=sub_questions,
                df=df,
                enriched_schema=enriched_schema,
                max_queries=3
            )
            
            logger.info(f"✅ Exploration complete: {len(exploratory_results)} queries executed")
            
            # Step 4: Main SQL Generation
            logger.info("Step 4/8: Generating main SQL query...")
            sql_result = await self._generate_main_sql(
                query=query,
                enriched_schema=enriched_schema,
                exploratory_results=exploratory_results,
                planning_result=planning_result
            )
            
            main_sql = sql_result.get('sql', '')
            sql_explanation = sql_result.get('explanation', '')
            
            logger.info(f"✅ SQL generated: {len(main_sql)} characters")
            
            # Step 5: Query Execution
            logger.info("Step 5/8: Executing main query...")
            execution_result = await self._execute_query(main_sql, df, connection)
            
            if not execution_result.get('success'):
                raise Exception(f"Query execution failed: {execution_result.get('error')}")
            
            logger.info(f"✅ Query executed: {execution_result.get('row_count', 0)} rows returned")
            
            # Step 6: Multi-Visualization Selection
            logger.info("Step 6/8: Selecting visualizations...")
            visualizations = await self._select_visualizations(
                query=query,
                query_results=execution_result,
                planning_result=planning_result
            )
            
            logger.info(f"✅ Visualizations selected: {len(visualizations)} charts")
            
            # Step 6.5: Generate Python Charts
            logger.info("Step 6.5/8: Generating Python visualizations...")
            python_charts = await self._generate_python_charts(
                visualizations=visualizations,
                query_results=execution_result
            )
            
            logger.info(f"✅ Charts generated: {len(python_charts)} images")
            
            # Step 7: Executive Insight Generation
            logger.info("Step 7/8: Generating executive insights...")
            insights = await self._generate_insights(
                query=query,
                execution_result=execution_result,
                exploratory_results=exploratory_results,
                enriched_schema=enriched_schema
            )
            
            logger.info(f"✅ Insights generated")
            
            # Step 8: Response Formatting
            logger.info("Step 8/8: Formatting final response...")
            total_time_ms = int((time.time() - start_time) * 1000)
            
            response = response_formatter_service.format_final_response(
                query=query,
                understanding=understanding,
                approach=approach,
                exploratory_results=exploratory_results,
                main_sql=main_sql,
                sql_explanation=sql_explanation,
                query_results=execution_result,
                visualizations=visualizations,
                python_charts=python_charts,
                insights=insights,
                schema_analysis=enriched_schema,
                execution_time_ms=total_time_ms
            )
            
            logger.info(f"✅ Analysis complete in {total_time_ms}ms")
            return response
            
        except Exception as e:
            logger.error(f"❌ Analysis pipeline failed: {str(e)}", exc_info=True)
            return self._create_error_response(query, str(e))
    
    async def _get_enriched_schema(
        self,
        dataset_id: int,
        df: pd.DataFrame,
        table_name: str
    ) -> Dict[str, Any]:
        """Get or create enriched schema with caching."""
        if dataset_id in self._schema_cache:
            logger.info("Using cached enriched schema")
            return self._schema_cache[dataset_id]
        
        enriched_schema = context_enrichment_service.enrich_schema_context(
            df=df,
            table_name=table_name
        )
        
        self._schema_cache[dataset_id] = enriched_schema
        return enriched_schema
    
    async def _create_analysis_plan(
        self,
        query: str,
        enriched_schema: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create analysis plan with sub-questions."""
        try:
            # Format context
            schema_details = format_schema_for_prompt(enriched_schema)
            sample_data = format_sample_data_for_prompt(enriched_schema.get('sample_data', []))
            column_stats = format_column_statistics_for_prompt(enriched_schema.get('column_statistics', {}))
            conversation_context = format_conversation_context_for_prompt(
                context.get('history', []) if context else []
            )
            
            # Create prompt
            prompt = PLANNING_PROMPT_TEMPLATE.format(
                question=query,
                schema_details=schema_details,
                sample_data=sample_data,
                column_statistics=column_stats,
                conversation_context=conversation_context
            )
            
            # Generate with LLM
            response = ollama_service.generate_response(
                prompt=prompt,
                json_mode=True,
                task_type='planning'
            )
            
            # Parse JSON
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Error creating analysis plan: {str(e)}")
            return {
                'understanding': query,
                'approach': 'Direct analysis',
                'sub_questions': [
                    'What is the overall data volume?',
                    'What are the key metrics?'
                ],
                'required_metrics': [],
                'suggested_visualizations': ['table']
            }
    
    async def _generate_main_sql(
        self,
        query: str,
        enriched_schema: Dict[str, Any],
        exploratory_results: List[Dict[str, Any]],
        planning_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate main SQL query informed by exploration."""
        try:
            # Format schema with samples (CamelAI style)
            import pandas as pd
            # Create a small sample DataFrame for schema formatting
            sample_data = enriched_schema.get('sample_data', [])
            if sample_data:
                df_sample = pd.DataFrame(sample_data[:100])
            else:
                # Fallback: create empty DataFrame with column info
                columns = [col['name'] for col in enriched_schema.get('columns', [])]
                df_sample = pd.DataFrame(columns=columns)
            
            schema_with_samples = format_schema_with_samples(df_sample, enriched_schema)
            
            # Format conversation history
            last_3_exchanges = format_conversation_history([])  # TODO: Add actual history
            
            # Create prompt using CamelAI template
            prompt = SQL_GENERATION_PROMPT.format(
                schema_with_samples=schema_with_samples,
                last_3_exchanges=last_3_exchanges,
                user_question=query
            )
            
            # Generate with LLM using MASTER_SYSTEM_PROMPT
            response = ollama_service.generate_response(
                prompt=prompt,
                system_prompt=MASTER_SYSTEM_PROMPT,
                json_mode=True,
                task_type='sql_generation'
            )
            
            # Parse JSON
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            # Fallback to simple SELECT
            return {
                'sql': f"SELECT * FROM data LIMIT 100",
                'explanation': 'Fallback query due to generation error',
                'complexity': 'simple'
            }
    
    async def _execute_query(
        self,
        sql: str,
        df: pd.DataFrame,
        connection: Any
    ) -> Dict[str, Any]:
        """Execute SQL query with DuckDB."""
        try:
            import duckdb
            
            conn = duckdb.connect(':memory:')
            conn.register('data', df)
            
            result = conn.execute(sql).fetchall()
            columns = [desc[0] for desc in conn.description]
            
            # Convert to list of dictionaries
            data = [dict(zip(columns, row)) for row in result]
            
            conn.close()
            
            return {
                'success': True,
                'data': data,
                'columns': columns,
                'row_count': len(data),
                'execution_time_ms': 0
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                'success': False,
                'data': [],
                'columns': [],
                'row_count': 0,
                'error': str(e)
            }
    
    async def _select_visualizations(
        self,
        query: str,
        query_results: Dict[str, Any],
        planning_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Select 2-3 complementary visualizations."""
        try:
            # Analyze result structure
            columns = query_results.get('columns', [])
            data = query_results.get('data', [])
            row_count = len(data)
            
            if not data or not columns:
                return []
            
            # Determine column types
            column_types = {}
            has_time_column = False
            has_categorical_column = False
            numeric_columns = []
            
            for col in columns:
                # Simple type inference from first row
                if data:
                    val = data[0].get(col)
                    if isinstance(val, (int, float)):
                        column_types[col] = 'numeric'
                        numeric_columns.append(col)
                    elif isinstance(val, str):
                        column_types[col] = 'categorical'
                        has_categorical_column = True
                    else:
                        column_types[col] = 'text'
            
            # Create prompt using CamelAI template
            column_info = ", ".join([f"{col} ({column_types.get(col, 'unknown')})" for col in columns])
            results_json = json.dumps(data[:10], indent=2, default=str)
            
            prompt = VISUALIZATION_PROMPT.format(
                results_json=results_json,
                column_info=column_info,
                row_count=row_count,
                user_question=query
            )
            
            # Generate with LLM using MASTER_SYSTEM_PROMPT
            response = ollama_service.generate_response(
                prompt=prompt,
                system_prompt=MASTER_SYSTEM_PROMPT,
                json_mode=True,
                task_type='visualization'
            )
            
            # Parse JSON
            result = json.loads(response)
            # Wrap single chart in array if needed
            if 'chart_type' in result:
                return [{
                    'type': result['chart_type'],
                    'config': result.get('config', {}),
                    'purpose': result.get('reasoning', '')
                }]
            return result.get('visualizations', [])
            
        except Exception as e:
            logger.error(f"Error selecting visualizations: {str(e)}")
            # Fallback to table view
            return [{
                'type': 'table',
                'config': {
                    'title': 'Query Results',
                    'columns': query_results.get('columns', [])
                },
                'purpose': 'Display raw data'
            }]
    
    async def _generate_python_charts(
        self,
        visualizations: List[Dict[str, Any]],
        query_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actual Python/matplotlib charts from visualization configs."""
        from ..services.visualization_service import visualization_service
        
        charts = []
        data = query_results.get('data', [])
        columns = query_results.get('columns', [])
        
        if not data or not columns:
            return charts
        
        try:
            for i, viz in enumerate(visualizations[:3]):  # Limit to 3 charts
                chart_type = viz.get('type', 'bar')
                config = viz.get('config', {})
                
                # Generate chart using visualization service
                result = visualization_service.generate_chart(
                    data=data,
                    columns=columns,
                    chart_type=chart_type,
                    title=config.get('title', f'Visualization {i+1}')
                )
                
                if result.get('success'):
                    charts.append({
                        'type': chart_type,
                        'image': result.get('image'),
                        'title': config.get('title', f'Chart {i+1}')
                    })
        except Exception as e:
            logger.error(f"Error generating Python charts: {str(e)}")
        
        return charts
    
    async def _generate_insights(
        self,
        query: str,
        execution_result: Dict[str, Any],
        exploratory_results: List[Dict[str, Any]],
        enriched_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive-level insights."""
        try:
            # Format results for prompt
            data = execution_result.get('data', [])
            results_json = json.dumps(data[:20], indent=2, default=str)  # Limit to 20 rows
            
            # Create prompt using CamelAI template
            prompt = INSIGHT_PROMPT.format(
                results_json=results_json,
                question=query
            )
            
            # Generate with LLM using MASTER_SYSTEM_PROMPT
            response = ollama_service.generate_response(
                prompt=prompt,
                system_prompt=MASTER_SYSTEM_PROMPT,
                json_mode=True,
                task_type='insight_generation'
            )
            
            # Parse JSON
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {
                'summary': 'Analysis completed successfully.',
                'insights': ['Data retrieved and processed.']
            }
    
    def _create_error_response(self, query: str, error: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            'query': query,
            'success': False,
            'error': {
                'message': 'Analysis failed',
                'details': error,
                'suggestions': [
                    'Check if your question matches the available data',
                    'Try rephrasing your question',
                    'Ensure the dataset contains the requested information'
                ]
            }
        }
    
    @classmethod
    def clear_schema_cache(cls, dataset_id: Optional[int] = None):
        """Clear schema cache."""
        if dataset_id:
            cls._schema_cache.pop(dataset_id, None)
        else:
            cls._schema_cache.clear()


# Singleton instance
analytics_service_v3 = AnalyticsServiceV3()
