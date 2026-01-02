import google.generativeai as genai
from typing import Dict, Any, Optional
from ..config import settings
import json
import re


class GeminiService:
    """Service for interacting with Google Gemini LLM"""
    
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model_name = "gemini-flash-latest" # Stable release alias
    
    def check_availability(self) -> bool:
        """Check if Gemini API is configured"""
        return bool(settings.GOOGLE_API_KEY)

    def _generate_with_retry(self, prompt: str, config: genai.GenerationConfig, max_retries: int = 3) -> Any:
        """Generate content with retry logic for transient errors"""
        import time
        import random
        
        last_error = None
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(self.model_name)
                return model.generate_content(prompt, generation_config=config)
            except Exception as e:
                last_error = e
                if "429" in str(e) or "503" in str(e):
                    # Exponential backoff: 1s, 2s, 4s... + jitter
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Gemini API rate limit/error (Attempt {attempt + 1}/{max_retries}). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    # Non-retriable error
                    raise e
        
        raise last_error
    
    def generate_analysis_plan(
        self, 
        natural_query: str, 
        schema: Dict[str, Any],
        sample_data: list,
        related_expertise: list = []
    ) -> Dict[str, Any]:
        """Generate a professional analysis plan: SQL + Python (Cleaning & Viz)"""
        
        schema_desc = self._format_schema(schema)
        sample_desc = self._format_sample_data(sample_data)
        
        expertise_desc = ""
        if related_expertise:
            expertise_desc = "\nHere are some examples of past successful queries for this specific data context:\n"
            for exp in related_expertise:
                expertise_desc += f"User: {exp['query']}\nSQL:\n```sql\n{exp['sql']}\n```\n"
        
        prompt = f"""You are a Senior Data Analyst. Your goal is to answer the user's question with professional-grade analysis.
Follow this workflow:
1. INTENT: Determine if the user wants to see a chart/visualization OR just specific data records/summary statistics.
2. SQL: Write a query to retrieve the raw data needed.
3. CLEANING: Write Python code to clean the retrieved data (handle nulls, types, etc.).
4. VISUALIZATION (OPTIONAL): If the user's intent is a visualization, write Python code to generate a sophisticated, business-ready chart. 
   If they ONLY want a data table or specific rows, leave the VISUALIZATION code block empty.

Dataset Schema:
{schema_desc}

Sample Data (first 3 rows):
{sample_desc}
{expertise_desc}

User Question: {natural_query}

IMPORTANT RULES FOR SQL:
1. Use DuckDB SQL syntax. Table name is 'data'.
2. Return ONLY the SQL query in the SQL block.
3. Limit results to 500 rows for analysis.

IMPORTANT RULES FOR PYTHON (Cleaning & Viz):
1. You are provided with a pandas DataFrame 'df' (from the SQL result) and a matplotlib axis 'ax'.
2. DO NOT create NEW figures or axes. Use 'ax'.
3. DO NOT re-assign 'df'.
4. Perform CLEANING if necessary (e.g., df['col'] = df['col'].fillna(0)).
5. Use SEABORN (sns) for sophisticated styling.
6. IF NO VISUALIZATION IS REQUESTED, LEAVE THE PYTHON BLOCK EMPTY OR JUST CLEANING.

Output Format:
SQL:
```sql
<sql here>
```

PYTHON:
```python
# Cleaning
<cleaning steps if needed>

# Visualization (ONLY IF REQUESTED)
<plotting logic using ax or leave empty>
```
"""

        try:
            response = self._generate_with_retry(
                prompt,
                config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                )
            )
            
            full_text = response.text
            sql_query = self._extract_sql(full_text)
            python_code = self._extract_python(full_text)
            
            return {
                "success": True,
                "sql": sql_query,
                "python": python_code,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "sql": None,
                "python": None,
                "error": str(e)
            }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a named section (e.g., 'STRATEGY:') from text"""
        if section_name not in text:
            return ""
        
        parts = text.split(section_name)
        if len(parts) < 2:
            return ""
            
        content = parts[1].split("\n\n")[0].split("SQL:")[0].split("PYTHON:")[0].strip()
        return content

    def _extract_python(self, text: str) -> str:
        """Extract Python from markdown code blocks"""
        import textwrap
        code_block_pattern = r"```(?:python)?\s*(.*?)\s*```"
        python_section = text.split("PYTHON:")[-1] if "PYTHON:" in text else text
        matches = re.findall(code_block_pattern, python_section, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return textwrap.dedent(matches[0]).strip()
        
        return ""

    def generate_eda_report(
        self,
        schema: Dict[str, Any],
        sample_data: list
    ) -> Dict[str, Any]:
        """Generate a comprehensive EDA report and plotting plan"""
        schema_desc = self._format_schema(schema)
        sample_desc = self._format_sample_data(sample_data)
        
        prompt = f"""You are a Lead Data Scientist. Perform a comprehensive Exploratory Data Analysis (EDA) on this dataset.

Dataset Schema:
{schema_desc}

Sample Data:
{sample_desc}

Provide a structured EDA report and Python code for key visualizations.

IMPORTANT RULES FOR PYTHON:
1. You are provided with a pandas DataFrame 'df' (pre-loaded with the data).
2. You are provided with a matplotlib axis 'ax'.
3. DO NOT use pd.read_csv, pd.read_json, or any file loading. Use 'df'.
4. DO NOT create new figures or axes. Use 'ax'.
5. ONLY use columns listed in the schema above.
6. Return ONLY valid Python code in the code block.

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
            response = self._generate_with_retry(
                prompt,
                config=genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=8192,
                )
            )
            
            full_text = response.text
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

    async def generate_insights(self, query: str, sql_result: list, visualization_config: Dict[str, Any]) -> str:
        """Generate executive-level insights from the analysis results"""
        
        # Format the data for the LLM
        data_preview = json.dumps(sql_result[:10], default=str)
        row_count = len(sql_result)
        
        prompt = f"""
You are a Senior Management Consultant (McKinsey/Bain style). 
Your goal is to provide a sharp, high-level business summary of the following analysis.

**CONTEXT**
User Question: "{query}"
Data Result ({row_count} rows total): {data_preview}

**INSTRUCTIONS**
1. **EXECUTIVE SUMMARY**: Start with a high-level takeaway (max 2 sentences).
2. **KEY FINDINGS**: Use a detailed, nested bulleted list to highlight trends, anomalies, or noteworthy data points.
3. **METRIC SUMMARY TABLE**: Create a clean Markdown Table summarizing the most important metrics (e.g., totals, averages, or top categories).
4. **ACTIONABLE RECOMMENDATIONS**: Provide 2-3 specific business recommendations based exclusively on this data.
5. **FORMATTING**: Use bold text for emphasis, clear headers (###), and ensure tables have proper alignment.

Structure your response exactly as follows:
### 📊 Executive Summary
<summary>

### 🔍 Key Findings
- **<finding 1>**: <detail>
  - <sub-point if needed>
- **<finding 2>**: <detail>

### 📈 Metric Summary
| <Category/Dimension> | <Metric 1> | <Metric 2> |
| :--- | :--- | :--- |
| ... | ... | :--- |

### 💡 Recommendations
- **<recommendation 1>**: <reasoning>
- **<recommendation 2>**: <reasoning>
"""
        try:
            response = self._generate_with_retry(
                prompt,
                config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048
                )
            )
            return response.text
        except Exception as e:
            print(f"Error generating insights: {e}")
            return "Key insights could not be generated at this time."
    
    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """Format schema for prompt"""
        lines = []
        for col_name, col_type in schema.items():
            lines.append(f"  - {col_name}: {col_type}")
        return "\n".join(lines)
    
    def _format_sample_data(self, sample_data: list) -> str:
        """Format sample data for prompt"""
        if not sample_data:
            return "No sample data available"
        
        limited = sample_data[:3]
        return json.dumps(limited, indent=2)
    
    def _extract_sql(self, text: str) -> str:
        """Extract SQL from markdown code blocks or plain text"""
        code_block_pattern = r"```(?:sql)?\s*(.*?)\s*```"
        matches = re.findall(code_block_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            # Return the last match as it's usually the final query (if multiple) or the main one
            return matches[-1].strip()
            
        # Fallback: Look for raw SELECT statement if no code blocks
        # This regex looks for "SELECT ... FROM" structure ignoring case/newlines
        select_pattern = r"(SELECT\s+[\s\S]+?\s+FROM\s+[\s\S]+?;)"
        raw_matches = re.findall(select_pattern, text, re.IGNORECASE)
        if raw_matches:
             return raw_matches[-1].strip()

        # SUPER FALLBACK: If we still have "SELECT" inside the text but missed regex (e.g. no semicolon)
        # Just find the last "SELECT" and take everything after it
        parts = re.split(r"SELECT\s", text, flags=re.IGNORECASE)
        if len(parts) > 1:
            # Reconstruct
            clean_sql = "SELECT " + parts[-1]
            return clean_sql.strip()

        # Last resort fallback (though risky, better than nothing if purely SQL text)
        return text.strip()


# Singleton instance
gemini_service = GeminiService()
