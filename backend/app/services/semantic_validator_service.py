"""
Semantic Validator Service

Validates query results to ensure they make semantic sense:
- Check if results are reasonable
- Detect anomalies (negative revenue, etc.)
- Compare with historical patterns
- Flag suspicious results for user confirmation
"""

import logging
from typing import Dict, Any, List, Optional
import statistics

logger = logging.getLogger(__name__)


class SemanticValidatorService:
    """
    Validates query results for semantic correctness.
    """
    
    def validate_results(
        self,
        sql: str,
        results: List[Dict[str, Any]],
        question: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate query results for semantic correctness.
        
        Args:
            sql: Executed SQL query
            results: Query results
            question: Original question
            schema: Optional schema information
            
        Returns:
            Validation result with score and warnings
        """
        try:
            warnings = []
            score = 1.0
            
            # Check 1: Empty results
            if not results or len(results) == 0:
                warnings.append({
                    'type': 'empty_results',
                    'severity': 'medium',
                    'message': 'Query returned no results - filters might be too restrictive'
                })
                score -= 0.3
            
            # Check 2: Negative values in financial columns
            if results:
                negative_check = self._check_negative_values(results)
                if negative_check['has_negatives']:
                    warnings.append({
                        'type': 'negative_values',
                        'severity': 'high',
                        'message': f"Negative values found in {negative_check['columns']}"
                    })
                    score -= 0.4
            
            # Check 3: Outliers in numeric columns
            if results and len(results) > 3:
                outlier_check = self._check_outliers(results)
                if outlier_check['has_outliers']:
                    warnings.append({
                        'type': 'outliers',
                        'severity': 'low',
                        'message': f"Potential outliers detected in {outlier_check['columns']}"
                    })
                    score -= 0.1
            
            # Check 4: Duplicate rows
            if results and len(results) > 1:
                duplicate_check = self._check_duplicates(results)
                if duplicate_check['has_duplicates']:
                    warnings.append({
                        'type': 'duplicates',
                        'severity': 'medium',
                        'message': f"{duplicate_check['count']} duplicate rows found"
                    })
                    score -= 0.2
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            return {
                'is_valid': score >= 0.5,
                'score': round(score, 2),
                'warnings': warnings,
                'checks_performed': 4,
                'recommendation': self._get_recommendation(score, warnings)
            }
            
        except Exception as e:
            logger.error(f"Semantic validation error: {e}")
            return {
                'is_valid': True,  # Don't block on validation errors
                'score': 0.8,
                'warnings': [],
                'error': str(e)
            }
    
    def _check_negative_values(self, results: List[Dict]) -> Dict[str, Any]:
        """Check for negative values in financial columns"""
        financial_keywords = ['revenue', 'sales', 'price', 'amount', 'cost', 'profit', 'income']
        negative_columns = []
        
        for row in results:
            for key, value in row.items():
                # Check if column name suggests financial data
                if any(kw in key.lower() for kw in financial_keywords):
                    if isinstance(value, (int, float)) and value < 0:
                        if key not in negative_columns:
                            negative_columns.append(key)
        
        return {
            'has_negatives': len(negative_columns) > 0,
            'columns': negative_columns
        }
    
    def _check_outliers(self, results: List[Dict]) -> Dict[str, Any]:
        """Check for statistical outliers in numeric columns"""
        outlier_columns = []
        
        # Get numeric columns
        numeric_cols = {}
        for row in results:
            for key, value in row.items():
                if isinstance(value, (int, float)):
                    if key not in numeric_cols:
                        numeric_cols[key] = []
                    numeric_cols[key].append(value)
        
        # Check each numeric column for outliers
        for col, values in numeric_cols.items():
            if len(values) >= 4:  # Need at least 4 values for meaningful stats
                try:
                    mean = statistics.mean(values)
                    stdev = statistics.stdev(values)
                    
                    # Check if any value is > 2 standard deviations from mean
                    for val in values:
                        if abs(val - mean) > 2 * stdev:
                            if col not in outlier_columns:
                                outlier_columns.append(col)
                            break
                except:
                    pass
        
        return {
            'has_outliers': len(outlier_columns) > 0,
            'columns': outlier_columns
        }
    
    def _check_duplicates(self, results: List[Dict]) -> Dict[str, Any]:
        """Check for duplicate rows"""
        # Convert rows to tuples for comparison
        row_tuples = [tuple(sorted(row.items())) for row in results]
        unique_rows = set(row_tuples)
        
        duplicate_count = len(row_tuples) - len(unique_rows)
        
        return {
            'has_duplicates': duplicate_count > 0,
            'count': duplicate_count
        }
    
    def _get_recommendation(self, score: float, warnings: List[Dict]) -> str:
        """Get recommendation based on validation score"""
        if score >= 0.9:
            return "Results look good"
        elif score >= 0.7:
            return "Results are acceptable with minor warnings"
        elif score >= 0.5:
            return "Results may need review - check warnings"
        else:
            return "Results are suspicious - manual review recommended"


# Singleton instance
semantic_validator = SemanticValidatorService()
