from typing import Dict, Any, Optional, List
import anthropic
import json
import logging
from ..config import settings
import asyncio

logger = logging.getLogger(__name__)

class AnthropicService:
    """
    Anthropic Claude Service for high-quality reasoning and generation.
    """
    
    def __init__(self):
        self.client = None
        self.model = settings.ANTHROPIC_MODEL
        self._initialized = False
        
    def _ensure_initialized(self):
        if not self._initialized:
            if not settings.ANTHROPIC_API_KEY:
                logger.warning("Anthropic API Key not found. Service will fail if used.")
                return
                
            try:
                self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                self._initialized = True
                logger.info(f"✅ Anthropic Service initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

    def check_availability(self) -> bool:
        self._ensure_initialized()
        return self.client is not None

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        task_type: Optional[str] = None
    ) -> str:
        """
        Generate response using Claude.
        """
        self._ensure_initialized()
        if not self.client:
            raise ValueError("Anthropic client not initialized. Check API Key.")

        try:
            # Adjust temperature based on task
            if task_type == "sql_generation":
                temperature = 0.1 # Precise
            elif task_type == "insight_generation":
                temperature = 0.5 # Creative
            
            system = system_prompt or "You are a helpful AI assistant."
            
            if json_mode:
                system += "\nOutput your response in valid JSON format."
                # Claude doesn't have a strict 'json_object' mode like OpenAI, 
                # but instruction following is high.
            
            # Use to_thread for blocking API call
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise e

# Global instance
anthropic_service = AnthropicService()
