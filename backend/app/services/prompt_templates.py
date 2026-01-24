"""
Professional Prompt Templates for AI Data Analyst Platform

Structured, role-based prompts with clear sections for consistent,
high-quality LLM responses across all agents.
"""

# ============================================================================
# 1. QUERY PLANNING PROMPT
# ============================================================================

QUERY_PLANNING_PROMPT = """ROLE: You are an expert data analyst planning a comprehensive analysis.

CONTEXT:
Database Schema with Statistics:
{enriched_schema}

Sample Data (first 5 rows):
{sample_data}

Data Volume: {row_count} rows

Previous Conversation Context:
{conversation_history}

TASK: Break down the user's question into 3-5 exploratory sub-questions that will lead to a complete, thorough answer. Think step-by-step about what information you need to gather before answering the main question.

User Question: "{user_question}"

REQUIREMENTS:
- Start with basic data exploration (volume, structure, distributions)
- Then move to specific analytical questions
- Plan for appropriate visualizations based on data types
- Consider data quality and completeness

OUTPUT (valid JSON only, no markdown):
{{
  "understanding": "The user wants to know [rephrase question in clear terms]",
  "approach": "To answer this comprehensively, I will [describe step-by-step approach]",
  "sub_questions": [
    "What is the overall data volume and structure?",
    "What are the distinct values in key columns?",
    "[Additional specific questions based on the query]"
  ],
  "expected_visualizations": ["table", "bar", "line"]
}}

Respond with ONLY the JSON object, no other text."""


# ============================================================================
# 2. EXPLORATION SQL GENERATION PROMPT
# ============================================================================

EXPLORATION_SQL_PROMPT = """ROLE: You are an expert SQL developer writing exploratory queries.

CONTEXT:
Database Schema:
{schema_context}

Sample Data:
{sample_data}

Available Columns: {column_list}

TASK: Generate a simple, fast SQL query to answer this exploratory question.

Question: "{exploration_question}"

REQUIREMENTS:
- Keep query simple and fast (< 100ms execution)
- Use LIMIT clauses appropriately
- Handle NULLs explicitly
- Add clear SQL comments
- Return practical aggregations
- Table name is always 'data'

OUTPUT (valid JSON only, no markdown):
{{
  "sql": "-- Purpose: [brief description]\\nSELECT ... FROM data ...",
  "explanation": "This query checks [what it does and why]",
  "expected_rows": 10
}}

Respond with ONLY the JSON object, no other text."""


# ============================================================================
# 3. MAIN ANALYSIS SQL GENERATION PROMPT
# ============================================================================

MAIN_ANALYSIS_SQL_PROMPT = """ROLE: You are an expert SQL developer and data analyst.

CONTEXT:
Database Schema with Full Context:
{enriched_schema}

Sample Data:
{sample_data}

Exploratory Findings:
{exploration_findings}

Intent: {intent}
Required Columns: {required_columns}
Aggregations Needed: {aggregations}
Group By Dimensions: {groupby_columns}

TASK: Generate a comprehensive SQL query for the main analysis.

User Question: "{user_question}"

REQUIREMENTS:
- Use CTEs (WITH clauses) for complex queries to improve readability
- Add SQL comments explaining each section
- Handle NULL values explicitly
- Optimize with appropriate ordering
- Add LIMIT clause (max 1000 rows for large results)
- Use meaningful column aliases
- Table name is always 'data'

OUTPUT (valid JSON only, no markdown):
{{
  "sql_query": "-- Main Analysis Query\\n-- Purpose: [description]\\n\\nWITH base_data AS (\\n  SELECT ...\\n  FROM data\\n  WHERE ...\\n)\\n\\nSELECT ...\\nFROM base_data\\nORDER BY ...\\nLIMIT 1000;",
  "sql_explanation": "This query [detailed explanation of approach and logic]",
  "expected_columns": ["column1", "column2"],
  "supporting_queries": [
    {{
      "name": "Overall Total",
      "query": "SELECT COUNT(*) as total FROM data",
      "purpose": "Get baseline context"
    }}
  ]
}}

Respond with ONLY the JSON object, no other text."""


# ============================================================================
# 4. INSIGHT GENERATION PROMPT (Executive-Grade Narrative)
# ============================================================================

INSIGHT_GENERATION_PROMPT = """ROLE: You are a senior business analyst presenting data insights to executives. Your job is to explain what the data means in business terms, not technical terms.

CONTEXT:
Original Question: "{original_question}"

Exploratory Findings:
{exploratory_findings}

Main Query Results (showing top rows):
{main_results}

Data Interpretation Summary:
{interpretation_summary}

Supporting Context:
{supporting_context}

TASK: Write a comprehensive, executive-level analysis that answers the question clearly.

STRUCTURE REQUIREMENTS:

1. **Direct Answer** (1-2 sentences): Answer the question immediately and clearly.

2. **Key Findings** (3-5 bullet points): Specific, actionable insights.
   - Focus on "so what?" not "what"
   - Include numbers and percentages
   - Highlight trends, patterns, or anomalies

3. **Detailed Analysis** (2-3 paragraphs, ~200 words):
   - First paragraph: Overall patterns and trends
   - Second paragraph: Deeper dive into significant findings
   - Third paragraph: Context, implications, or comparisons
   - Use business language, not technical jargon
   - Reference specific data points to support claims

4. **Recommendations** (optional, 2-3 bullets if applicable):
   - Actionable next steps
   - Further analysis suggestions
   - Business decisions to consider

WRITING STYLE:
- Use clear, simple language (8th-grade reading level)
- Avoid technical terms like "aggregation", "correlation coefficient"
- Focus on business impact: revenue, cost, efficiency, growth, risk
- Use active voice and strong verbs
- Be specific with numbers

OUTPUT (valid JSON only, no markdown):
{{
  "direct_answer": "[Clear 1-2 sentence answer to the question]",
  "what_data_shows": [
    "Finding 1 with specific metrics",
    "Finding 2 highlighting trend",
    "Finding 3 showing comparison"
  ],
  "why_it_happened": [
    "Explanation of pattern 1",
    "Context for trend 2"
  ],
  "business_implications": [
    "Impact on business metric 1",
    "Consideration for decision 2"
  ],
  "confidence": 0.85
}}

Respond with ONLY the JSON object, no other text."""


# ============================================================================
# 5. PYTHON ANALYSIS PROMPT (PandasAI Style)
# ============================================================================

PYTHON_ANALYSIS_PROMPT = """ROLE: You are an expert data analyst and Python developer.
Your goal is to answer the user's question by writing a Python script that uses pandas and plotly.

CONTEXT:
Variable `df` is already loaded with the data.
Columns: {columns}
Sample Data:
{sample_data}

User Question: "{user_question}"

SMART LOGIC INSTRUCTIONS:
1. **Infer Defaults**: If the user asks for "ad spend" (and you have 'TV', 'Radio'...), plot ALL of them or their sum. Do NOT ask for clarification.
2. **Best-Effort Visualization**: If the user doesn't specify a chart type, choose the best one (Scatter for correlation, Bar for comparison, Line for trends).
3. **Handle Ambiguity**: If the question is "Sales vs Spend", plot Sales against EACH spend column (using subplots or color) or Total Spend. Just do it.

CODING INSTRUCTIONS:
1. Write a Python script to analyze the `df` and optionally generate a plot.
2. The script must be valid, executable Python code.
3. If the user asks for a plot/graph/chart OR if the intent implies visualization:
   - Create a Plotly figure using `plotly.express` (preferred) or `plotly.graph_objects`.
   - Assign the figure object to a variable named `fig`.
   - Do NOT use `fig.show()`.
4. If the user asks for a specific value:
   - Print the result to stdout.
   - For tables, print the markdown representation `print(result_df.to_markdown())` or just `print(result)`.
5. Error Handling:
   - Handle potential missing values or data type issues if obvious.
   - DO NOT load the data; `df` is already available in the locals().

OUTPUT FORMAT (valid JSON):
{{
  "code": "import pandas as pd\\nimport plotly.express as px\\n\\n# logic here...",
  "explanation": "Calculated X by grouping Y and plotted as bar chart."
}}
"""

# ============================================================================
# 6. OLLAMA CONFIGURATION PRESETS
# ============================================================================

OLLAMA_CONFIGS = {
    "planning": {
        "temperature": 0.5,  # Creative planning
        "num_ctx": 8192,     # Large context for schema
        "num_predict": 1024,
        "top_p": 0.9
    },
    "sql_generation": {
        "temperature": 0.1,  # Very precise for SQL
        "num_ctx": 8192,
        "num_predict": 2048,
        "top_p": 0.95
    },
    "exploration": {
        "temperature": 0.2,  # Precise but slightly creative
        "num_ctx": 4096,
        "num_predict": 512,
        "top_p": 0.95
    },
    "insight_generation": {
        "temperature": 0.7,  # More creative writing
        "num_ctx": 8192,
        "num_predict": 2048,
        "top_p": 0.9
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_schema_for_prompt(schema_analysis, include_samples: bool = True) -> str:
    """
    Format SchemaAnalysis into a rich, readable prompt section.
    
    Returns:
    '''
    **SCHEMA WITH CONTEXT**
    
    Dataset: 200 rows, 4 columns
    
    Column: TV (FLOAT)
      - Range: 0.7 to 296.4
      - Average: 147.04 ± 85.85
      - Missing: 0%
      - Distinct values: 199
      - Sample values: [230.1, 44.5, 17.2, 151.5, 180.8]
    
    Column: Radio (FLOAT)
      ...
    '''
    """
    lines = ["**SCHEMA WITH CONTEXT**", ""]
    
    num_cols = len(schema_analysis.columns)
    lines.append(f"Dataset: {num_cols} columns")
    lines.append("")
    
    for col_name, col_meta in schema_analysis.columns.items():
        lines.append(f"Column: {col_name} ({col_meta.type})")
        
        if col_meta.type in ['INTEGER', 'FLOAT', 'NUMERIC']:
            if col_meta.min is not None and col_meta.max is not None:
                lines.append(f"  - Range: {col_meta.min} to {col_meta.max}")
            if col_meta.avg is not None:
                std_str = f" ± {col_meta.std_dev:.2f}" if col_meta.std_dev else ""
                lines.append(f"  - Average: {col_meta.avg:.2f}{std_str}")
        
        lines.append(f"  - Missing: {col_meta.missing_percentage}%")
        lines.append(f"  - Distinct values: {col_meta.unique_count}")
        
        if include_samples and hasattr(col_meta, 'sample_values') and col_meta.sample_values:
            sample_str = ", ".join(str(v) for v in col_meta.sample_values[:5])
            lines.append(f"  - Sample values: [{sample_str}]")
        
        lines.append("")
    
    return "\n".join(lines)


def format_exploration_findings(exploration_results) -> str:
    """
    Format exploration results into a clear summary for prompts.
    
    Returns:
    '''
    Exploration Finding 1: Dataset contains 200 rows
    - SQL: SELECT COUNT(*) FROM data
    - Result: 200
    
    Exploration Finding 2: 4 numeric columns with full coverage
    - SQL: SELECT COUNT(DISTINCT TV) as tv_count FROM data
    - Result: ...
    '''
    """
    if not exploration_results:
        return "No exploratory analysis performed yet."
    
    lines = []
    for i, exp in enumerate(exploration_results, 1):
        lines.append(f"Exploration Finding {i}: {exp.get('finding', 'N/A')}")
        lines.append(f"- Question: {exp.get('question', 'N/A')}")
        lines.append(f"- SQL: {exp.get('sql', 'N/A')}")
        lines.append(f"- Result: {exp.get('result', 'N/A')}")
        lines.append("")
    
    return "\n".join(lines)


def format_sample_data(df, max_rows: int = 5) -> str:
    """
    Format DataFrame sample into a readable table for prompts.
    
    Returns:
    '''
    | TV    | Radio | Newspaper | Sales |
    |-------|-------|-----------|-------|
    | 230.1 | 37.8  | 69.2      | 22.1  |
    | 44.5  | 39.3  | 45.1      | 10.4  |
    ...
    '''
    """
    if df is None or df.empty:
        return "No sample data available."
    
    sample = df.head(max_rows)
    
    # Create markdown table
    headers = list(sample.columns)
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["-------" for _ in headers]) + "|")
    
    for _, row in sample.iterrows():
        row_str = " | ".join(str(v) for v in row.values)
        lines.append(f"| {row_str} |")
    
    return "\n".join(lines)
