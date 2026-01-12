"""
Few-Shot Examples Library - High-Quality SQL Examples

This module contains carefully crafted examples for few-shot learning.
Each example demonstrates best practices for DuckDB SQL generation.
"""

# Example format: (question, thinking, sql)
FEW_SHOT_EXAMPLES = [
    {
        "id": 1,
        "category": "DESCRIPTIVE",
        "question": "Show me the first 10 rows of data",
        "thinking": "User wants to preview the dataset. Simple SELECT with LIMIT.",
        "sql": """SELECT *
FROM data d
LIMIT 10"""
    },
    {
        "id": 2,
        "category": "AGGREGATION",
        "question": "What is the total revenue?",
        "thinking": "User wants sum of revenue column. Need to aggregate all rows.",
        "sql": """SELECT 
    SUM("Revenue") as total_revenue
FROM data d"""
    },
    {
        "id": 3,
        "category": "AGGREGATION",
        "question": "What's the average price by category?",
        "thinking": "User wants average price grouped by category. Need GROUP BY.",
        "sql": """SELECT 
    "Category",
    AVG("Price") as avg_price,
    COUNT(*) as product_count
FROM data d
GROUP BY "Category"
ORDER BY avg_price DESC"""
    },
    {
        "id": 4,
        "category": "RANKING",
        "question": "Show me the top 5 products by sales",
        "thinking": "User wants products ranked by total sales. Need SUM, GROUP BY, ORDER BY DESC, LIMIT 5.",
        "sql": """SELECT 
    "Product Name",
    SUM("Sales") as total_sales,
    COUNT(*) as order_count
FROM data d
GROUP BY "Product Name"
ORDER BY total_sales DESC
LIMIT 5"""
    },
    {
        "id": 5,
        "category": "TREND",
        "question": "Show sales trend by month",
        "thinking": "User wants time series by month. Need DATE_TRUNC to group by month.",
        "sql": """SELECT 
    DATE_TRUNC('month', "Order Date") as month,
    SUM("Sales") as monthly_sales,
    COUNT(*) as order_count
FROM data d
GROUP BY DATE_TRUNC('month', "Order Date")
ORDER BY month"""
    },
    {
        "id": 6,
        "category": "FILTER",
        "question": "Which customers spent more than $1000?",
        "thinking": "User wants customers filtered by total spending. Need GROUP BY and HAVING.",
        "sql": """SELECT 
    "Customer Name",
    SUM("Amount") as total_spent,
    COUNT(*) as purchase_count
FROM data d
GROUP BY "Customer Name"
HAVING SUM("Amount") > 1000
ORDER BY total_spent DESC"""
    },
    {
        "id": 7,
        "category": "COMPARISON",
        "question": "Compare revenue by region",
        "thinking": "User wants to see revenue breakdown by region for comparison.",
        "sql": """SELECT 
    "Region",
    SUM("Revenue") as total_revenue,
    AVG("Revenue") as avg_revenue,
    COUNT(*) as transaction_count
FROM data d
GROUP BY "Region"
ORDER BY total_revenue DESC"""
    },
    {
        "id": 8,
        "category": "DISTRIBUTION",
        "question": "Show the distribution of orders by status",
        "thinking": "User wants count and percentage breakdown by status.",
        "sql": """SELECT 
    "Status",
    COUNT(*) as order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM data d
GROUP BY "Status"
ORDER BY order_count DESC"""
    },
    {
        "id": 9,
        "category": "COMPLEX",
        "question": "What are the top 3 products in each category by revenue?",
        "thinking": "User wants top products per category. Need window function with ROW_NUMBER.",
        "sql": """WITH ranked_products AS (
    SELECT 
        "Category",
        "Product Name",
        SUM("Revenue") as total_revenue,
        ROW_NUMBER() OVER (PARTITION BY "Category" ORDER BY SUM("Revenue") DESC) as rank
    FROM data d
    GROUP BY "Category", "Product Name"
)
SELECT 
    "Category",
    "Product Name",
    total_revenue
FROM ranked_products
WHERE rank <= 3
ORDER BY "Category", rank"""
    },
    {
        "id": 10,
        "category": "TIME_COMPARISON",
        "question": "Compare this month's sales to last month",
        "thinking": "User wants month-over-month comparison. Need to calculate current and previous month.",
        "sql": """WITH monthly_sales AS (
    SELECT 
        DATE_TRUNC('month', "Order Date") as month,
        SUM("Sales") as total_sales
    FROM data d
    WHERE "Order Date" >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '2 months')
    GROUP BY DATE_TRUNC('month', "Order Date")
)
SELECT 
    month,
    total_sales,
    LAG(total_sales) OVER (ORDER BY month) as previous_month_sales,
    ROUND((total_sales - LAG(total_sales) OVER (ORDER BY month)) * 100.0 / 
          LAG(total_sales) OVER (ORDER BY month), 2) as growth_percentage
FROM monthly_sales
ORDER BY month DESC
LIMIT 2"""
    }
]


def get_examples_by_intent(intent: str, limit: int = 3) -> list:
    """
    Get few-shot examples filtered by intent category.
    
    Args:
        intent: Intent type (AGGREGATION, RANKING, TREND, etc.)
        limit: Maximum number of examples to return
        
    Returns:
        List of relevant examples
    """
    # First try exact match
    exact_matches = [ex for ex in FEW_SHOT_EXAMPLES if ex['category'] == intent]
    
    if exact_matches:
        return exact_matches[:limit]
    
    # If no exact match, return general examples
    return FEW_SHOT_EXAMPLES[:limit]


def get_all_examples() -> list:
    """Get all few-shot examples."""
    return FEW_SHOT_EXAMPLES


def format_examples_for_prompt(examples: list) -> str:
    """
    Format examples for inclusion in LLM prompt.
    
    Args:
        examples: List of example dictionaries
        
    Returns:
        Formatted string for prompt
    """
    formatted = []
    
    for i, ex in enumerate(examples, 1):
        formatted.append(f"""Example {i}:
Question: "{ex['question']}"
Thinking: {ex['thinking']}
SQL:
```sql
{ex['sql']}
```
""")
    
    return "\n".join(formatted)


# Domain-specific examples for common business questions
BUSINESS_EXAMPLES = {
    "sales": [
        {
            "question": "What are our best-selling products?",
            "sql": """SELECT 
    "Product Name",
    SUM("Quantity") as units_sold,
    SUM("Revenue") as total_revenue
FROM data d
GROUP BY "Product Name"
ORDER BY units_sold DESC
LIMIT 10"""
        },
        {
            "question": "Show quarterly sales performance",
            "sql": """SELECT 
    DATE_TRUNC('quarter', "Order Date") as quarter,
    SUM("Revenue") as quarterly_revenue,
    COUNT(DISTINCT "Customer ID") as unique_customers
FROM data d
GROUP BY DATE_TRUNC('quarter', "Order Date")
ORDER BY quarter"""
        }
    ],
    "customer": [
        {
            "question": "Who are our top customers by lifetime value?",
            "sql": """SELECT 
    "Customer Name",
    SUM("Amount") as lifetime_value,
    COUNT(*) as total_orders,
    AVG("Amount") as avg_order_value
FROM data d
GROUP BY "Customer Name"
ORDER BY lifetime_value DESC
LIMIT 20"""
        }
    ],
    "inventory": [
        {
            "question": "Which products have low stock levels?",
            "sql": """SELECT 
    "Product Name",
    "Stock Quantity",
    "Reorder Level"
FROM data d
WHERE "Stock Quantity" < "Reorder Level"
ORDER BY "Stock Quantity" ASC"""
        }
    ]
}


def get_domain_examples(domain: str) -> list:
    """
    Get domain-specific examples (sales, customer, inventory, etc.)
    
    Args:
        domain: Domain category
        
    Returns:
        List of domain-specific examples
    """
    return BUSINESS_EXAMPLES.get(domain.lower(), [])
