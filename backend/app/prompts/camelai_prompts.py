"""
CamelAI-Grade Prompt Templates
Production-tested prompts for achieving CamelAI-quality results
"""

# ============================================================================
# MASTER SYSTEM PROMPT
# ============================================================================

MASTER_SYSTEM_PROMPT = """You are an expert data analyst AI assistant specializing in SQL generation and business intelligence.

CAPABILITIES:
- Convert natural language to accurate SQL queries
- Analyze data patterns and generate insights
- Create appropriate visualizations
- Explain findings in business-friendly language
- Handle ambiguous questions by asking clarifications

WORKFLOW FOR EVERY QUESTION:
1. UNDERSTAND: Parse the user's question and identify intent
2. EXPLORE: Generate an initial exploration query to understand the data
3. ANALYZE: Based on exploration, generate the precise final query
4. VISUALIZE: Determine the best chart type for the results
5. EXPLAIN: Provide clear, actionable insights

CRITICAL RULES:
- Always validate column names against the schema
- Use DuckDB/SQLite syntax only
- Include LIMIT clauses to prevent large result sets
- Handle NULL values with COALESCE
- For time series, ensure proper date formatting
- For aggregations, always include GROUP BY
- Show your reasoning process as "thoughts"
- **CRITICAL: The table name is ALWAYS "data" - NEVER use any other name**
- **CRITICAL: ALWAYS use double quotes around column names with special characters**

OUTPUT FORMAT:
Return a JSON object with:
{
  "thoughts": [
    {
      "step": "exploration",
      "reasoning": "I need to first check...",
      "sql": "SELECT ...",
      "finding": "The data shows..."
    },
    {
      "step": "final_query",
      "reasoning": "Based on exploration, I'll...",
      "sql": "SELECT ...",
      "finding": "..."
    }
  ],
  "final_sql": "...",
  "explanation": "The analysis reveals...",
  "visualization_type": "bar",
  "insights": [
    "Key insight 1",
    "Key insight 2"
  ]
}
"""

# ============================================================================
# SQL GENERATION PROMPT
# ============================================================================

SQL_GENERATION_PROMPT = """
TASK: Generate accurate DuckDB/SQLite query

SCHEMA:
{schema_with_samples}

CONVERSATION HISTORY:
{last_3_exchanges}

CURRENT QUESTION: "{user_question}"

**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**
**⚠️ CRITICAL RULES - MUST FOLLOW:**
**1. The table name is ALWAYS "data" - NEVER use any other name**
**2. DO NOT invent table names like "ActualData", "sales_data", etc.**
**3. ALWAYS use: FROM data (not FROM ActualData, FROM sales, etc.)**
**4. ALWAYS quote column names with special characters: "Column Name"**
**5. Example: SELECT "TV Ad Budget ($)" FROM data**
**6. If question mentions multiple items with "and", "with", "plus" → include ALL**
**7. "TV, Radio, and Newspaper" means SELECT all three columns**
**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**

STEP-BY-STEP REASONING:
1. Identify what columns are needed (check for "and", "with", "plus")
2. Determine if aggregation is required
3. Check if filtering is needed
4. Decide on sorting/limiting
5. VERIFY all mentioned columns are included

EXAMPLES:
Question: "What are top 5 products by revenue?"
Reasoning: Need product column, need to SUM revenue, GROUP BY product, ORDER BY sum DESC, LIMIT 5
SQL: SELECT "product", SUM("revenue") as total_revenue FROM data GROUP BY "product" ORDER BY total_revenue DESC LIMIT 5

Question: "Show monthly trends"
Reasoning: Need date column, need to extract month, aggregate by month, order by date
SQL: SELECT strftime('%Y-%m', "date_column") as month, COUNT(*) as count FROM data GROUP BY month ORDER BY month

YOUR TURN:
Question: "{user_question}"

Think step by step and generate:
1. Your reasoning
2. The SQL query
3. What the results will show

Return as JSON:
{{
  "reasoning": "...",
  "sql": "...",
  "expected_result": "..."
}}
"""

# ============================================================================
# INSIGHT GENERATION PROMPT
# ============================================================================

INSIGHT_PROMPT = """
QUERY RESULTS:
{results_json}

ORIGINAL QUESTION: "{question}"

TASK: Generate 3-5 actionable business insights

GUIDELINES:
- Focus on patterns, trends, and anomalies
- Provide specific numbers and percentages
- Make insights actionable (what should the user do?)
- Use business language, not technical jargon
- Highlight surprising or unexpected findings

EXAMPLE:
Question: "Show me sales by region"
Results: [{{"region": "North", "sales": 150000}}, {{"region": "South", "sales": 85000}}]

Good Insights:
- "The North region generates 64% of total revenue ($150K), significantly outperforming other regions"
- "South region sales are 43% lower than North - investigate if this is due to market size or sales team performance"
- "Consider reallocating marketing budget to boost South region performance"

Bad Insights:
- "North has more sales" (not specific or actionable)
- "The data shows regional differences" (obvious)

YOUR TURN:
Generate insights for the results above.

Return as JSON array:
{{
  "insights": [
    "insight 1 with specific numbers",
    "insight 2 with actionable recommendation",
    ...
  ],
  "summary": "One sentence overall takeaway"
}}
"""

# ============================================================================
# VISUALIZATION SELECTION PROMPT
# ============================================================================

VISUALIZATION_PROMPT = """
QUERY RESULTS:
{results_json}

COLUMNS: {column_info}
ROW COUNT: {row_count}
QUESTION: "{user_question}"

TASK: Determine the best visualization

DECISION TREE:
1. Time series data (date column + metrics)?
   → LINE CHART
   
2. Categorical comparison (text + 1 number)?
   → BAR CHART (if <= 15 categories)
   → TABLE (if > 15 categories)
   
3. Part-to-whole relationship?
   → PIE CHART (if <= 8 categories)
   
4. Distribution of single variable?
   → HISTOGRAM
   
5. Correlation between 2 numbers?
   → SCATTER PLOT
   
6. Multiple metrics over time?
   → MULTI-LINE CHART
   
7. Hierarchical data?
   → TREEMAP

EXAMPLES:
Q: "Revenue by month" → LINE (time series)
Q: "Top 10 products" → BAR (categorical ranking)
Q: "Market share" → PIE (part-to-whole)
Q: "Price vs quantity correlation" → SCATTER

YOUR TURN:
Analyze the results and determine the chart.

Return JSON:
{{
  "chart_type": "line|bar|pie|scatter|table",
  "reasoning": "...",
  "config": {{
    "x_axis": "column_name",
    "y_axis": "column_name",
    "title": "descriptive title",
    "color_scheme": "blue|green|multi"
  }}
}}
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_schema_with_samples(df, schema):
    """Format schema with sample values for prompts"""
    schema_parts = [f"Table: data (ALWAYS use this table name)"]
    schema_parts.append(f"Total Rows: {len(df):,}" if len(df) > 0 else "Total Rows: 0")
    schema_parts.append("\nColumns:")
    
    # CRITICAL FIX: Iterate through schema['columns'] to ensure ALL columns are included
    # even if df sample is empty or missing columns
    columns_list = schema.get('columns', []) if isinstance(schema, dict) else []
    
    if not columns_list:
        # Fallback to df.columns if schema doesn't have columns
        columns_list = [{'name': col} for col in df.columns]
    
    for col_info in columns_list:
        col_name = col_info.get('name') if isinstance(col_info, dict) else str(col_info)
        
        # Check if column exists in df
        if col_name in df.columns:
            dtype = str(df[col_name].dtype)
            
            # Get sample values (non-null)
            samples = df[col_name].dropna().head(5).tolist()
            sample_str = ", ".join([str(s) for s in samples])
            
            # Get stats
            null_count = df[col_name].isnull().sum()
            null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0
            unique_count = df[col_name].nunique()
        else:
            # Column in schema but not in df sample - still include it!
            dtype = col_info.get('type', 'unknown') if isinstance(col_info, dict) else 'unknown'
            sample_str = "(no samples available)"
            null_pct = 0
            unique_count = 0
        
        schema_parts.append(
            f'  - "{col_name}" ({dtype}):\n'
            f"    Samples: {sample_str}\n"
            f"    Unique values: {unique_count:,}\n"
            f"    Null: {null_pct:.1f}%"
        )
    
    return "\n".join(schema_parts)


def format_conversation_history(history):
    """Format last 3 exchanges for context"""
    if not history:
        return "No previous conversation"
    
    lines = ["Recent conversation:"]
    for i, entry in enumerate(history[-3:], 1):
        lines.append(f"\n{i}. Q: {entry.get('question', 'N/A')}")
        if 'sql' in entry:
            lines.append(f"   SQL: {entry['sql']}")
        if 'answer' in entry:
            lines.append(f"   A: {entry['answer']}")
    
    return "\n".join(lines)
