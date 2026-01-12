"""
SQL Generation Agent - CamelAI-Grade SQL Query Generation

This agent generates production-ready SQL queries using:
- Chain-of-thought reasoning
- Few-shot learning with high-quality examples
- DuckDB-specific optimizations
- Comprehensive error handling
- Professional SQL best practices
"""

from typing import Dict, Any, Optional, List
import logging
import re
from ..services.ollama_service import ollama_service
from ..prompts.sql_system_prompts import SQL_GENERATION_SYSTEM_PROMPT
from ..prompts.few_shot_examples import get_examples_by_intent, format_examples_for_prompt
from ..prompts.chain_of_thought_templates import COT_SQL_GENERATION_TEMPLATE
from ..config import settings

logger = logging.getLogger(__name__)



class SQLGenerationAgent:
    """Agent for generating professional SQL queries"""
    
    def __init__(self):
        """Initialize the SQL generation agent"""
        self.system_prompt = SQL_GENERATION_SYSTEM_PROMPT
    
    async def generate_sql(
        self,
        user_question: str,
        schema_context: Dict[str, Any],
        query_analysis: Dict[str, Any],
        similar_queries: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query for the user's question.
        
        Args:
            user_question: The user's natural language question
            schema_context: Schema information from RAG
            query_analysis: Analysis from Query Understanding Agent
            similar_queries: Similar successful queries for few-shot learning
            
        Returns:
            Dictionary with generated SQL and metadata
        """
        try:
            # Build comprehensive context
            context = self._build_context(
                user_question,
                schema_context,
                query_analysis,
                similar_queries
            )
            
            # Generate SQL using Claude
            if settings.ENABLE_CHAIN_OF_THOUGHT:
                sql_response = await self._generate_with_cot(context)
            else:
                sql_response = await self._generate_direct(context)
            
            # Extract and clean SQL
            sql = self._extract_sql(sql_response)
            
            # Validate SQL structure
            validation = self._validate_sql_structure(sql)
            
            result = {
                "sql": sql,
                "raw_response": sql_response,
                "validation": validation,
                "success": validation["is_valid"],
                "reasoning": self._extract_reasoning(sql_response) if settings.ENABLE_CHAIN_OF_THOUGHT else None
            }
            
            logger.info(f"SQL generation complete. Valid: {validation['is_valid']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in SQL generation: {str(e)}")
            return {
                "sql": None,
                "success": False,
                "error": str(e)
            }
    
    def _build_context(
        self,
        user_question: str,
        schema_context: Dict[str, Any],
        query_analysis: Dict[str, Any],
        similar_queries: List[Dict[str, Any]]
    ) -> str:
        """Build comprehensive context for SQL generation"""
        context_parts = []
        
        # User question and intent
        context_parts.append(f"**User Question:** {user_question}")
        context_parts.append(f"**Intent:** {query_analysis.get('intent', 'DESCRIPTIVE')}")
        context_parts.append(f"**Interpretation:** {query_analysis.get('interpretation', user_question)}")
        context_parts.append("")
        
        # Schema information
        context_parts.append("**Available Schema:**")
        context_parts.append("Table: data")
        context_parts.append("Columns:")
        
        for col in schema_context.get('relevant_columns', [])[:20]:
            col_line = f"- \"{col['column_name']}\" ({col['data_type']})"
            if col.get('business_name'):
                col_line += f" - {col['business_name']}"
            if col.get('description'):
                col_line += f": {col['description']}"
            
            # Add profile information if available
            if col.get('profile'):
                profile = col['profile']
                stats = []
                if profile.get('min_value'):
                    stats.append(f"min={profile['min_value']}")
                if profile.get('max_value'):
                    stats.append(f"max={profile['max_value']}")
                if profile.get('unique_count'):
                    stats.append(f"unique={profile['unique_count']}")
                if stats:
                    col_line += f" [{', '.join(stats)}]"
            
            context_parts.append(col_line)
        
        context_parts.append("")
        
        # Similar queries for few-shot learning
        if similar_queries and len(similar_queries) > 0:
            context_parts.append("**Similar Successful Queries (for reference):**")
            for i, query in enumerate(similar_queries[:3], 1):
                context_parts.append(f"\nExample {i}:")
                context_parts.append(f"Question: {query.get('natural_language', '')}")
                context_parts.append(f"SQL:")
                context_parts.append(f"```sql")
                context_parts.append(query.get('sql_query', ''))
                context_parts.append(f"```")
            context_parts.append("")
        
        # Required columns (from query analysis)
        if query_analysis.get('required_columns'):
            context_parts.append("**Required Columns:**")
            for col in query_analysis['required_columns']:
                context_parts.append(f"- {col}")
            context_parts.append("")
        
        # Task
        context_parts.append("**Task:**")
        context_parts.append("Generate a DuckDB SQL query to answer the user's question.")
        context_parts.append("Follow all the rules and best practices from the system prompt.")
        context_parts.append("Return ONLY the SQL query, properly formatted and ready to execute.")
        
        return "\n".join(context_parts)
    
    async def _generate_with_cot(self, context: str) -> str:
        """Generate SQL with chain-of-thought reasoning and few-shot examples"""
        # Extract intent from context for few-shot selection
        intent = "DESCRIPTIVE"  # default
        if "**Intent:**" in context:
            intent_line = [line for line in context.split('\n') if '**Intent:**' in line]
            if intent_line:
                intent = intent_line[0].split('**Intent:**')[1].strip()
        
        # Get relevant few-shot examples based on intent
        examples = get_examples_by_intent(intent, limit=3)
        few_shot_text = format_examples_for_prompt(examples)
        
        # Extract question and schema from context
        question = ""
        schema = ""
        if "**User Question:**" in context:
            question_line = [line for line in context.split('\n') if '**User Question:**' in line]
            if question_line:
                question = question_line[0].split('**User Question:**')[1].strip()
        
        if "**Available Schema:**" in context:
            schema_start = context.find("**Available Schema:**")
            schema_end = context.find("**", schema_start + 20)
            if schema_end == -1:
                schema = context[schema_start:]
            else:
                schema = context[schema_start:schema_end]
        
        # Build CoT prompt with few-shot examples
        cot_prompt = f"""{self.system_prompt}

{few_shot_text}

Now, generate SQL for this new question:

**User Question:** {question}

{schema}

Think step-by-step:
1. What is the user asking?
2. Which columns are needed?
3. What operations (aggregation, filtering, sorting)?
4. What is the SQL structure?

Then provide ONLY the SQL query:
"""
        
        response = await ollama_service.generate(
            system_prompt="You are an expert SQL analyst. Generate accurate DuckDB SQL queries.",
            user_prompt=cot_prompt,
            temperature=0.1,  # CamelAI-grade: very deterministic
            task_type='sql_generation',
            max_tokens=2000
        )
        
        return response
    
    async def _generate_direct(self, context: str) -> str:
        """Generate SQL directly with few-shot examples but without explicit CoT"""
        # Extract intent from context
        intent = "DESCRIPTIVE"
        if "**Intent:**" in context:
            intent_line = [line for line in context.split('\n') if '**Intent:**' in line]
            if intent_line:
                intent = intent_line[0].split('**Intent:**')[1].strip()
        
        # Get relevant few-shot examples
        examples = get_examples_by_intent(intent, limit=2)
        few_shot_text = format_examples_for_prompt(examples)
        
        # Build prompt with examples
        full_prompt = f"""{self.system_prompt}

{few_shot_text}

Now generate SQL for:

{context}
"""
        
        response = await ollama_service.generate(
            system_prompt="You are an expert SQL analyst.",
            user_prompt=full_prompt,
            temperature=0.1,  # CamelAI-grade: deterministic
            task_type='sql_generation',
            max_tokens=1500
        )
        
        return response

    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL from the response"""
        # Try to find SQL in code blocks
        sql_pattern = r'```sql\s*(.*?)\s*```'
        matches = re.findall(sql_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            # Return the last SQL block (most likely the final query)
            return matches[-1].strip()
        
        # If no code blocks, try to find SQL keywords
        # Look for SELECT, WITH, INSERT, UPDATE, DELETE
        sql_keywords = r'(WITH|SELECT|INSERT|UPDATE|DELETE)\s+'
        if re.search(sql_keywords, response, re.IGNORECASE):
            # Extract from first SQL keyword to end or until non-SQL content
            match = re.search(sql_keywords, response, re.IGNORECASE)
            if match:
                sql = response[match.start():].strip()
                # Remove any trailing markdown or text after the query
                sql = re.split(r'\n\n[A-Z]', sql)[0]
                return sql.strip()
        
        # Fallback: return the whole response
        return response.strip()
    
    def _extract_reasoning(self, response: str) -> Optional[str]:
        """Extract reasoning from chain-of-thought response"""
        reasoning_pattern = r'```reasoning\s*(.*?)\s*```'
        matches = re.findall(reasoning_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        return None
    
    def _validate_sql_structure(self, sql: str) -> Dict[str, Any]:
        """Basic validation of SQL structure"""
        if not sql:
            return {
                "is_valid": False,
                "errors": ["No SQL generated"]
            }
        
        errors = []
        warnings = []
        
        # Check for basic SQL keywords
        if not re.search(r'\b(SELECT|WITH)\b', sql, re.IGNORECASE):
            errors.append("SQL must contain SELECT or WITH clause")
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            errors.append("Unbalanced parentheses")
        
        # Check for quoted column names (best practice)
        if re.search(r'SELECT\s+[a-zA-Z_][a-zA-Z0-9_]*\s*,', sql) and '"' not in sql:
            warnings.append("Consider using quoted column names for clarity")
        
        # Check for table alias
        if 'FROM data' in sql and not re.search(r'FROM\s+data\s+[a-zA-Z]', sql, re.IGNORECASE):
            warnings.append("Consider using table alias for clarity")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# Global instance
sql_generation_agent = SQLGenerationAgent()
