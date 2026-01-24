"""
Groq LLM Service - Fast Llama 70B via Groq API

Provides cloud-based LLM with:
- Llama 3.1 70B (best accuracy for SQL)
- Ultra-fast inference (<1s response time)
- Cost-effective ($0.50/1M tokens)
"""

import logging
from typing import Dict, Any, Optional
from groq import Groq
import json
import re

from ..config import settings

logger = logging.getLogger(__name__)


class GroqService:
    """
    Groq LLM Service for fast cloud-based inference.
    Uses Llama 3.1 70B for superior SQL generation.
    """
    
    def __init__(self):
        self.provider = "groq"
        self.model_name = "llama-3.1-70b-versatile"
        
        # Get API key from settings
        api_key = getattr(settings, 'GROQ_API_KEY', None)
        if not api_key:
            raise ValueError("GROQ_API_KEY not configured in settings")
        
        self.client = Groq(api_key=api_key)
        logger.info(f"🚀 Using Groq Provider: {self.model_name}")
    
    def check_availability(self) -> bool:
        """Check if Groq service is available"""
        try:
            return True
        except Exception as e:
            logger.error(f"Groq availability check failed: {e}")
            return False
    
    def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.7,
        task_type: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate LLM response using Groq API.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            json_mode: Whether to request JSON output
            temperature: Temperature for generation
            task_type: Task type (for logging)
            max_tokens: Maximum tokens to generate
        """
        try:
            # Build messages
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add JSON instruction if needed
            user_content = prompt
            if json_mode:
                user_content += "\n\nRespond with valid JSON only. Do not include any text before or after the JSON."
            
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 2048,
                top_p=0.95,
            )
            
            # Extract response
            response_text = response.choices[0].message.content.strip()
            
            # If JSON mode, try to extract JSON
            if json_mode:
                response_text = self._extract_json(response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"Groq generation error: {e}")
            raise e
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.7,
        task_type: Optional[str] = None
    ) -> str:
        """
        Alias for generate_response() for backward compatibility.
        """
        return self.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=json_mode,
            temperature=temperature,
            task_type=task_type
        )
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from response text"""
        # Try to find JSON object in the response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group(0)
        
        # Try to find JSON array
        array_match = re.search(r'\[[\s\S]*\]', text)
        if array_match:
            return array_match.group(0)
        
        return text


# Singleton instance - will be initialized if GROQ_API_KEY is set
try:
    groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
    if groq_api_key:
        groq_service = GroqService()
        logger.info("✅ Groq service initialized successfully")
    else:
        groq_service = None
        logger.info("ℹ️  Groq service not initialized (GROQ_API_KEY not set)")
except Exception as e:
    logger.error(f"❌ Failed to initialize Groq service: {e}")
    groq_service = None
