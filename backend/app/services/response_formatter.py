"""
Response Formatter - Converts SQL results to natural language

Formats query results in conversational, human-readable format
matching the style shown in reference examples.
"""
from typing import Dict, Any, List, Optional
import json


class ResponseFormatter:
    """Formats query results as natural language responses"""
    
    def format_response(
        self,
        query: str,
        result_data: List[Dict[str, Any]],
        columns: List[str],
        intent: str = 'descriptive',
        format_type: str = 'auto'
    ) -> str:
        """
        Format query results as natural language
        
        Args:
            query: Original user query
            result_data: Query results
            columns: Column names
            intent: Query intent (descriptive, comparative, etc.)
            format_type: 'list', 'table', 'summary', 'auto'
            
        Returns:
            Natural language formatted response
        """
        if not result_data:
            return "No results found for your query."
        
        # Auto-detect format if not specified
        if format_type == 'auto':
            format_type = self._detect_format(query, result_data, columns)
        
        if format_type == 'list':
            return self._format_as_list(query, result_data, columns)
        elif format_type == 'table':
            return self._format_as_table(query, result_data, columns)
        elif format_type == 'summary':
            return self._format_as_summary(query, result_data, columns)
        else:
            return self._format_as_list(query, result_data, columns)
    
    def _detect_format(
        self,
        query: str,
        result_data: List[Dict[str, Any]],
        columns: List[str]
    ) -> str:
        """Auto-detect the best format for results"""
        query_lower = query.lower()
        
        # Explicit format requests
        if 'table' in query_lower or 'tabular' in query_lower:
            return 'table'
        if 'list' in query_lower:
            return 'list'
        if 'summary' in query_lower or 'summarize' in query_lower:
            return 'summary'
        
        # Based on result characteristics
        row_count = len(result_data)
        col_count = len(columns)
        
        # Single value -> summary
        if row_count == 1 and col_count == 1:
            return 'summary'
        
        # Few rows, many columns -> table
        if row_count <= 5 and col_count > 3:
            return 'table'
        
        # Many rows, few columns -> list (ranking/ordering)
        if row_count > 5 and col_count <= 3:
            return 'list'
        
        # Default to list for rankings/orderings
        if any(word in query_lower for word in ['rank', 'top', 'bottom', 'highest', 'lowest', 'best', 'worst']):
            return 'list'
        
        return 'list'
    
    def _format_as_list(
        self,
        query: str,
        result_data: List[Dict[str, Any]],
        columns: List[str]
    ) -> str:
        """Format as a bulleted/numbered list"""
        # Detect if it's a ranking query
        query_lower = query.lower()
        is_ranking = any(word in query_lower for word in ['rank', 'top', 'bottom', 'order'])
        
        # Build intro sentence
        intro = self._generate_intro(query, result_data, is_ranking)
        
        # Format items
        items = []
        for i, row in enumerate(result_data, 1):
            item = self._format_list_item(row, columns, i if is_ranking else None)
            items.append(item)
        
        # Combine
        response = intro + "\n\n" + "\n".join(items)
        
        # Add footer if needed
        if len(result_data) > 5:
            response += f"\n\nShowing {len(result_data)} results."
        
        return response
    
    def _format_as_table(
        self,
        query: str,
        result_data: List[Dict[str, Any]],
        columns: List[str]
    ) -> str:
        """Format as a markdown table"""
        intro = f"Here is a ranking of {self._extract_subject(query)}:\n\n"
        
        # Build markdown table
        # Header
        header = "| " + " | ".join(self._format_column_name(col) for col in columns) + " |"
        separator = "|" + "|".join([" --- " for _ in columns]) + "|"
        
        # Rows
        rows = []
        for row in result_data:
            row_values = [self._format_value(row.get(col)) for col in columns]
            rows.append("| " + " | ".join(row_values) + " |")
        
        table = "\n".join([header, separator] + rows)
        
        return intro + table
    
    def _format_as_summary(
        self,
        query: str,
        result_data: List[Dict[str, Any]],
        columns: List[str]
    ) -> str:
        """Format as a prose summary"""
        if len(result_data) == 1 and len(columns) == 1:
            # Single value
            value = self._format_value(list(result_data[0].values())[0])
            return f"The result is **{value}**."
        
        # Multiple values - create a summary
        summary_parts = []
        for row in result_data[:5]:  # Limit to first 5
            parts = [f"{self._format_column_name(k)}: {self._format_value(v)}" for k, v in row.items()]
            summary_parts.append(", ".join(parts))
        
        return "\\n".join(f"- {part}" for part in summary_parts)
    
    def _format_list_item(
        self,
        row: Dict[str, Any],
        columns: List[str],
        rank: Optional[int] = None
    ) -> str:
        """Format a single list item"""
        # Get the main identifier (usually first column)
        identifier = self._format_value(row.get(columns[0]))
        
        # Get the metric (usually second column, or last if only 2 columns)
        if len(columns) >= 2:
            metric_col = columns[1] if len(columns) == 2 else columns[-1]
            metric = self._format_value(row.get(metric_col))
            
            if rank:
                return f"{rank}. **{identifier}**: {metric}"
            else:
                return f"- **{identifier}**: {metric}"
        else:
            if rank:
                return f"{rank}. {identifier}"
            else:
                return f"- {identifier}"
    
    def _generate_intro(
        self,
        query: str,
        result_data: List[Dict[str, Any]],
        is_ranking: bool
    ) -> str:
        """Generate an introductory sentence"""
        subject = self._extract_subject(query)
        count = len(result_data)
        
        if is_ranking:
            if 'descending' in query.lower() or 'highest' in query.lower() or 'top' in query.lower():
                order = "in descending order"
            elif 'ascending' in query.lower() or 'lowest' in query.lower() or 'bottom' in query.lower():
                order = "in ascending order"
            else:
                order = "by their values"
            
            return f"The {subject} are ranked {order} as follows:"
        else:
            return f"Here are the {subject}:"
    
    def _extract_subject(self, query: str) -> str:
        """Extract the subject from a query"""
        # Common subjects
        subjects = ['products', 'sales', 'customers', 'orders', 'items', 'regions', 'categories']
        
        query_lower = query.lower()
        for subject in subjects:
            if subject in query_lower:
                return subject
        
        # Default
        return "results"
    
    def _format_column_name(self, col_name: str) -> str:
        """Format column name for display"""
        # Convert snake_case to Title Case
        return col_name.replace('_', ' ').title()
    
    def _format_value(self, value: Any) -> str:
        """Format a value for display"""
        if value is None:
            return "N/A"
        
        # Number formatting
        if isinstance(value, (int, float)):
            # Check if it looks like money
            if abs(value) >= 0.01 and abs(value) < 1000000:
                # Could be money - format with 2 decimals
                return f"${value:,.2f}"
            elif abs(value) >= 1000000:
                # Large number - format with commas
                return f"${value:,.0f}"
            else:
                # Regular number
                return f"{value:,.2f}" if isinstance(value, float) else str(value)
        
        return str(value)


# Singleton instance
response_formatter = ResponseFormatter()
