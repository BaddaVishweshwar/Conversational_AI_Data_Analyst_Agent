
import logging
import os
from openai import OpenAI
from typing import Optional, Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)

class GitHubService:
    """
    Service to interact with GitHub Models (e.g., GPT-4o) via OpenAI-compatible API.
    """
    def __init__(self):
        self.api_key = settings.GITHUB_TOKEN
        self.model_name = settings.GITHUB_MODEL or "gpt-4o"
        self.base_url = "https://models.inference.ai.azure.com"
        self.client = None
        self._initialized = False

        if self.api_key:
            try:
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                )
                logger.info(f"🚀 Initialized GitHubService with model: {self.model_name}")
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize GitHubService: {e}")

    def check_availability(self) -> bool:
        return self._initialized and self.client is not None

    def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        task_type: str = "general"
    ) -> str:
        """
        Generate response using GitHub Models.
        Matches the signature of OllamaService.generate_response for compatibility.
        """
        if not self.check_availability():
            logger.error("GitHubService is not available")
            return "Error: GitHub Models service is not configured."

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})

            response_format = {"type": "json_object"} if json_mode else None

            logger.info(f"🤖 Sending request to GitHub Models ({self.model_name})...")
            
            # Note: GitHub Models (Azure) usually supports 'json_object' for GPT-4o
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )

            response_content = completion.choices[0].message.content
            logger.info("✅ Received response from GitHub Models")
            return response_content

        except Exception as e:
            logger.error(f"GitHub Models generation failed: {e}")
            return f"Error generating response: {str(e)}"

# Singleton instance
github_service = GitHubService()
