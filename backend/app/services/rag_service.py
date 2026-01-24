"""
RAG Service - Retrieval-Augmented Generation for Schema Context

This service retrieves relevant schema information, similar queries, and business definitions
to provide rich context for the LLM agents. This is critical for achieving 80% accuracy.

Key Features:
- Semantic search over schema using embeddings
- Retrieve similar successful queries for few-shot learning
- Pull business term definitions
- Build comprehensive context for SQL generation
"""

from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import DatasetSchema, ColumnProfile, QueryTemplate, SemanticMapping
from .embedding_service import embedding_service
import json
import asyncio

logger = logging.getLogger(__name__)


class RAGService:
    """Service for retrieving relevant context using RAG"""
    
    def __init__(self):
        """Initialize RAG service"""
        pass
    
    async def retrieve_schema_context(
        self,
        dataset_id: int,
        user_question: str,
        db: Session,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve relevant schema information for a user question.
        
        Uses semantic search to find the most relevant columns and tables.
        
        Args:
            dataset_id: Dataset identifier
            user_question: User's natural language question
            db: Database session
            top_k: Number of top columns to retrieve
            
        Returns:
            Dictionary with relevant schema context
        """
        try:
            # Generate embedding for the question
            question_embedding = await asyncio.to_thread(embedding_service.embed_query, user_question)
            
            if not question_embedding:
                # Fallback: return all schema if embedding fails
                return await self._get_full_schema(dataset_id, db)
            
            # Get all schema entries for this dataset
            schema_entries = db.query(DatasetSchema).filter(
                DatasetSchema.dataset_id == dataset_id
            ).all()
            
            # Prepare candidates with embeddings
            candidates = []
            for entry in schema_entries:
                if entry.embedding:
                    try:
                        embedding = json.loads(entry.embedding)
                        candidates.append({
                            "column_name": entry.column_name,
                            "data_type": entry.data_type,
                            "business_name": entry.business_name,
                            "description": entry.description,
                            "semantic_tags": json.loads(entry.semantic_tags) if entry.semantic_tags else [],
                            "embedding": embedding
                        })
                    except:
                        continue
            
            # Find most similar columns
            relevant_columns = embedding_service.find_most_similar(
                question_embedding,
                candidates,
                top_k=top_k
            )
            
            # Get column profiles for relevant columns
            column_names = [col["column_name"] for col in relevant_columns]
            profiles = db.query(ColumnProfile).filter(
                and_(
                    ColumnProfile.dataset_id == dataset_id,
                    ColumnProfile.column_name.in_(column_names)
                )
            ).all()
            
            # Build profile map
            profile_map = {}
            for profile in profiles:
                profile_map[profile.column_name] = {
                    "null_percentage": profile.null_percentage,
                    "unique_count": profile.unique_count,
                    "min_value": profile.min_value,
                    "max_value": profile.max_value,
                    "mean_value": profile.mean_value,
                    "top_values": json.loads(profile.top_values) if profile.top_values else [],
                    "sample_values": json.loads(profile.sample_values) if profile.sample_values else []
                }
            
            # Enhance relevant columns with profile data
                if col["column_name"] in profile_map:
                    col["profile"] = profile_map[col["column_name"]]
            
            # If no relevant columns found (e.g. missing embeddings), fallback to full schema
            if not relevant_columns:
                logger.warning(f"No relevant columns found via RAG for dataset {dataset_id}. Falling back to full schema.")
                return await self._get_full_schema(dataset_id, db)
            
            return {
                "relevant_columns": relevant_columns,
                "columns": relevant_columns,  # Add for backward compatibility
                "total_columns": len(schema_entries),
                "retrieval_method": "semantic_search"
            }
            
        except Exception as e:
            logger.error(f"Error in schema retrieval: {str(e)}")
            # Fallback to full schema
            return await self._get_full_schema(dataset_id, db)
    
    async def retrieve_similar_queries(
        self,
        dataset_id: int,
        user_question: str,
        db: Session,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar successful queries for few-shot learning.
        
        Args:
            dataset_id: Dataset identifier
            user_question: User's natural language question
            db: Database session
            top_k: Number of similar queries to retrieve
            
        Returns:
            List of similar query templates
        """
        try:
            # Generate embedding for the question
            question_embedding = await asyncio.to_thread(embedding_service.embed_query, user_question)
            
            if not question_embedding:
                # Fallback: return most recent successful queries
                templates = db.query(QueryTemplate).filter(
                    QueryTemplate.dataset_id == dataset_id
                ).order_by(QueryTemplate.last_used.desc()).limit(top_k).all()
                
                return [self._template_to_dict(t) for t in templates]
            
            # Get all query templates
            templates = db.query(QueryTemplate).filter(
                QueryTemplate.dataset_id == dataset_id
            ).all()
            
            # Prepare candidates
            candidates = []
            for template in templates:
                if template.embedding:
                    try:
                        embedding = json.loads(template.embedding)
                        candidates.append({
                            "id": template.id,
                            "natural_language": template.natural_language,
                            "sql_query": template.sql_query,
                            "query_type": template.query_type,
                            "description": template.description,
                            "complexity": template.complexity,
                            "embedding": embedding
                        })
                    except:
                        continue
            
            # Find most similar queries
            similar_queries = embedding_service.find_most_similar(
                question_embedding,
                candidates,
                top_k=top_k
            )
            
            return similar_queries
            
        except Exception as e:
            logger.error(f"Error retrieving similar queries: {str(e)}")
            return []
    
    async def retrieve_business_definitions(
        self,
        dataset_id: int,
        user_question: str,
        db: Session,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant business term definitions.
        
        Args:
            dataset_id: Dataset identifier
            user_question: User's natural language question
            db: Database session
            top_k: Number of definitions to retrieve
            
        Returns:
            List of relevant business term definitions
        """
        try:
            # Generate embedding for the question
            question_embedding = await asyncio.to_thread(embedding_service.embed_query, user_question)
            
            if not question_embedding:
                # Fallback: return all definitions
                mappings = db.query(SemanticMapping).filter(
                    SemanticMapping.dataset_id == dataset_id
                ).limit(top_k).all()
                
                return [self._mapping_to_dict(m) for m in mappings]
            
            # Get all semantic mappings
            mappings = db.query(SemanticMapping).filter(
                SemanticMapping.dataset_id == dataset_id
            ).all()
            
            # Prepare candidates
            candidates = []
            for mapping in mappings:
                if mapping.embedding:
                    try:
                        embedding = json.loads(mapping.embedding)
                        candidates.append({
                            "business_term": mapping.business_term,
                            "definition": mapping.definition,
                            "sql_expression": mapping.sql_expression,
                            "category": mapping.category,
                            "synonyms": json.loads(mapping.synonyms) if mapping.synonyms else [],
                            "example_usage": mapping.example_usage,
                            "embedding": embedding
                        })
                    except:
                        continue
            
            # Find most similar definitions
            relevant_definitions = embedding_service.find_most_similar(
                question_embedding,
                candidates,
                top_k=top_k
            )
            
            return relevant_definitions
            
        except Exception as e:
            logger.error(f"Error retrieving business definitions: {str(e)}")
            return []
    
    async def build_complete_context(
        self,
        dataset_id: int,
        user_question: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Build complete RAG context for LLM agents.
        
        Combines schema, similar queries, and business definitions.
        
        Args:
            dataset_id: Dataset identifier
            user_question: User's natural language question
            db: Database session
            
        Returns:
            Complete context dictionary
        """
        # Retrieve all components in parallel
        schema_context = await self.retrieve_schema_context(dataset_id, user_question, db)
        similar_queries = await self.retrieve_similar_queries(dataset_id, user_question, db)
        business_definitions = await self.retrieve_business_definitions(dataset_id, user_question, db)
        
        return {
            "schema": schema_context,
            "similar_queries": similar_queries,
            "business_definitions": business_definitions,
            "dataset_id": dataset_id,
            "question": user_question
        }
    
    async def _get_full_schema(self, dataset_id: int, db: Session) -> Dict[str, Any]:
        """Fallback: Get full schema without semantic search"""
        schema_entries = db.query(DatasetSchema).filter(
            DatasetSchema.dataset_id == dataset_id
        ).all()
        
        columns = []
        for entry in schema_entries:
            columns.append({
                "column_name": entry.column_name,
                "data_type": entry.data_type,
                "business_name": entry.business_name,
                "description": entry.description,
                "semantic_tags": json.loads(entry.semantic_tags) if entry.semantic_tags else []
            })
        
        return {
            "relevant_columns": columns,
            "columns": columns,  # Add for backward compatibility
            "total_columns": len(columns),
            "retrieval_method": "full_schema"
        }
    
    def _template_to_dict(self, template: QueryTemplate) -> Dict[str, Any]:
        """Convert QueryTemplate model to dictionary"""
        return {
            "natural_language": template.natural_language,
            "sql_query": template.sql_query,
            "query_type": template.query_type,
            "description": template.description,
            "complexity": template.complexity
        }
    
    def _mapping_to_dict(self, mapping: SemanticMapping) -> Dict[str, Any]:
        """Convert SemanticMapping model to dictionary"""
        return {
            "business_term": mapping.business_term,
            "definition": mapping.definition,
            "sql_expression": mapping.sql_expression,
            "category": mapping.category,
            "synonyms": json.loads(mapping.synonyms) if mapping.synonyms else [],
            "example_usage": mapping.example_usage
        }


# Global instance
rag_service = RAGService()
