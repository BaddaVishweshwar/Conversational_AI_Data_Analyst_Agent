"""
Self-Consistency Service

Implements self-consistency approach for SQL generation:
1. Generate multiple (3) different SQL queries for same question
2. Execute all queries
3. Compare results
4. Pick the best query based on agreement and quality

This significantly improves accuracy by catching edge cases
and selecting the most reliable solution.
"""

import logging
from typing import Dict, Any, List, Optional
import json
from collections import Counter

from ..services.ollama_service import ollama_service
from ..services.duckdb_service import duckdb_service
from ..agents.sql_generation_agent_v2 import sql_generation_agent
import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


class SelfConsistencyService:
    """
    Generates multiple query candidates and picks the best one.
    """
    
    def __init__(self):
        self.num_candidates = 3
        self.temperature_range = [0.1, 0.3, 0.5]  # Different temps for diversity
    
    async def generate_multiple_queries(
        self,
        question: str,
        schema: Dict[str, Any],
        query_analysis: Dict[str, Any],
        similar_queries: List[Dict] = None,
        n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple SQL query candidates.
        
        Args:
            question: Natural language question
            schema: Dataset schema
            query_analysis: Query analysis from understanding agent
            similar_queries: Similar past queries for RAG
            n: Number of candidates to generate
            
        Returns:
            List of query candidates with SQL and reasoning
        """
        try:
            logger.info(f"🔄 Generating {n} query candidates for self-consistency")
            
            candidates = []
            
            for i in range(n):
                # Use different temperature for diversity
                temp = self.temperature_range[i % len(self.temperature_range)]
                
                # Add variation instruction
                variation_context = ""
                if i > 0:
                    variation_context = f"\n\nIMPORTANT: Generate a DIFFERENT approach than previous attempts. Try alternative SQL patterns."
                
                # Modify query analysis to encourage variation
                varied_analysis = query_analysis.copy()
                varied_analysis['variation_seed'] = i
                varied_analysis['additional_context'] = variation_context
                
                # Generate SQL
                result = await sql_generation_agent.generate_sql(
                    question,
                    schema,
                    varied_analysis,
                    similar_queries or [],
                    temperature=temp
                )
                
                if result['success'] and result.get('sql'):
                    candidates.append({
                        'candidate_id': i + 1,
                        'sql': result['sql'],
                        'reasoning': result.get('reasoning', ''),
                        'temperature': temp,
                        'confidence': result.get('confidence', 0.5)
                    })
                    logger.info(f"  Candidate {i+1}: Generated successfully")
                else:
                    logger.warning(f"  Candidate {i+1}: Generation failed")
            
            logger.info(f"✅ Generated {len(candidates)}/{n} candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"Error generating multiple queries: {e}")
            return []
    
    async def pick_best_query(
        self,
        candidates: List[Dict[str, Any]],
        dataset_id: int,
        question: str,
        df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Execute all candidates and pick the best one.
        
        Args:
            candidates: List of query candidates
            dataset_id: Dataset ID for execution
            question: Original question
            
        Returns:
            Best query with execution results
        """
        try:
            logger.info(f"🎯 Evaluating {len(candidates)} candidates")
            
            if not candidates:
                return {
                    'success': False,
                    'error': 'No candidates to evaluate'
                }
            
            # Execute all candidates
            results = []
            for candidate in candidates:
                if df is not None:
                    exec_result = self._execute_adhoc(candidate['sql'], df)
                else:
                    exec_result = duckdb_service.execute_query(
                        dataset_id,
                        candidate['sql']
                    )
                
                results.append({
                    'candidate_id': candidate['candidate_id'],
                    'sql': candidate['sql'],
                    'reasoning': candidate['reasoning'],
                    'success': exec_result['success'],
                    'data': exec_result.get('data', []),
                    'error': exec_result.get('error'),
                    'row_count': len(exec_result.get('data', []))
                })
            
            # Filter successful executions
            successful = [r for r in results if r['success']]
            
            if not successful:
                # All failed - return first candidate with error
                return {
                    'success': False,
                    'sql': results[0]['sql'],
                    'error': 'All candidates failed execution',
                    'all_results': results
                }
            
            # Pick best based on agreement and quality
            best = self._select_best_candidate(successful, question)
            
            logger.info(f"✅ Selected candidate {best['candidate_id']} as best")
            
            return {
                'success': True,
                'sql': best['sql'],
                'data': best['data'],
                'reasoning': best['reasoning'],
                'selected_candidate': best['candidate_id'],
                'total_candidates': len(candidates),
                'successful_candidates': len(successful),
                'agreement_score': best.get('agreement_score', 0),
                'all_results': results
            }
            
        except Exception as e:
            logger.error(f"Error picking best query: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _select_best_candidate(
        self,
        successful: List[Dict[str, Any]],
        question: str
    ) -> Dict[str, Any]:
        """
        Select best candidate based on multiple criteria.
        
        Criteria:
        1. Result agreement (if multiple return same row count)
        2. Non-empty results
        3. Reasonable row count
        4. SQL complexity (simpler is better if results agree)
        """
        if len(successful) == 1:
            successful[0]['agreement_score'] = 1.0
            return successful[0]
        
        # Check for result agreement
        row_counts = [r['row_count'] for r in successful]
        count_frequency = Counter(row_counts)
        most_common_count, frequency = count_frequency.most_common(1)[0]
        
        # Filter candidates with most common row count
        agreed_candidates = [
            r for r in successful
            if r['row_count'] == most_common_count
        ]
        
        # If multiple agree, pick simplest SQL
        if len(agreed_candidates) > 1:
            # Score by SQL length (shorter = simpler)
            for candidate in agreed_candidates:
                sql_length = len(candidate['sql'])
                candidate['simplicity_score'] = 1.0 / (1.0 + sql_length / 100)
                candidate['agreement_score'] = frequency / len(successful)
            
            # Pick highest simplicity score
            best = max(agreed_candidates, key=lambda x: x['simplicity_score'])
        else:
            best = agreed_candidates[0]
            best['agreement_score'] = frequency / len(successful)
        
        return best
    
    async def generate_with_self_consistency(
        self,
        question: str,
        schema: Dict[str, Any],
        query_analysis: Dict[str, Any],
        dataset_id: int,
        similar_queries: List[Dict] = None,
        df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Complete self-consistency workflow: generate → execute → pick best.
        
        Args:
            question: Natural language question
            schema: Dataset schema
            query_analysis: Query analysis
            dataset_id: Dataset ID
            similar_queries: Similar past queries
            
        Returns:
            Best query with results
        """
        # Generate multiple candidates
        candidates = await self.generate_multiple_queries(
            question, schema, query_analysis, similar_queries
        )
        
        if not candidates:
            return {
                'success': False,
                'error': 'Failed to generate candidates'
            }
        
        # Pick best candidate
        return await self.pick_best_query(candidates, dataset_id, question, df)

    def _execute_adhoc(self, sql: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute query against dataframe inplace"""
        try:
            conn = duckdb.connect(':memory:')
            conn.register('data', df)
            
            # Limited execution for safety/speed if not explicit
            if "limit" not in sql.lower():
                sql += " LIMIT 1000"
                
            result = conn.execute(sql).fetchall()
            columns = [desc[0] for desc in conn.description]
            
            data = [dict(zip(columns, row)) for row in result]
            conn.close()
            
            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "sql": sql
            }
        except Exception as e:
            logger.error(f"Adhoc execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "sql": sql
            }


# Singleton instance
self_consistency_service = SelfConsistencyService()
