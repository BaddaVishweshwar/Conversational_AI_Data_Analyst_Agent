import ollama
from typing import Dict, Any, List, Optional
import json
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class QueryResolverAgent:
    """
    Resolves contextual queries using LLM to rewrite them into standalone queries.
    Handles:
    - Pronoun resolution ("it", "that")
    - Follow-up context ("what about 2023?")
    - Implicit references
    """
    
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model_name = settings.OLLAMA_MODEL

    def resolve_query(
        self,
        current_query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve a query using conversation context via LLM
        
        Args:
            current_query: The user's current query
            context: Conversation context containing history
            
        Returns:
            Dict with 'resolved_query', 'intent', 'is_followup'
        """
        
        # history is a list of {"role": "user/assistant", "content": "..."}
        history = context.get('history', [])
        last_query = context.get('last_query')
        
        # If no history, it's a new query
        if not history and not last_query:
            return {
                'is_followup': False,
                'resolved_query': current_query,
                'intent': 'new_query',
                'references_previous': False
            }

        # Format history for prompt (limit to last 5 turns to save context window)
        formatted_history = ""
        recent_history = history[-5:] if history else []
        
        if last_query and not recent_history:
            # Fallback if history object structure is different
             formatted_history = f"User: {last_query}\nAssistant: (Previous Analysis)"
        else:
            for msg in recent_history:
                role = "User" if msg.get('role') == 'user' else "Assistant"
                content = msg.get('content', '')
                # Truncate long assistant responses
                if role == "Assistant" and len(content) > 200:
                    content = content[:200] + "...(truncated)"
                formatted_history += f"{role}: {content}\n"

        prompt = f"""You are a helpful conversation context resolver. 
Your task is to REWRITE the "Current User Query" into a standalone, unambiguous query that includes all necessary context from the conversation history.

CONVERSATION HISTORY:
{formatted_history}

CURRENT USER QUERY: "{current_query}"

INSTRUCTIONS:
1. If the current query depends on previous context (e.g., "what about for 2023?", "show me the code", "sort it by date"), rewrite it to be fully self-contained.
2. If the current query uses pronouns like "it", "that", "them", replace them with the actual referenced entities.
3. If the current query is completely new and unrelated, keep it as is.
4. If the user asks to "visualize" or "chart" the previous result, explicitly state "Visualize the data from the previous result as a [chart type]".
5. Output valid JSON only.

OUTPUT FORMAT (JSON):
{{
    "resolved_query": "The fully rewritten standalone query",
    "is_followup": true/false,
    "intent": "refinement|new_topic|visualization|explanation"
}}

Respond with ONLY the JSON."""

        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 256}
            )
            
            result_text = response['response'].strip()
            
            # Clean up markdown if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                
            # Parse JSON
            result_data = json.loads(result_text)
            
            resolved = result_data.get("resolved_query", current_query)
            is_followup = result_data.get("is_followup", False)
            intent = result_data.get("intent", "new_topic")
            
            logger.info(f"Context Resolution: '{current_query}' -> '{resolved}' (Intent: {intent})")
            
            return {
                'is_followup': is_followup,
                'resolved_query': resolved,
                'intent': intent,
                'references_previous': is_followup,
                'original_query': current_query
            }
            
        except Exception as e:
            logger.error(f"Context resolution failed: {e}")
            # Fallback to original query
            return {
                'is_followup': False,
                'resolved_query': current_query,
                'intent': 'new_query',
                'references_previous': False,
                'error': str(e)
            }

# Singleton instance
query_resolver = QueryResolverAgent()
