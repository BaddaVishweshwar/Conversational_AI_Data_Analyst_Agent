"""
Business Rules Service

Stores and retrieves user-defined business rules and metrics:
- Custom KPI definitions (e.g., "active user" = "last_login > 30 days")
- Business term mappings
- Domain-specific logic
- User preferences

This allows the system to learn business context once
and apply it consistently across all queries.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..database import SessionLocal
from ..models import BusinessRule
from ..services.embedding_service import embedding_service
from ..services.vector_service import vector_service

logger = logging.getLogger(__name__)


class BusinessRulesService:
    """
    Manages user-defined business rules and metrics.
    """
    
    def __init__(self):
        self.collection_name = "business_rules"
    
    def store_user_definition(
        self,
        user_id: int,
        dataset_id: int,
        term: str,
        definition: str,
        sql_pattern: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a user-defined business rule.
        
        Args:
            user_id: User ID
            dataset_id: Dataset ID
            term: Business term (e.g., "active user")
            definition: Definition (e.g., "user who logged in within 30 days")
            sql_pattern: Optional SQL pattern (e.g., "last_login > CURRENT_DATE - 30")
            metadata: Additional metadata
            
        Returns:
            Success boolean
        """
        try:
            # Generate embedding for term
            embedding = embedding_service.generate_embedding(term)
            
            # Prepare metadata
            rule_metadata = {
                "term": term,
                "definition": definition,
                "sql_pattern": sql_pattern,
                "user_id": user_id,
                "dataset_id": dataset_id,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store in vector database
            vector_id = f"rule_{user_id}_{dataset_id}_{term.replace(' ', '_')}"
            
            vector_service.add_vector(
                collection_name=self.collection_name,
                vector_id=vector_id,
                embedding=embedding,
                metadata=rule_metadata
            )
            
            logger.info(f"✅ Stored business rule: {term} = {definition}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store business rule: {e}")
            return False
    
    def get_relevant_rules(
        self,
        question: str,
        dataset_id: Optional[int] = None,
        user_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve business rules relevant to question.
        
        Args:
            question: Natural language question
            dataset_id: Optional dataset ID filter
            user_id: Optional user ID filter
            top_k: Number of rules to return
            
        Returns:
            List of relevant business rules
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
            
            # Filter by dataset and user if specified
            filtered = []
            for result in results:
                metadata = result.get('metadata', {})
                
                # Check dataset filter
                if dataset_id and metadata.get('dataset_id') != dataset_id:
                    continue
                
                # Check user filter
                if user_id and metadata.get('user_id') != user_id:
                    continue
                
                filtered.append(metadata)
            
            # Limit to top_k
            filtered = filtered[:top_k]
            
            logger.info(f"Found {len(filtered)} relevant business rules")
            return filtered
            
        except Exception as e:
            logger.error(f"Failed to get relevant rules: {e}")
            return []
    
    def format_rules_for_prompt(
        self,
        rules: List[Dict[str, Any]]
    ) -> str:
        """
        Format business rules for inclusion in prompt.
        
        Args:
            rules: List of business rules
            
        Returns:
            Formatted string for prompt
        """
        if not rules:
            return ""
        
        lines = ["**BUSINESS RULES & DEFINITIONS:**\n"]
        
        for i, rule in enumerate(rules, 1):
            term = rule.get('term', 'Unknown')
            definition = rule.get('definition', 'No definition')
            sql_pattern = rule.get('sql_pattern')
            
            lines.append(f"{i}. **{term}**: {definition}")
            if sql_pattern:
                lines.append(f"   SQL Pattern: `{sql_pattern}`")
            lines.append("")
        
        return "\n".join(lines)
    
    def store_common_definitions(self, dataset_id: int, user_id: int = 1):
        """
        Store common business definitions for a dataset.
        
        Args:
            dataset_id: Dataset ID
            user_id: User ID (default 1)
        """
        common_rules = [
            {
                "term": "active user",
                "definition": "User who has logged in within the last 30 days",
                "sql_pattern": "last_login >= CURRENT_DATE - INTERVAL '30 days'"
            },
            {
                "term": "high value customer",
                "definition": "Customer with lifetime value > $1000",
                "sql_pattern": "lifetime_value > 1000"
            },
            {
                "term": "recent order",
                "definition": "Order placed within the last 7 days",
                "sql_pattern": "order_date >= CURRENT_DATE - INTERVAL '7 days'"
            },
            {
                "term": "top performer",
                "definition": "Sales representative in top 10% by revenue",
                "sql_pattern": "revenue >= PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY revenue)"
            },
            {
                "term": "churned customer",
                "definition": "Customer with no purchases in last 90 days",
                "sql_pattern": "last_purchase_date < CURRENT_DATE - INTERVAL '90 days'"
            }
        ]
        
        for rule in common_rules:
            self.store_user_definition(
                user_id=user_id,
                dataset_id=dataset_id,
                term=rule['term'],
                definition=rule['definition'],
                sql_pattern=rule.get('sql_pattern'),
                metadata={'is_common': True}
            )
        
        logger.info(f"Stored {len(common_rules)} common business definitions")
    
    def update_rule_from_feedback(
        self,
        term: str,
        corrected_sql: str,
        dataset_id: int,
        user_id: int
    ) -> bool:
        """
        Update business rule based on user correction.
        
        Args:
            term: Business term
            corrected_sql: User-corrected SQL pattern
            dataset_id: Dataset ID
            user_id: User ID
            
        Returns:
            Success boolean
        """
        try:
            # Extract definition from corrected SQL
            definition = f"Updated based on user correction"
            
            # Store updated rule
            return self.store_user_definition(
                user_id=user_id,
                dataset_id=dataset_id,
                term=term,
                definition=definition,
                sql_pattern=corrected_sql,
                metadata={
                    'is_correction': True,
                    'updated_at': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to update rule from feedback: {e}")
            return False


# Singleton instance
business_rules_service = BusinessRulesService()
