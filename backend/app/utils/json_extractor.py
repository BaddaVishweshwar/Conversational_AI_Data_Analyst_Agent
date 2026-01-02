"""
Robust JSON Extraction Utility

Handles common LLM output formatting issues:
- Markdown code blocks (```json, ```)
- Extra text before/after JSON
- Multiple JSON objects
- Malformed JSON
"""
import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def extract_json_from_llm_response(text: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Robustly extract JSON from LLM responses that may contain markdown, extra text, etc.
    
    Args:
        text: Raw LLM response text
        fallback: Default dict to return if extraction fails
    
    Returns:
        Parsed JSON dict
    
    Raises:
        ValueError: If JSON cannot be extracted and no fallback provided
    """
    if not text or not text.strip():
        if fallback is not None:
            return fallback
        raise ValueError("Empty LLM response")
    
    original_text = text
    text = text.strip()
    
    # Strategy 1: Try direct JSON parse (best case)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Remove markdown code blocks
    # Handle ```json ... ``` or ``` ... ```
    if "```" in text:
        # Extract content between code fences
        matches = re.findall(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
    
    # Strategy 3: Find JSON object by braces
    # Look for outermost { ... }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON extraction failed: {e}")
            logger.debug(f"Attempted to parse: {json_candidate[:200]}...")
    
    # Strategy 4: Try to find JSON array
    first_bracket = text.find('[')
    last_bracket = text.rfind(']')
    
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        json_candidate = text[first_bracket:last_bracket + 1]
        try:
            result = json.loads(json_candidate)
            # Wrap array in object if expected
            if isinstance(result, list) and fallback and isinstance(fallback, dict):
                # Guess the key from fallback
                if fallback:
                    first_key = list(fallback.keys())[0]
                    return {first_key: result}
                return {"items": result}
            return result
        except json.JSONDecodeError:
            pass
    
    # Strategy 5: Try to clean up common issues
    # Remove leading/trailing non-JSON text (common LLM behavior)
    lines = text.split('\n')
    json_lines = []
    in_json = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('{') or stripped.startswith('['):
            in_json = True
        if in_json:
            json_lines.append(line)
        if stripped.endswith('}') or stripped.endswith(']'):
            # Try to parse accumulated lines
            potential_json = '\n'.join(json_lines)
            try:
                return json.loads(potential_json)
            except json.JSONDecodeError:
                pass
    
    # All strategies failed
    logger.error(f"Failed to extract JSON from LLM response. Text: {original_text[:500]}...")
    
    if fallback is not None:
        logger.warning(f"Returning fallback: {fallback}")
        return fallback
    
    raise ValueError(f"Could not extract valid JSON from response: {original_text[:200]}...")


def safe_json_parse(text: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Alias for extract_json_from_llm_response for backwards compatibility.
    """
    return extract_json_from_llm_response(text, fallback)
