"""
Embedding Service - Generate and Manage Vector Embeddings for RAG

This service handles generating embeddings for schema information, queries, and business terms
to enable semantic search and retrieval-augmented generation (RAG).

Uses OpenAI's text-embedding-3-small model for cost-effective, high-quality embeddings.
"""

import openai
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from ..config import settings
import asyncio

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        """Initialize embedding service with OpenRouter support"""
        # Make API key optional - get it if it exists
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        # Check if using OpenRouter (key starts with sk-or-)
        self.use_openrouter = self.api_key and self.api_key.startswith('sk-or-')
        
        if self.use_openrouter:
            # OpenRouter configuration
            self.model = "openai/text-embedding-3-small"  # OpenRouter model path
            self.dimensions = 1536  # Standard for text-embedding-3-small
            logger.info("Using OpenRouter for embeddings")
        else:
            # Direct OpenAI configuration
            self.model = getattr(settings, 'EMBEDDING_MODEL', 'text-embedding-3-small')
            self.dimensions = getattr(settings, 'EMBEDDING_DIMENSIONS', 1536)
            if self.api_key:
                logger.info("Using OpenAI directly for embeddings")
        
        self.batch_size = getattr(settings, 'EMBEDDING_BATCH_SIZE', 100)  # Add batch_size for all configurations
        
        if self.api_key:
            try:
                from openai import OpenAI
                
                if self.use_openrouter:
                    # OpenRouter endpoint
                    self.client = OpenAI(
                        api_key=self.api_key,
                        base_url="https://openrouter.ai/api/v1"
                    )
                else:
                    # Direct OpenAI
                    self.client = OpenAI(api_key=self.api_key)
                
                logger.info(f"✅ Embedding service initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize embedding client: {str(e)}")
                self.client = None
        else:
            logger.warning("⚠️ OpenAI API key not configured. Embedding service will not work. RAG features disabled.")
            self.client = None

    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return None
        
        try:
            # Clean and prepare text
            text = text.strip()
            if not text:
                return None
            
            # Generate embedding
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.
        More efficient than calling generate_embedding multiple times.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (same order as input)
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return [None] * len(texts)
        
        try:
            # Clean texts
            cleaned_texts = [text.strip() for text in texts if text and text.strip()]
            
            if not cleaned_texts:
                return [None] * len(texts)
            
            # Process in batches
            all_embeddings = []
            
            for i in range(0, len(cleaned_texts), self.batch_size):
                batch = cleaned_texts[i:i + self.batch_size]
                
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return [None] * len(texts)
    
    def embed_column_schema(self, column_info: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for a database column schema.
        Combines column name, data type, and description into a rich representation.
        
        Args:
            column_info: Dictionary with column metadata
                - column_name: Name of the column
                - data_type: SQL data type
                - description: Optional description
                - business_name: Optional business-friendly name
                - sample_values: Optional sample values
                
        Returns:
            Embedding vector
        """
        # Build rich text representation
        parts = []
        
        # Column name
        parts.append(f"Column: {column_info.get('column_name', '')}")
        
        # Business name if available
        if column_info.get('business_name'):
            parts.append(f"Business Name: {column_info['business_name']}")
        
        # Data type
        parts.append(f"Type: {column_info.get('data_type', '')}")
        
        # Description
        if column_info.get('description'):
            parts.append(f"Description: {column_info['description']}")
        
        # Sample values (first few)
        if column_info.get('sample_values'):
            samples = column_info['sample_values'][:5]
            parts.append(f"Sample values: {', '.join(map(str, samples))}")
        
        # Semantic tags
        if column_info.get('semantic_tags'):
            tags = ', '.join(column_info['semantic_tags'])
            parts.append(f"Tags: {tags}")
        
        text = " | ".join(parts)
        return self.generate_embedding(text)
    
    def embed_query(self, natural_language: str, context: Optional[str] = None) -> Optional[List[float]]:
        """
        Generate embedding for a natural language query.
        
        Args:
            natural_language: The user's question
            context: Optional additional context
            
        Returns:
            Embedding vector
        """
        text = natural_language
        if context:
            text = f"{natural_language} | Context: {context}"
        
        return self.generate_embedding(text)
    
    def embed_business_term(self, term_info: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for a business term definition.
        
        Args:
            term_info: Dictionary with term metadata
                - business_term: The term itself
                - definition: Definition of the term
                - synonyms: List of synonyms
                - category: Category (metric, dimension, etc.)
                
        Returns:
            Embedding vector
        """
        parts = []
        
        parts.append(f"Term: {term_info.get('business_term', '')}")
        parts.append(f"Definition: {term_info.get('definition', '')}")
        
        if term_info.get('synonyms'):
            synonyms = ', '.join(term_info['synonyms'])
            parts.append(f"Synonyms: {synonyms}")
        
        if term_info.get('category'):
            parts.append(f"Category: {term_info['category']}")
        
        if term_info.get('example_usage'):
            parts.append(f"Example: {term_info['example_usage']}")
        
        text = " | ".join(parts)
        return self.generate_embedding(text)
    
    def cosine_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1 (higher is more similar)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the most similar embeddings to a query.
        
        Args:
            query_embedding: The query embedding vector
            candidate_embeddings: List of dicts with 'embedding' and other metadata
            top_k: Number of top results to return
            
        Returns:
            List of top_k most similar items with similarity scores
        """
        results = []
        
        for candidate in candidate_embeddings:
            if 'embedding' not in candidate or not candidate['embedding']:
                continue
            
            similarity = self.cosine_similarity(query_embedding, candidate['embedding'])
            
            result = candidate.copy()
            result['similarity_score'] = similarity
            results.append(result)
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results[:top_k]


# Global instance
embedding_service = EmbeddingService()
