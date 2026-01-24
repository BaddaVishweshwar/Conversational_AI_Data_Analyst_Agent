"""
Metrics Service

Tracks query performance metrics for monitoring and improvement:
- Query success rate
- Execution time
- User satisfaction (feedback)
- Correction rate
- Model performance

Provides analytics dashboard data and identifies areas for improvement.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Tracks and analyzes query performance metrics.
    """
    
    def __init__(self):
        # In-memory storage (in production, use database)
        self.query_metrics = []
        self.feedback_data = []
    
    def track_query_success(
        self,
        query_id: str,
        success: bool,
        execution_time_ms: int,
        dataset_id: int,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track query execution metrics.
        
        Args:
            query_id: Unique query ID
            success: Whether query succeeded
            execution_time_ms: Execution time in milliseconds
            dataset_id: Dataset ID
            user_id: User ID
            metadata: Additional metadata
        """
        try:
            metric = {
                'query_id': query_id,
                'success': success,
                'execution_time_ms': execution_time_ms,
                'dataset_id': dataset_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            self.query_metrics.append(metric)
            
            # Log if slow query
            if execution_time_ms > 5000:
                logger.warning(f"Slow query detected: {execution_time_ms}ms")
            
        except Exception as e:
            logger.error(f"Error tracking query metrics: {e}")
    
    def track_user_feedback(
        self,
        query_id: str,
        rating: str,  # 'up' or 'down'
        correction: Optional[str] = None,
        comment: Optional[str] = None
    ):
        """
        Track user feedback on query results.
        
        Args:
            query_id: Query ID
            rating: 'up' or 'down'
            correction: Optional corrected SQL
            comment: Optional user comment
        """
        try:
            feedback = {
                'query_id': query_id,
                'rating': rating,
                'correction': correction,
                'comment': comment,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.feedback_data.append(feedback)
            
            logger.info(f"Feedback recorded: {rating} for query {query_id}")
            
        except Exception as e:
            logger.error(f"Error tracking feedback: {e}")
    
    def get_accuracy_metrics(
        self,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get accuracy metrics for specified time window.
        
        Args:
            time_window_hours: Time window in hours
            
        Returns:
            Accuracy metrics
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
            
            # Filter recent queries
            recent_queries = [
                q for q in self.query_metrics
                if datetime.fromisoformat(q['timestamp']) > cutoff_time
            ]
            
            if not recent_queries:
                return {
                    'total_queries': 0,
                    'success_rate': 0,
                    'avg_execution_time_ms': 0
                }
            
            # Calculate metrics
            total = len(recent_queries)
            successful = sum(1 for q in recent_queries if q['success'])
            success_rate = (successful / total * 100) if total > 0 else 0
            
            exec_times = [q['execution_time_ms'] for q in recent_queries]
            avg_time = sum(exec_times) / len(exec_times) if exec_times else 0
            
            # Get feedback metrics
            recent_feedback = [
                f for f in self.feedback_data
                if datetime.fromisoformat(f['timestamp']) > cutoff_time
            ]
            
            positive_feedback = sum(1 for f in recent_feedback if f['rating'] == 'up')
            total_feedback = len(recent_feedback)
            satisfaction_rate = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
            
            correction_rate = sum(1 for f in recent_feedback if f.get('correction')) / total_feedback * 100 if total_feedback > 0 else 0
            
            return {
                'time_window_hours': time_window_hours,
                'total_queries': total,
                'successful_queries': successful,
                'failed_queries': total - successful,
                'success_rate': round(success_rate, 2),
                'avg_execution_time_ms': round(avg_time, 0),
                'total_feedback': total_feedback,
                'positive_feedback': positive_feedback,
                'satisfaction_rate': round(satisfaction_rate, 2),
                'correction_rate': round(correction_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {}
    
    def get_performance_trends(
        self,
        days: int = 7
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get performance trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Daily performance metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Group by date
            daily_metrics = defaultdict(lambda: {'total': 0, 'successful': 0, 'exec_times': []})
            
            for query in self.query_metrics:
                timestamp = datetime.fromisoformat(query['timestamp'])
                if timestamp > cutoff_date:
                    date_key = timestamp.date().isoformat()
                    daily_metrics[date_key]['total'] += 1
                    if query['success']:
                        daily_metrics[date_key]['successful'] += 1
                    daily_metrics[date_key]['exec_times'].append(query['execution_time_ms'])
            
            # Calculate daily stats
            trends = []
            for date, metrics in sorted(daily_metrics.items()):
                success_rate = (metrics['successful'] / metrics['total'] * 100) if metrics['total'] > 0 else 0
                avg_time = sum(metrics['exec_times']) / len(metrics['exec_times']) if metrics['exec_times'] else 0
                
                trends.append({
                    'date': date,
                    'total_queries': metrics['total'],
                    'success_rate': round(success_rate, 2),
                    'avg_execution_time_ms': round(avg_time, 0)
                })
            
            return {'daily_trends': trends}
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {'daily_trends': []}
    
    def get_slow_queries(
        self,
        threshold_ms: int = 3000,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get slowest queries for optimization.
        
        Args:
            threshold_ms: Threshold in milliseconds
            limit: Maximum number of queries to return
            
        Returns:
            List of slow queries
        """
        try:
            slow_queries = [
                q for q in self.query_metrics
                if q['execution_time_ms'] > threshold_ms
            ]
            
            # Sort by execution time (slowest first)
            slow_queries.sort(key=lambda x: x['execution_time_ms'], reverse=True)
            
            return slow_queries[:limit]
            
        except Exception as e:
            logger.error(f"Error getting slow queries: {e}")
            return []
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """
        Analyze common error patterns.
        
        Returns:
            Error analysis
        """
        try:
            failed_queries = [q for q in self.query_metrics if not q['success']]
            
            if not failed_queries:
                return {'total_errors': 0, 'error_types': {}}
            
            # Group by error type (from metadata)
            error_types = defaultdict(int)
            for query in failed_queries:
                error = query.get('metadata', {}).get('error_type', 'unknown')
                error_types[error] += 1
            
            return {
                'total_errors': len(failed_queries),
                'error_types': dict(error_types),
                'error_rate': round(len(failed_queries) / len(self.query_metrics) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing errors: {e}")
            return {}


# Singleton instance
metrics_service = MetricsService()
