"""
Query Resolver Agent - Resolves contextual queries using conversation history

Handles:
- Follow-up queries like "draw it in chart", "show more", "what about X?"
- Pronoun resolution ("it", "that", "the data")
- Implicit references to previous queries/results
- Command detection ("draw", "show", "export", "visualize")
"""
from typing import Dict, Any, Optional
import re


class QueryResolverAgent:
    """Resolves contextual queries using conversation history"""
    
    # Commands that reference previous results
    VISUALIZATION_COMMANDS = [
        "draw", "plot", "chart", "graph", "visualize", "show chart",
        "create chart", "make chart", "display chart"
    ]
    
    FORMAT_COMMANDS = [
        "show as", "display as", "format as", "convert to",
        "in tabular format", "as a table", "as a list"
    ]
    
    REFERENCE_PRONOUNS = [
        "it", "that", "this", "these", "those", "them"
    ]
    
    def resolve_query(
        self,
        current_query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve a query using conversation context
        
        Args:
            current_query: The user's current query
            context: Conversation context from conversation_service
            
        Returns:
            {
                'is_followup': bool,
                'resolved_query': str,  # Standalone query with context merged
                'intent': str,  # 'visualization', 'format_change', 'new_query', 'clarification'
                'references_previous': bool,
                'previous_query': str,  # If referencing previous
                'previous_result': dict  # If available
            }
        """
        query_lower = current_query.lower().strip()
        
        # Check if it's a follow-up query
        is_followup = self._is_followup_query(query_lower, context)
        
        if not is_followup:
            # It's a new, standalone query
            return {
                'is_followup': False,
                'resolved_query': current_query,
                'intent': 'new_query',
                'references_previous': False,
                'previous_query': None,
                'previous_result': None
            }
        
        # Determine the intent of the follow-up
        intent = self._determine_followup_intent(query_lower)
        
        # Resolve the query based on intent
        resolved_query = self._resolve_followup(
            current_query=current_query,
            intent=intent,
            context=context
        )
        
        return {
            'is_followup': True,
            'resolved_query': resolved_query,
            'intent': intent,
            'references_previous': True,
            'previous_query': context.get('last_query'),
            'previous_result': context.get('last_result'),
            'previous_sql': context.get('last_sql')
        }
    
    def _is_followup_query(self, query_lower: str, context: Dict[str, Any]) -> bool:
        """Determine if query is a follow-up to previous conversation"""
        # No context = can't be a follow-up
        if not context.get('last_query'):
            return False
        
        # Check for visualization commands
        if any(cmd in query_lower for cmd in self.VISUALIZATION_COMMANDS):
            return True
        
        # Check for format commands
        if any(cmd in query_lower for cmd in self.FORMAT_COMMANDS):
            return True
        
        # Check for pronouns at start of query
        words = query_lower.split()
        if words and words[0] in self.REFERENCE_PRONOUNS:
            return True
        
        # Check for very short queries (likely follow-ups)
        if len(words) <= 3 and any(pronoun in words for pronoun in self.REFERENCE_PRONOUNS):
            return True
        
        # Check for questions about previous results
        followup_patterns = [
            r"^(what|which|how|why|when|where).*\b(it|that|this|these|those)\b",
            r"^(show|display|give|tell).*\b(me|us)\b",
            r"^(more|less|other|another)",
            r"^(and|also|additionally)",
        ]
        
        for pattern in followup_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def _determine_followup_intent(self, query_lower: str) -> str:
        """Determine the intent of a follow-up query"""
        # Visualization request
        if any(cmd in query_lower for cmd in self.VISUALIZATION_COMMANDS):
            return 'visualization'
        
        # Format change request
        if any(cmd in query_lower for cmd in self.FORMAT_COMMANDS):
            return 'format_change'
        
        # Clarification/drill-down
        question_words = ['what', 'which', 'how', 'why', 'when', 'where', 'who']
        if any(query_lower.startswith(word) for word in question_words):
            return 'clarification'
        
        # Default to clarification
        return 'clarification'
    
    def _resolve_followup(
        self,
        current_query: str,
        intent: str,
        context: Dict[str, Any]
    ) -> str:
        """Resolve a follow-up query into a standalone query"""
        last_query = context.get('last_query', '')
        
        if intent == 'visualization':
            # "draw it in chart" -> "show [previous query] as a chart"
            return f"{last_query} (visualize as chart)"
        
        elif intent == 'format_change':
            # "show as table" -> "[previous query] in tabular format"
            format_match = re.search(r'(as|in)\s+(a\s+)?(table|list|chart|graph)', current_query.lower())
            if format_match:
                format_type = format_match.group(3)
                return f"{last_query} (format as {format_type})"
            return f"{last_query} (change format)"
        
        elif intent == 'clarification':
            # Replace pronouns with context
            resolved = current_query
            
            # Replace "it", "that", "this" with the subject of previous query
            subject = self._extract_subject(last_query)
            if subject:
                resolved = re.sub(
                    r'\b(it|that|this)\b',
                    subject,
                    resolved,
                    flags=re.IGNORECASE
                )
            
            # If query still seems incomplete, prepend context
            if len(resolved.split()) <= 5:
                resolved = f"{last_query}, specifically: {resolved}"
            
            return resolved
        
        return current_query
    
    def _extract_subject(self, query: str) -> Optional[str]:
        """Extract the main subject from a query"""
        # Simple extraction - look for common patterns
        patterns = [
            r'(products?|sales?|customers?|orders?|revenue|profit|items?)',
            r'(by|for|of|about)\s+(\w+)',
            r'(show|get|find|list)\s+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                # Return the last captured group
                groups = match.groups()
                return groups[-1] if groups else None
        
        return None


# Singleton instance
query_resolver = QueryResolverAgent()
