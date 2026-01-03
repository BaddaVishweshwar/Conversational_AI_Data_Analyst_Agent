import ollama
from typing import Dict, Any, Optional, List
import json
import re
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Task-specific temperature configurations (CamelAI-grade)
TEMPERATURE_CONFIG = {
    'planning': 0.5,           # Creative but structured
    'exploratory': 0.3,        # Focused exploration
    'sql_generation': 0.1,     # Very precise for SQL
    'insight_generation': 0.7, # More creative writing
    'visualization': 0.4,      # Balanced selection
    'error_correction': 0.2    # Precise debugging
}

# Context configuration for larger prompts
CONTEXT_CONFIG = {
    'num_ctx': 8192,      # Large context window
    'num_predict': 2048   # Allow longer responses
}

class OllamaService:
    """
    Ollama LLM Service.
    Uses local Ollama models for all LLM operations.
    """
    
    def __init__(self):
        self.provider = "ollama"
        self.model_name = settings.OLLAMA_MODEL
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        logger.info(f"🦙 Using Ollama Provider: {self.model_name}")


    def check_availability(self) -> bool:
        """Check if Ollama service is available"""
        return True


    def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.7,
        task_type: Optional[str] = None
    ) -> str:
        """
        Generate LLM response using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            json_mode: Whether to request JSON output
            temperature: Temperature override (optional)
            task_type: Task type for automatic temperature selection (planning, sql_generation, etc.)
        """
        # Use task-specific temperature if provided
        if task_type and task_type in TEMPERATURE_CONFIG:
            temperature = TEMPERATURE_CONFIG[task_type]
            logger.debug(f"Using task-specific temperature for {task_type}: {temperature}")
        
        # Ollama Implementation with enhanced context
        options = {
            "temperature": temperature,
            "num_ctx": CONTEXT_CONFIG['num_ctx'],
            "num_predict": CONTEXT_CONFIG['num_predict']
        }
        if json_mode:
            options["format"] = "json"
            
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        response = self.client.generate(
            model=self.model_name,
            prompt=full_prompt,
            options=options
        )
        return response['response']

    
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
        Many agents call .generate() instead of .generate_response().
        """
        return self.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=json_mode,
            temperature=temperature,
            task_type=task_type
        )

    # ------------------------------------------------------------------
    # Legacy Methods (Refactored to use generic generate_response)
    # ------------------------------------------------------------------

    def generate_analysis_plan(
        self, 
        natural_query: str, 
        schema: Dict[str, Any],
        sample_data: list,
        related_expertise: list = []
    ) -> Dict[str, Any]:
        """Generate a professional analysis plan"""
        
        schema_desc = self._format_schema(schema)
        sample_desc = self._format_sample_data(sample_data)
        
        expertise_desc = ""
        if related_expertise:
            expertise_desc = "\nExamples of past successful queries:\n"
            for exp in related_expertise:
                expertise_desc += f"User: {exp['query']}\nSQL:\n```sql\n{exp['sql']}\n```\n"
        
        system_prompt = "You are a Senior Data Analyst with expertise in SQL and data visualization. Provide accurate, well-reasoned analysis."
        prompt = f"""
Analyze this data and answer the user's question with ACCURATE results.

**SCHEMA:**
{schema_desc}

**SAMPLE DATA:**
{sample_desc}
{expertise_desc}

**USER QUESTION:** {natural_query}

**CRITICAL SQL RULES:**
1. ALWAYS use double quotes around column names: "Column Name"
2. For aggregations (sum, average, count), use proper GROUP BY
3. For "total" questions, use SUM() aggregation
4. For "average" questions, use AVG() aggregation  
5. For "top N" questions, use ORDER BY ... DESC LIMIT N
6. Double-check your SQL logic before outputting
7. Limit results to 500 rows maximum

**VISUALIZATION REQUIREMENTS (MANDATORY):**
You MUST generate Python visualization code. Follow these exact steps:

1. Import matplotlib if needed: `import matplotlib.pyplot as plt`
2. Use the provided 'ax' object (DO NOT create new figure)
3. Choose appropriate chart type based on data
4. Add labels, title, and formatting

**WORKING EXAMPLES:**

For comparing multiple columns (like TV, Radio, Newspaper budgets):
```python
import matplotlib.pyplot as plt
import numpy as np

# Prepare data for grouped bar chart
categories = ['TV', 'Radio', 'Newspaper']
values = [df["TV Ad Budget ($)"].mean(), df["Radio Ad Budget ($)"].mean(), df["Newspaper Ad Budget ($)"].mean()]

# Create bar chart
bars = ax.bar(categories, values, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
ax.set_ylabel('Average Budget ($)')
ax.set_title('Average Ad Budgets by Channel')
ax.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'${height:.1f}',
            ha='center', va='bottom')
```

For scatter plots (relationship between two variables):
```python
import matplotlib.pyplot as plt

ax.scatter(df["TV Ad Budget ($)"], df["Sales ($)"], alpha=0.6, s=50)
ax.set_xlabel('TV Ad Budget ($)')
ax.set_ylabel('Sales ($)')
ax.set_title('TV Ad Budget vs Sales')
ax.grid(True, alpha=0.3)
```

For top N items:
```python
import matplotlib.pyplot as plt

# Get top 10 rows
top_data = df.head(10)
ax.barh(range(len(top_data)), top_data.iloc[:, 1])
ax.set_yticks(range(len(top_data)))
ax.set_yticklabels(top_data.iloc[:, 0])
ax.set_xlabel(df.columns[1])
ax.set_title('Top 10 Items')
ax.grid(axis='x', alpha=0.3)
```

**OUTPUT FORMAT:**
SQL:
```sql
-- Example: For "visualize TV, Radio, Newspaper with Sales"
SELECT "TV Ad Budget ($)", "Radio Ad Budget ($)", "Newspaper Ad Budget ($)", "Sales ($)"
FROM data
LIMIT 200
```

PYTHON:
```python
# Data cleaning (if needed)
df = df.dropna()

# Visualization (REQUIRED - always create a chart)
import matplotlib.pyplot as plt
ax.bar(df.iloc[:, 0], df.iloc[:, 1])
ax.set_xlabel(df.columns[0])
ax.set_ylabel(df.columns[1])
ax.set_title("{natural_query}")
plt.xticks(rotation=45, ha='right')
ax.grid(axis='y', alpha=0.3)
```
"""
        try:
            full_text = self.generate_response(prompt, system_prompt=system_prompt, temperature=0.1)
            
            sql_query = self._extract_sql(full_text)
            python_code = self._extract_python(full_text)
            
            return {
                "success": True,
                "sql": sql_query,
                "python": python_code,
                "error": None
            }
        except Exception as e:
            return {"success": False, "sql": None, "python": None, "error": str(e)}

    def generate_eda_report(
        self,
        schema: Dict[str, Any],
        sample_data: list
    ) -> Dict[str, Any]:
        """Generate a comprehensive EDA report"""
        schema_desc = self._format_schema(schema)
        sample_desc = self._format_sample_data(sample_data)
        
        system_prompt = "You are a Lead Data Scientist. Perform a comprehensive Exploratory Data Analysis (EDA)."
        prompt = f"""
Dataset Schema:
{schema_desc}

Sample Data:
{sample_desc}

Provide a structured EDA report and Python code for key visualizations.
You are provided with a pandas DataFrame 'df' and a matplotlib axis 'ax'.
DO NOT create new figures or axes. Use 'ax'.

Output Format:
REPORT:
- Data Overview
- Potential Data Quality Issues
- Key Correlations
- Recommended Cleaning steps

PYTHON:
```python
# Cleaning (if needed on df)
# Plotting (on ax)
```
"""
        try:
            full_text = self.generate_response(prompt, system_prompt=system_prompt, temperature=0.2)
            
            report = full_text.split("PYTHON:")[0].replace("REPORT:", "").strip()
            python_code = self._extract_python(full_text)
            
            return {
                "success": True,
                "report": report,
                "python": python_code,
                "error": None
            }
        except Exception as e:
            return {"success": False, "report": None, "python": None, "error": str(e)}

    def generate_insights(
        self,
        query: str,
        result_data: list,
        chart_type: Optional[str] = None
    ) -> str:
        """Generate high-level business insights"""
        
        limited_data = result_data[:10] # Larger context allowed for GPT
        
        system_prompt = "You are a Management Consultant."
        prompt = f"""
Provide a sharp, executive summary of this data.

**CONTEXT**
User Question: "{query}"
Data Preview: {json.dumps(limited_data, default=str)}

**INSTRUCTIONS**
1. **EXECUTIVE SUMMARY**: 1-2 sentence high-level takeaway.
2. **KEY FINDINGS**: Detailed bulleted list with bold emphasis.
3. **METRIC SUMMARY TABLE**: Clean Markdown table for key numbers.
4. **ACTIONABLE RECOMMENDATIONS**: Specific steps based on data.

Format Structure:
### 📊 Executive Summary
<summary>

### 🔍 Key Findings
- **<point>**: <detail>

### 📈 Metric Summary
| Dimension | Metric |
| :--- | :--- |
| ... | ... |

### 💡 Recommendations
- **<step>**: <reason>
"""
        try:
             return self.generate_response(prompt, system_prompt=system_prompt, temperature=0.3)
        except Exception as e:
            return "Insights unavailable."

    # ------------------------------------------------------------------
    # Compatibility Layer for Agents
    # Agents call client.generate(model=..., prompt=..., options=...) directly
    # We must patch this if using OpenAI
    # ------------------------------------------------------------------
    
    def generate(self, model: str, prompt: str, options: dict = None) -> Dict[str, str]:
        """
        Compatibility method to mimic ollama.generate signature.
        Used by the new agent system (SchemaAnalyzer, QueryPlanner, etc.)
        """
        temp = options.get("temperature", 0.7) if options else 0.7
        
        # Check if json mode is requested via options or prompt
        json_mode = False
        if options and options.get("format") == "json":
            json_mode = True
        
        response_text = self.generate_response(prompt, temperature=temp, json_mode=json_mode)
        
        # Return in Ollama format: {'response': '...'}
        return {'response': response_text}

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a named section (e.g., 'STRATEGY:') from text"""
        if section_name not in text:
            return ""
        
        parts = text.split(section_name)
        if len(parts) < 2:
            return ""
            
        content = parts[1].split("\n\n")[0].split("SQL:")[0].split("PYTHON:")[0].strip()
        return content

    def _format_schema(self, schema: Dict[str, Any]) -> str:
        return "\n".join([f"  - {k}: {v}" for k, v in schema.items()])
    
    def _format_sample_data(self, sample_data: list) -> str:
        return json.dumps(sample_data[:3], indent=2)

    def _extract_sql(self, text: str) -> str:
        matches = re.findall(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[-1].strip()
            
        # Fallback: Look for raw SELECT statement
        select_pattern = r"(SELECT\s+[\s\S]+?\s+FROM\s+[\s\S]+?;)"
        raw_matches = re.findall(select_pattern, text, re.IGNORECASE)
        if raw_matches:
             return raw_matches[-1].strip()

        # SUPER FALLBACK: Find "SELECT" case-insensitive
        parts = re.split(r"SELECT\s", text, flags=re.IGNORECASE)
        if len(parts) > 1:
            return ("SELECT " + parts[-1]).strip()

        return text.strip()

    def _extract_python(self, text: str) -> str:
        import textwrap
        python_section = text.split("PYTHON:")[-1] if "PYTHON:" in text else text
        matches = re.findall(r"```(?:python)?\s*(.*?)\s*```", python_section, re.DOTALL | re.IGNORECASE)
        return textwrap.dedent(matches[0]).strip() if matches else ""

# Singleton instance
ollama_service = OllamaService()
