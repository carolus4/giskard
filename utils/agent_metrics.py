"""
Agent metrics and observability utilities
"""
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AgentMetrics:
    """Simple metrics collector for agent operations"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.metrics = {
            'requests_total': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'tool_calls_total': 0,
            'create_task_calls': 0,
            'undo_operations': 0,
            'average_response_time': 0.0,
            'response_times': deque(maxlen=max_history),
            'error_counts': defaultdict(int),
            'last_reset': datetime.now().isoformat()
        }
    
    def record_request(self, success: bool, response_time: float, tool_calls: int = 0, 
                      create_task_calls: int = 0, error_type: Optional[str] = None):
        """Record a request and its metrics"""
        self.metrics['requests_total'] += 1
        self.metrics['response_times'].append(response_time)
        
        if success:
            self.metrics['requests_successful'] += 1
        else:
            self.metrics['requests_failed'] += 1
            if error_type:
                self.metrics['error_counts'][error_type] += 1
        
        self.metrics['tool_calls_total'] += tool_calls
        self.metrics['create_task_calls'] += create_task_calls
        
        # Update average response time
        if self.metrics['response_times']:
            self.metrics['average_response_time'] = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
    
    def record_undo(self):
        """Record an undo operation"""
        self.metrics['undo_operations'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return dict(self.metrics)
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            'requests_total': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'tool_calls_total': 0,
            'create_task_calls': 0,
            'undo_operations': 0,
            'average_response_time': 0.0,
            'response_times': deque(maxlen=self.max_history),
            'error_counts': defaultdict(int),
            'last_reset': datetime.now().isoformat()
        }
    
    def log_metrics(self):
        """Log current metrics"""
        logger.info(f"Agent Metrics: {self.get_metrics()}")

# Global metrics instance
agent_metrics = AgentMetrics()

class RequestTimer:
    """Context manager for timing requests"""
    
    def __init__(self, metrics: AgentMetrics):
        self.metrics = metrics
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            response_time = time.time() - self.start_time
            success = exc_type is None
            error_type = exc_type.__name__ if exc_type else None
            
            self.metrics.record_request(
                success=success,
                response_time=response_time,
                error_type=error_type
            )
