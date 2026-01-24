"""
Query Pattern Service - Store and Retrieve Successful Queries

Implements RAG for SQL generation by:
- Storing successfully executed queries with embeddings
- Finding similar past queries for few-shot examples
- Learning from user corrections and feedback
- Building a knowledge base of business definitions
"""

import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from ..services.embedding_service import embedding_service
from ..services.vector_service import vector_service
from ..database import SessionLocal

logger = logging.getLogger(__name__)


class QueryPatternService:
    """
    Manages query patterns for RAG-enhanced SQL generation.
    Stores successful queries and retrieves similar examples.
    """
    
    def __init__(self):
        self.collection_name = "query_patterns"
    
    async def store_successful_query(
        self,
        question: str,
        sql: str,
        result_summary: str,
        dataset_id: int,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a successfully executed query for future reference.
        
        Args:
            question: Natural language question
            sql: Generated SQL query
            result_summary: Summary of results (row count, columns, etc.)
            dataset_id: ID of dataset used
            user_id: ID of user who ran query
            metadata: Additional metadata (intent, tables used, etc.)
            
        Returns:
            Success boolean
        """
        try:
            # Generate embedding for question
            embedding = embedding_service.generate_embedding(question)
            
            # Prepare metadata
            pattern_metadata = {
                "question": question,
                "sql": sql,
                "result_summary": result_summary,
                "dataset_id": dataset_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store in vector database
            vector_id = f"query_{dataset_id}_{user_id}_{datetime.utcnow().timestamp()}"
            
            vector_service.add_vector(
                collection_name=self.collection_name,
                vector_id=vector_id,
                embedding=embedding,
                metadata=pattern_metadata
            )
            
            logger.info(f"✅ Stored query pattern: {question[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store query pattern: {e}")
            return False
    
    async def find_similar_queries(
        self,
        question: str,
        dataset_id: Optional[int] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find similar past queries using semantic search.
        
        Args:
            question: Natural language question
            dataset_id: Optional dataset ID to filter by
            top_k: Number of similar queries to return
            
        Returns:
            List of similar query patterns
        """
        try:
            # Generate embedding for question
            embedding = embedding_service.generate_embedding(question)
            
            # Search vector database
            results = vector_service.search(
                collection_name=self.collection_name,
                query_embedding=embedding,
                top_k=top_k * 2  # Get more, then filter
            )
            
            # Filter by dataset if specified
            if dataset_id:
                results = [
                    r for r in results
                    if r.get('metadata', {}).get('dataset_id') == dataset_id
                ]
            
            # Limit to top_k
            results = results[:top_k]
            
            logger.info(f"Found {len(results)} similar queries for: {question[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Failed to find similar queries: {e}")
            return []
    
    def get_query_examples_for_prompt(
        self,
        question: str,
        dataset_id: Optional[int] = None,
        max_examples: int = 3
    ) -> str:
        """
        Format similar queries as few-shot examples for prompt.
        
        Args:
            question: Natural language question
            dataset_id: Optional dataset ID
            max_examples: Maximum number of examples
            
        Returns:
            Formatted string for prompt injection
        """
        try:
            # Find similar queries (sync wrapper)
            import asyncio
            loop = asyncio.get_event_loop()
            similar_queries = loop.run_until_complete(
                self.find_similar_queries(question, dataset_id, max_examples)
            )
            
            if not similar_queries:
                return ""
            
            # Format as examples
            examples = ["**SIMILAR PAST QUERIES (for reference):**\n"]
            
            for i, query in enumerate(similar_queries, 1):
                metadata = query.get('metadata', {})
                q = metadata.get('question', 'Unknown')
                sql = metadata.get('sql', 'Unknown')
                
                examples.append(f"Example {i}:")
                examples.append(f"Question: {q}")
                examples.append(f"SQL: {sql}")
                examples.append("")
            
            return "\n".join(examples)
            
        except Exception as e:
            logger.error(f"Failed to format query examples: {e}")
            return ""
    
    async def store_user_correction(
        self,
        original_question: str,
        original_sql: str,
        corrected_sql: str,
        dataset_id: int,
        user_id: int
    ) -> bool:
        """
        Store user correction to learn from feedback.
        
        Args:
            original_question: Original question
            original_sql: Original (incorrect) SQL
            corrected_sql: User-corrected SQL
            dataset_id: Dataset ID
            user_id: User ID
            
        Returns:
            Success boolean
        """
        try:
            # Store corrected version as a successful pattern
            return await self.store_successful_query(
                question=original_question,
                sql=corrected_sql,
                result_summary="User-corrected query",
                dataset_id=dataset_id,
                user_id=user_id,
                metadata={
                    "is_correction": True,
                    "original_sql": original_sql,
                    "correction_type": "user_feedback"
                }
            )
        except Exception as e:
            logger.error(f"Failed to store user correction: {e}")
            return False
    
    async def get_business_definitions(
        self,
        question: str,
        dataset_id: int
    ) -> List[Dict[str, str]]:
        """
        Retrieve business definitions mentioned in question.
        
        Args:
            question: Natural language question
            dataset_id: Dataset ID
            
        Returns:
            List of business definitions
        """
        try:
            # Search for queries with business definitions
            similar = await self.find_similar_queries(question, dataset_id, top_k=5)
            
            definitions = []
            for query in similar:
                metadata = query.get('metadata', {})
                if metadata.get('has_business_definition'):
                    definitions.append({
                        "term": metadata.get('business_term'),
                        "definition": metadata.get('business_definition'),
                        "sql_pattern": metadata.get('sql')
                    })
            
            return definitions
            
        except Exception as e:
            logger.error(f"Failed to get business definitions: {e}")
            return []


# Singleton instance
query_pattern_service = QueryPatternService()
