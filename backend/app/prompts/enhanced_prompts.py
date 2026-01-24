"""
Enhanced Prompt Templates for Multi-Agent Analytics Pipeline

CamelAI-grade prompts with rich context, structured outputs, and task-specific configurations.
"""

# ============================================================================
# PLANNING PROMPTS
# ============================================================================

PLANNING_PROMPT_TEMPLATE = """You are a senior data analyst planning a comprehensive data analysis.

USER QUESTION: "{question}"

DATABASE SCHEMA:
{schema_details}

SAMPLE DATA (First 5 rows):
{sample_data}

COLUMN STATISTICS:
{column_statistics}

PREVIOUS CONVERSATION CONTEXT:
{conversation_context}

YOUR TASK:
Create a step-by-step analysis plan. Break down this question into 3-5 exploratory sub-questions that need to be investigated before answering the main question.

Think about:
1. What do I need to understand about the data first? (volume, categories, date ranges)
2. What are the key metrics or dimensions involved?
3. What preliminary queries will help me answer the main question?
4. What visualizations would best communicate the findings?

OUTPUT FORMAT (JSON):
{{
  "understanding": "Clear statement of what the user is asking for",
  "approach": "Brief explanation of how you'll answer this question",
  "sub_questions": [
    "What is the overall data volume and date range?",
    "What are the distinct categories/groups in the data?",
    "What are the key metrics and their distributions?",
    ...
  ],
  "required_metrics": ["metric1", "metric2", ...],
  "suggested_visualizations": ["line_chart", "bar_chart", "metric_cards"]
}}

Be specific and actionable. Focus on exploratory questions that will provide context for the main analysis.
"""

# ============================================================================
# EXPLORATORY QUERY PROMPTS
# ============================================================================

EXPLORATORY_QUERY_PROMPT_TEMPLATE = """You are generating an exploratory SQL query to understand the data better.

SUB-QUESTION: "{sub_question}"

DATABASE SCHEMA:
{schema_details}

SAMPLE DATA:
{sample_data}

PREVIOUS EXPLORATORY FINDINGS:
{previous_findings}

YOUR TASK:
Generate a SQL query to answer this exploratory sub-question. Keep it simple and focused.

**CRITICAL: The table name is ALWAYS "data"**
**CRITICAL: Use double quotes around column names: "Column Name"**

GUIDELINES:
- Use SQLite syntax only
- Keep queries simple (no complex JOINs or subqueries unless necessary)
- Limit results to 100 rows for exploratory queries
- Use DISTINCT, COUNT, MIN, MAX, AVG as appropriate
- Handle NULL values with COALESCE if needed
- For categorical data, show top 10 values
- For date ranges, use MIN/MAX
- For distributions, use COUNT and GROUP BY

OUTPUT FORMAT (JSON):
{{
  "sql": "SELECT ... FROM ... WHERE ... LIMIT 100",
  "explanation": "This query explores X by doing Y",
  "expected_insight": "This will tell us about..."
}}

Generate the SQL query now.
"""

# ============================================================================
# MAIN SQL GENERATION PROMPTS
# ============================================================================

SQL_GENERATION_PROMPT_TEMPLATE = """You are an expert SQL developer generating production-grade queries.

USER QUESTION: "{question}"

DATABASE SCHEMA:
{schema_details}

SAMPLE DATA:
{sample_data}

EXPLORATORY FINDINGS:
{exploratory_findings}

ANALYSIS PLAN:
{analysis_plan}

YOUR TASK:
Generate a comprehensive SQL query to answer the user's question. Use the exploratory findings to inform your query design.

**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**
**⚠️ CRITICAL RULES - MUST FOLLOW:**
**1. The table name is ALWAYS "data" - NEVER use any other name**
**2. DO NOT invent table names like "tv_radio", "sales_data", etc.**
**3. ALWAYS use: FROM data (not FROM tv_radio, FROM sales, etc.)**
**4. ALWAYS quote column names: "Column Name"**
**5. Example: SELECT "TV Ad Budget ($)" FROM data**
**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**

REQUIREMENTS:
- Use SQLite syntax only (no MySQL/PostgreSQL specific functions)
- Use CTEs (WITH clauses) for complex logic to improve readability
- Add SQL comments (--) explaining each major section
- Handle NULL values explicitly with COALESCE
- Use proper date formatting with strftime() for SQLite
- Include appropriate GROUP BY, ORDER BY, and LIMIT clauses
- Optimize for performance (avoid SELECT *, use indexes when possible)
- Limit final results to 1000 rows unless specifically requested
- Use meaningful column aliases (AS)

QUERY PATTERNS:
- Aggregation: SELECT "column", COUNT(*)/SUM()/AVG() FROM data GROUP BY "column"
- Time series: SELECT strftime('%Y-%m', "date") as month, SUM("metric") FROM data GROUP BY month ORDER BY month
- Top N: SELECT "column", COUNT(*) as count FROM data GROUP BY "column" ORDER BY count DESC LIMIT N
- Comparison: Use CASE statements for bucketing and categorization

OUTPUT FORMAT (JSON):
{{
  "sql": "-- Main analysis query\\nWITH cte_name AS (\\n  SELECT ...\\n)\\nSELECT ... FROM cte_name ...",
  "explanation": "Detailed explanation of what this query does and why it's structured this way",
  "complexity": "simple|medium|complex",
  "expected_rows": 50
}}

Generate the optimized SQL query now.
"""

# ============================================================================
# INSIGHT GENERATION PROMPTS
# ============================================================================

INSIGHT_GENERATION_PROMPT_TEMPLATE = """You are a senior business analyst at McKinsey/BCG explaining data analysis results to C-level executives.

USER'S QUESTION: "{question}"

QUERY RESULTS:
{formatted_results}

EXPLORATORY FINDINGS:
{exploratory_findings}

DATA CONTEXT:
- Total rows analyzed: {total_rows}
- Date range: {date_range}
- Key metrics: {key_metrics}

YOUR TASK:
Write a comprehensive business analysis explaining what the data reveals. Use clear, executive-friendly language.

STRUCTURE YOUR RESPONSE AS FOLLOWS:

**Summary** (2-3 sentences):
Provide a high-level answer to the user's question. Focus on the most important finding.

**Key Findings** (3-5 bullet points):
- Most important insights from the data
- Notable trends, patterns, or anomalies
- Unexpected discoveries or surprises
- Comparative insights (vs benchmarks, time periods, segments)

**Detailed Analysis** (2-3 paragraphs):
Explain what the data shows in depth. Provide context, comparisons, and relationships between variables. 
Discuss why these patterns might exist and what they mean for the business.
Use specific numbers and percentages to support your points.

**Recommendations** (if applicable):
Based on this analysis, suggest:
- Actionable next steps
- Areas requiring attention or investigation
- Opportunities to capitalize on
- Follow-up questions to explore

WRITING GUIDELINES:
- Use simple business language, avoid technical jargon
- Be specific with numbers (e.g., "increased by 23%" not "increased significantly")
- Focus on business impact and actionable insights
- Write in a confident, authoritative tone
- Use comparisons to provide context (e.g., "compared to last quarter")
- Highlight both positive findings and areas of concern

OUTPUT FORMAT (JSON):
{{
  "summary": "2-3 sentence high-level answer",
  "key_findings": [
    "Finding 1 with specific numbers",
    "Finding 2 with context",
    "Finding 3 highlighting trends",
    ...
  ],
  "detailed_analysis": "2-3 paragraphs of in-depth business analysis with specific data points and context",
  "recommendations": "Actionable next steps and opportunities (or null if not applicable)"
}}

Write the business analysis now.
"""

# ============================================================================
# VISUALIZATION SELECTION PROMPTS
# ============================================================================

VISUALIZATION_SELECTION_PROMPT_TEMPLATE = """You are a data visualization expert selecting the best charts to communicate insights.

USER QUESTION: "{question}"

QUERY RESULTS STRUCTURE:
- Columns: {column_names}
- Column types: {column_types}
- Row count: {row_count}
- Has time/date column: {has_time_column}
- Has categorical column: {has_categorical_column}
- Numeric columns: {numeric_columns}

QUERY INTENT: {query_intent}

YOUR TASK:
Select 2-3 complementary visualizations that best communicate the findings. Consider the data structure and user's question.

SELECTION RULES:
1. Time series data (date + numeric) → Line chart or Area chart
2. Categories + numeric (≤10 categories) → Bar chart or Pie chart
3. Categories + numeric (>10 categories) → Bar chart (top 10) + "Others"
4. Multiple numeric columns → Multi-line chart or Grouped bar chart
5. Single metric → Metric card with large number
6. Comparisons → Horizontal bar chart or Side-by-side bars
7. Distribution → Histogram or Box plot
8. Always include summary statistics table for detailed data

CHART TYPES AVAILABLE:
- line: Trends over time
- bar: Category comparisons
- horizontal_bar: Ranking comparisons
- pie: Proportions (max 10 slices)
- metric_card: Single key number
- table: Detailed data view
- multi_line: Multiple metrics over time
- grouped_bar: Multi-dimensional comparisons

OUTPUT FORMAT (JSON):
{{
  "visualizations": [
    {{
      "type": "line|bar|pie|metric_card|table|...",
      "config": {{
        "x_axis": "column_name",
        "y_axis": "column_name" or ["col1", "col2"],
        "title": "Descriptive chart title",
        "x_label": "X axis label",
        "y_label": "Y axis label",
        "color_scheme": "blue|green|purple|multi",
        "sort": "ascending|descending|none",
        "limit": 10
      }},
      "purpose": "Why this chart is useful"
    }},
    ...
  ],
  "primary_chart": 0
}}

Select the visualizations now.
"""

# ============================================================================
# ERROR CORRECTION PROMPTS
# ============================================================================

SQL_ERROR_CORRECTION_PROMPT_TEMPLATE = """You are debugging a SQL query that failed to execute.

ORIGINAL QUERY:
{failed_sql}

ERROR MESSAGE:
{error_message}

DATABASE SCHEMA:
{schema_details}

YOUR TASK:
Fix the SQL query to resolve the error. Analyze the error message and correct the issue.

COMMON ERRORS:
1. Column name typos or case sensitivity
2. Missing GROUP BY for aggregations
3. Invalid date format or functions
4. Syntax errors (missing commas, parentheses)
5. Using MySQL/PostgreSQL functions instead of SQLite
6. NULL handling issues

OUTPUT FORMAT (JSON):
{{
  "fixed_sql": "Corrected SQL query",
  "explanation": "What was wrong and how you fixed it",
  "confidence": "high|medium|low"
}}

Fix the query now.
"""

EMPTY_RESULTS_ANALYSIS_PROMPT_TEMPLATE = """A SQL query returned no results. Help understand why.

QUERY:
{sql_query}

USER QUESTION:
{user_question}

DATABASE SCHEMA:
{schema_details}

SAMPLE DATA:
{sample_data}

YOUR TASK:
Explain why the query returned no results and suggest an alternative approach.

POSSIBLE REASONS:
1. Filters too restrictive (date range, WHERE conditions)
2. No data matching the criteria
3. Column values don't match expected format
4. JOIN conditions eliminating all rows
5. Typo in filter values

OUTPUT FORMAT (JSON):
{{
  "reason": "Most likely explanation for empty results",
  "suggestion": "Alternative query or approach to try",
  "alternative_sql": "Modified SQL query (if applicable)"
}}

Analyze the empty results now.
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_schema_for_prompt(schema: dict) -> str:
    """Format schema dictionary into readable text for prompts."""
    lines = [f"Table: {schema.get('table_name', 'data')}"]
    lines.append("\nColumns:")
    
    for col in schema.get('columns', []):
        col_info = f"- {col['name']} ({col['type']})"
        if 'description' in col:
            col_info += f": {col['description']}"
        if 'sample_values' in col:
            samples = ', '.join(str(v) for v in col['sample_values'][:5])
            col_info += f"\n  Sample values: {samples}"
        lines.append(col_info)
    
    if 'row_count' in schema:
        lines.append(f"\nTotal rows: {schema['row_count']}")
    
    return '\n'.join(lines)

def format_sample_data_for_prompt(sample_data: list) -> str:
    """Format sample data into readable text for prompts."""
    if not sample_data:
        return "No sample data available"
    
    lines = ["First 5 rows:"]
    for i, row in enumerate(sample_data[:5], 1):
        lines.append(f"{i}. {row}")
    
    return '\n'.join(lines)

def format_column_statistics_for_prompt(statistics: dict) -> str:
    """Format column statistics into readable text for prompts."""
    if not statistics:
        return "No statistics available"
    
    lines = []
    for col_name, stats in statistics.items():
        lines.append(f"\n{col_name}:")
        if 'distinct_count' in stats:
            lines.append(f"  - Distinct values: {stats['distinct_count']}")
        if 'null_percentage' in stats:
            lines.append(f"  - NULL %: {stats['null_percentage']:.1f}%")
        if 'min_value' in stats and 'max_value' in stats:
            lines.append(f"  - Range: {stats['min_value']} to {stats['max_value']}")
        if 'top_values' in stats:
            top = ', '.join(str(v) for v in stats['top_values'][:5])
            lines.append(f"  - Top values: {top}")
    
    return '\n'.join(lines)

def format_conversation_context_for_prompt(context: list) -> str:
    """Format conversation history into readable text for prompts."""
    if not context:
        return "No previous conversation"
    
    lines = ["Recent conversation:"]
    for i, entry in enumerate(context[-5:], 1):
        q = entry.get('user_query') or entry.get('question') or 'N/A'
        lines.append(f"\n{i}. Q: {q}")
        
        # Try multiple fields for answer/insights
        a = entry.get('insights') or entry.get('key_findings') or entry.get('answer')
        if a:
            # If it's a long text, truncate?
            if isinstance(a, list): a = "; ".join(a)
            lines.append(f"   A: {str(a)[:200]}...")
    
    return '\n'.join(lines)

def format_exploratory_findings_for_prompt(findings: list) -> str:
    """Format exploratory query findings into readable text for prompts."""
    if not findings:
        return "No exploratory findings yet"
    
    lines = ["Exploratory findings:"]
    for i, finding in enumerate(findings, 1):
        lines.append(f"\n{i}. {finding.get('sub_question', 'N/A')}")
        lines.append(f"   Finding: {finding.get('finding', 'N/A')}")
    
    return '\n'.join(lines)

# ============================================================================
# TEMPERATURE CONFIGURATIONS
# ============================================================================

TEMPERATURE_CONFIG = {
    'planning': 0.5,           # Creative but structured
    'exploratory': 0.3,        # Focused exploration
    'sql_generation': 0.1,     # Very precise for SQL
    'insight_generation': 0.7, # More creative writing
    'visualization': 0.4,      # Balanced selection
    'error_correction': 0.2    # Precise debugging
}

CONTEXT_CONFIG = {
    'num_ctx': 8192,      # Large context window
    'num_predict': 2048   # Allow longer responses
}
