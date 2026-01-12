"""
Chain-of-Thought Templates - Multi-Step Reasoning for SQL Generation

This module provides templates for structured reasoning before SQL generation.
Implements the "think step-by-step" approach for better accuracy.
"""

COT_SQL_GENERATION_TEMPLATE = """Given the user's question and available schema, think through the problem step-by-step before generating SQL.

**User Question:** {question}

**Available Schema:**
{schema}

**Step-by-Step Reasoning:**

1. **Understand the Question:**
   - What is the user asking for?
   - What is the expected output?
   - What type of analysis is this? (aggregation, trend, ranking, filter, etc.)

2. **Identify Required Columns:**
   - Which columns from the schema are needed?
   - Are all required columns available?
   - What are the data types?

3. **Determine Operations:**
   - Do we need aggregation? (SUM, AVG, COUNT, etc.)
   - Do we need grouping? (GROUP BY)
   - Do we need filtering? (WHERE, HAVING)
   - Do we need sorting? (ORDER BY)
   - Do we need limiting? (LIMIT)

4. **Plan the SQL Structure:**
   - SELECT: What columns/calculations to return?
   - FROM: Table alias 'd'
   - WHERE: Any row-level filters?
   - GROUP BY: Group by which columns?
   - HAVING: Any aggregate filters?
   - ORDER BY: Sort by which columns?
   - LIMIT: How many rows?

5. **Handle Edge Cases:**
   - NULL values: Use COALESCE if needed
   - Date formatting: Use DATE_TRUNC if needed
   - String matching: Use LIKE/ILIKE if needed
   - Type casting: Use CAST if needed

6. **Generate SQL:**
   - Write clean, formatted SQL
   - Use double quotes for column names
   - Use table alias 'd'
   - Add appropriate LIMIT

Now, generate the SQL query:
"""

COT_INTENT_CLASSIFICATION_TEMPLATE = """Analyze the user's question step-by-step to classify its intent.

**User Question:** {question}

**Available Schema:**
{schema}

**Step-by-Step Analysis:**

1. **Parse the Question:**
   - What are the key words? (top, average, trend, show, compare, etc.)
   - What entities are mentioned? (products, customers, sales, etc.)
   - What metrics are implied? (total, count, percentage, etc.)

2. **Identify Intent Type:**
   - Is this asking to SHOW data? (DESCRIPTIVE)
   - Is this asking to CALCULATE something? (AGGREGATION)
   - Is this asking for TRENDS over time? (TREND)
   - Is this asking for TOP/BOTTOM items? (RANKING)
   - Is this asking to COMPARE groups? (COMPARISON)
   - Is this asking for DISTRIBUTION/breakdown? (DISTRIBUTION)
   - Is this asking to FILTER data? (FILTER)
   - Is this UNRELATED to the data? (INVALID)

3. **Check Answerability:**
   - Are the required columns present in the schema?
   - Is the question specific enough?
   - Is there any ambiguity?

4. **Extract Components:**
   - Entities: What things are being asked about?
   - Metrics: What measurements are needed?
   - Time dimension: Is there a time component?
   - Filters: Are there any conditions?

Now, provide the classification in JSON format:
"""

COT_QUESTION_VALIDATION_TEMPLATE = """Validate whether this question can be answered with the available dataset.

**User Question:** {question}

**Available Schema:**
{schema}

**Validation Steps:**

1. **Relevance Check:**
   - Is this question related to data analysis?
   - Is it asking about business/data metrics?
   - Or is it completely unrelated (weather, sports, etc.)?

2. **Column Availability:**
   - What columns would be needed to answer this?
   - Are all required columns present in the schema?
   - List any missing columns

3. **Specificity Check:**
   - Is the question specific enough?
   - Or is it too vague/ambiguous?
   - Does it need clarification?

4. **Data Type Compatibility:**
   - Can the available columns support the requested analysis?
   - Are there type mismatches?

5. **Final Decision:**
   - Can we answer this question? YES/NO
   - If NO, why not?
   - If YES, what columns will we use?

Now, provide the validation result in JSON format:
"""

COT_SQL_CORRECTION_TEMPLATE = """Fix the SQL query that failed with an error.

**Original Question:** {question}

**Failed SQL:**
```sql
{failed_sql}
```

**Error Message:**
{error_message}

**Available Schema:**
{schema}

**Debugging Steps:**

1. **Understand the Error:**
   - What type of error is this? (syntax, column not found, type mismatch, etc.)
   - What line/part of the SQL caused it?

2. **Identify the Root Cause:**
   - Is it a column name issue? (wrong name, missing quotes)
   - Is it a syntax issue? (missing GROUP BY, wrong function)
   - Is it a type issue? (comparing wrong types)
   - Is it a logic issue? (wrong aggregation)

3. **Plan the Fix:**
   - What needs to be changed?
   - Check schema for correct column names
   - Verify syntax rules
   - Ensure proper aggregation

4. **Apply the Fix:**
   - Correct the SQL
   - Validate against schema
   - Ensure it follows DuckDB syntax

Now, provide ONLY the corrected SQL query:
"""

COT_VISUALIZATION_TEMPLATE = """Determine the best visualization for this data.

**User Question:** {question}

**Query Intent:** {intent}

**Data Structure:**
- Columns: {columns}
- Row count: {row_count}
- Sample data: {sample_data}

**Decision Steps:**

1. **Analyze Data Structure:**
   - How many columns?
   - What are the data types?
   - Is there a time dimension?
   - Is there a categorical dimension?

2. **Match Intent to Chart Type:**
   - TREND → Line chart (time series)
   - RANKING → Bar chart (horizontal or vertical)
   - DISTRIBUTION → Pie chart or stacked bar
   - COMPARISON → Grouped bar chart
   - AGGREGATION → Single metric or bar chart
   - DESCRIPTIVE → Table

3. **Consider Data Characteristics:**
   - Few categories (< 10) → Pie or bar
   - Many categories (> 10) → Bar chart with scroll
   - Time series → Line chart
   - Single metric → Card/number display
   - Multiple metrics → Table or grouped bar

4. **Choose Chart Type:**
   - Best option: [line|bar|pie|scatter|table]
   - Reason: [why this chart type]

Now, provide the visualization recommendation in JSON format:
"""


def build_cot_prompt(template: str, **kwargs) -> str:
    """
    Build a chain-of-thought prompt from template.
    
    Args:
        template: COT template string
        **kwargs: Variables to fill in template
        
    Returns:
        Formatted prompt string
    """
    return template.format(**kwargs)


def get_cot_template(task: str) -> str:
    """
    Get the appropriate COT template for a task.
    
    Args:
        task: Task type (sql_generation, intent_classification, etc.)
        
    Returns:
        COT template string
    """
    templates = {
        "sql_generation": COT_SQL_GENERATION_TEMPLATE,
        "intent_classification": COT_INTENT_CLASSIFICATION_TEMPLATE,
        "question_validation": COT_QUESTION_VALIDATION_TEMPLATE,
        "sql_correction": COT_SQL_CORRECTION_TEMPLATE,
        "visualization": COT_VISUALIZATION_TEMPLATE
    }
    
    return templates.get(task, "")
