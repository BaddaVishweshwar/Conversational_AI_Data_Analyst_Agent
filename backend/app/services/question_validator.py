"""
Question Validator - Validate if Questions are Answerable

This service checks if a user's question can be answered with the available dataset.
Prevents wasted LLM calls and provides better user experience.
"""

from typing import Dict, Any, Optional
import logging
import json
import asyncio
from ..services.ollama_service import ollama_service
from ..prompts.sql_system_prompts import QUESTION_VALIDATION_SYSTEM_PROMPT
from ..prompts.chain_of_thought_templates import COT_QUESTION_VALIDATION_TEMPLATE

logger = logging.getLogger(__name__)


class QuestionValidator:
    """Validator for checking if questions are answerable"""
    
    def __init__(self):
        """Initialize question validator"""
        self.system_prompt = QUESTION_VALIDATION_SYSTEM_PROMPT
    
    async def validate_question(
        self,
        question: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate if a question can be answered with the available dataset.
        
        Args:
            question: User's natural language question
            schema: Dataset schema information
            
        Returns:
            Dictionary with validation result
        """
        try:
            logger.info(f"Validating question: {question}")
            
            # Quick rule-based checks first
            quick_check = self._quick_validation(question, schema)
            if not quick_check['needs_llm']:
                return quick_check['result']
            
            # Build schema context
            schema_context = self._format_schema(schema)
            
            # Build validation prompt using CoT template
            validation_prompt = COT_QUESTION_VALIDATION_TEMPLATE.format(
                question=question,
                schema=schema_context
            )
            
            # Call LLM for validation
            # Wrap synchronous call in to_thread to avoid blocking event loop
            response = await asyncio.to_thread(
                ollama_service.generate_response,
                prompt=validation_prompt,
                system_prompt=self.system_prompt,
                json_mode=True,
                temperature=0.2,
                task_type='planning'
            )
            
            # Parse JSON response
            try:
                validation = json.loads(response)
            except json.JSONDecodeError:
                logger.warning("Failed to parse validation JSON, using fallback")
                validation = self._fallback_validation(question, schema)
            
            # Enhance validation result
            validation = self._enhance_validation(validation, question, schema)
            
            logger.info(f"Question validation: {'VALID' if validation['is_valid'] else 'INVALID'}")
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating question: {str(e)}")
            return self._fallback_validation(question, schema)
    
    def _quick_validation(self, question: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Quick rule-based validation checks.
        
        Returns:
            Dictionary with 'needs_llm' flag and optional 'result'
        """
        question_lower = question.lower()
        
        # Check for obviously invalid questions
        invalid_keywords = [
            'weather', 'news', 'sports', 'stock market', 'movie', 'recipe',
            'translate', 'define', 'what is the meaning', 'who is', 'when was',
            'how to', 'tutorial', 'guide'
        ]
        
        for keyword in invalid_keywords:
            if keyword in question_lower:
                return {
                    'needs_llm': False,
                    'result': {
                        'is_valid': False,
                        'is_answerable': False,
                        'confidence': 0.95,
                        'required_columns': [],
                        'missing_columns': [],
                        'reason': f"Question appears to be about '{keyword}' which is not related to data analysis",
                        'suggestion': "Please ask a question about the data in your dataset"
                    }
                }
        
        # Check if question is too vague
        vague_questions = ['show me data', 'what do you have', 'tell me about this', 'analyze']
        if question_lower.strip() in vague_questions:
            return {
                'needs_llm': False,
                'result': {
                    'is_valid': False,
                    'is_answerable': False,
                    'confidence': 0.9,
                    'required_columns': [],
                    'missing_columns': [],
                    'reason': "Question is too vague",
                    'suggestion': "Please be more specific. For example: 'What is the total revenue?' or 'Show top 10 products by sales'"
                }
            }

        
        # Needs LLM validation
        return {'needs_llm': True}
    
    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """Format schema for prompt."""
        if isinstance(schema, dict) and 'relevant_columns' in schema:
            columns = schema['relevant_columns']
        elif isinstance(schema, dict) and 'columns' in schema:
            columns = schema['columns']
        else:
            return "Schema information not available"
        
        formatted = []
        for col in columns:
            if isinstance(col, dict):
                col_name = col.get('column_name', col.get('name', 'unknown'))
                col_type = col.get('data_type', col.get('type', 'unknown'))
                semantic = col.get('semantic_type', '')
                
                line = f'  - "{col_name}" ({col_type})'
                if semantic:
                    line += f' - {semantic}'
                formatted.append(line)
            else:
                formatted.append(f'  - "{col}"')
        
        return "\n".join(formatted)
    
    def _enhance_validation(
        self,
        validation: Dict[str, Any],
        question: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance and validate the validation result."""
        # Ensure required fields
        if 'is_valid' not in validation:
            validation['is_valid'] = True
        
        if 'is_answerable' not in validation:
            validation['is_answerable'] = validation['is_valid']
        
        if 'confidence' not in validation:
            validation['confidence'] = 0.7
        
        if 'required_columns' not in validation:
            validation['required_columns'] = []
        
        if 'missing_columns' not in validation:
            validation['missing_columns'] = []
        
        if 'reason' not in validation:
            if validation['is_valid']:
                validation['reason'] = "Question can be answered with available data"
            else:
                validation['reason'] = "Question cannot be answered with available data"
        
        if 'suggestion' not in validation and not validation['is_valid']:
            validation['suggestion'] = "Try asking about available columns in the dataset"
        
        return validation
    
    def _fallback_validation(self, question: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback validation when LLM fails."""
        # Simple heuristic: if question mentions data-related words, it's probably valid
        data_keywords = [
            'total', 'average', 'sum', 'count', 'show', 'list', 'top', 'bottom',
            'trend', 'compare', 'sales', 'revenue', 'customer', 'product', 'order'
        ]
        
        question_lower = question.lower()
        has_data_keyword = any(keyword in question_lower for keyword in data_keywords)
        
        return {
            'is_valid': has_data_keyword,
            'is_answerable': has_data_keyword,
            'confidence': 0.6,
            'required_columns': [],
            'missing_columns': [],
            'reason': "Validation performed using fallback heuristics",
            'suggestion': None if has_data_keyword else "Please ask a question about the data"
        }


# Global instance
question_validator = QuestionValidator()
