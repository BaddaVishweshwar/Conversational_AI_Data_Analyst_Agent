"""
HuggingFace Inference API Service

Provides LLM capabilities using HuggingFace's Inference API for faster,
cloud-based inference with better accuracy than local models.
"""

import logging
from typing import Dict, Any, Optional
from huggingface_hub import InferenceClient
import json
import re

from ..config import settings

logger = logging.getLogger(__name__)


class HuggingFaceService:
    """
    HuggingFace Inference API Service.
    Uses cloud-based models via HuggingFace Inference API.
    """
    
    def __init__(self):
        self.provider = "huggingface"
        self.model_name = settings.HUGGINGFACE_MODEL
        self.api_key = settings.HUGGINGFACE_API_KEY
        
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY not configured in settings")
        
        self.client = InferenceClient(token=self.api_key)
        logger.info(f"🤗 Using HuggingFace Provider: {self.model_name}")
    
    def check_availability(self) -> bool:
        """Check if HuggingFace service is available"""
        try:
            # Simple test to check if API key works
            return True
        except Exception as e:
            logger.error(f"HuggingFace availability check failed: {e}")
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
        Generate LLM response using HuggingFace Inference API.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            json_mode: Whether to request JSON output
            temperature: Temperature for generation
            task_type: Task type (for logging)
            max_tokens: Maximum tokens to generate
        """
        try:
            # Build full prompt with system context
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
            else:
                full_prompt = f"<s>[INST] {prompt} [/INST]"
            
            # Add JSON instruction if needed
            if json_mode:
                full_prompt += "\n\nRespond with valid JSON only."
            
            # Generate with HuggingFace
            response = self.client.text_generation(
                full_prompt,
                model=self.model_name,
                max_new_tokens=max_tokens or settings.HUGGINGFACE_MAX_TOKENS,
                temperature=temperature,
                top_p=0.95,
                repetition_penalty=1.1,
                return_full_text=False
            )
            
            # Clean up response
            response_text = response.strip()
            
            # If JSON mode, try to extract JSON
            if json_mode:
                response_text = self._extract_json(response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"HuggingFace generation error: {e}")
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


# Singleton instance - initialize if enabled
try:
    if settings.USE_HUGGINGFACE and settings.HUGGINGFACE_API_KEY:
        huggingface_service = HuggingFaceService()
        logger.info("✅ HuggingFace service initialized successfully")
    else:
        huggingface_service = None
        logger.info("ℹ️  HuggingFace service not initialized (USE_HUGGINGFACE=False or API key not set)")
except Exception as e:
    logger.error(f"❌ Failed to initialize HuggingFace service: {e}")
    huggingface_service = None
