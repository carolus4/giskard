"""
Prompt performance tracking and analysis utilities
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics


@dataclass
class PerformanceMetrics:
    """Performance metrics for a prompt execution"""
    execution_time_ms: Optional[float] = None
    token_count: Optional[int] = None
    output_length: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    user_feedback: Optional[str] = None
    quality_score: Optional[float] = None  # 1-10 scale


class PromptPerformanceTracker:
    """Track and analyze prompt performance over time"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.performance_file = os.path.join(data_dir, "prompt_performance.json")
        self.metrics_file = os.path.join(data_dir, "prompt_metrics.json")
        self._performance_log: List[Dict[str, Any]] = []
        self._metrics_cache: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self):
        """Load existing performance data"""
        if os.path.exists(self.performance_file):
            try:
                with open(self.performance_file, 'r') as f:
                    self._performance_log = json.load(f)
            except Exception as e:
                print(f"Error loading performance data: {e}")
                self._performance_log = []

        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    self._metrics_cache = json.load(f)
            except Exception as e:
                print(f"Error loading metrics cache: {e}")
                self._metrics_cache = {}

    def _save_data(self):
        """Save performance data to files"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        with open(self.performance_file, 'w') as f:
            json.dump(self._performance_log, f, indent=2)
        
        with open(self.metrics_file, 'w') as f:
            json.dump(self._metrics_cache, f, indent=2)

    def log_execution(self, prompt_name: str, prompt_version: str, 
                     output: str, metrics: PerformanceMetrics,
                     input_data: Optional[Dict[str, Any]] = None):
        """Log a prompt execution with performance metrics"""
        execution_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "input_data": input_data or {},
            "output": output,
            "execution_time_ms": metrics.execution_time_ms,
            "token_count": metrics.token_count,
            "output_length": metrics.output_length,
            "success": metrics.success,
            "error_message": metrics.error_message,
            "user_feedback": metrics.user_feedback,
            "quality_score": metrics.quality_score
        }
        
        self._performance_log.append(execution_entry)
        self._save_data()
        
        # Update metrics cache
        self._update_metrics_cache(prompt_name, prompt_version)

    def _update_metrics_cache(self, prompt_name: str, prompt_version: str):
        """Update cached metrics for a prompt"""
        key = f"{prompt_name}_v{prompt_version}"
        
        # Get all executions for this prompt version
        executions = [e for e in self._performance_log 
                     if e.get('prompt_name') == prompt_name and 
                        e.get('prompt_version') == prompt_version]
        
        if not executions:
            return
        
        # Calculate metrics
        successful_executions = [e for e in executions if e.get('success', True)]
        
        metrics = {
            "total_executions": len(executions),
            "successful_executions": len(successful_executions),
            "success_rate": len(successful_executions) / len(executions) if executions else 0,
            "average_execution_time_ms": self._safe_average([e.get('execution_time_ms') for e in successful_executions]),
            "average_output_length": self._safe_average([e.get('output_length') for e in successful_executions]),
            "average_quality_score": self._safe_average([e.get('quality_score') for e in successful_executions if e.get('quality_score')]),
            "latest_execution": executions[-1]["timestamp"] if executions else None,
            "first_execution": executions[0]["timestamp"] if executions else None
        }
        
        self._metrics_cache[key] = metrics
        self._save_data()

    def _safe_average(self, values: List[Optional[float]]) -> Optional[float]:
        """Calculate average of non-None values"""
        valid_values = [v for v in values if v is not None]
        return statistics.mean(valid_values) if valid_values else None

    def get_performance_summary(self, prompt_name: str, 
                              days: Optional[int] = None) -> Dict[str, Any]:
        """Get performance summary for a prompt"""
        # Filter by time if specified
        executions = self._performance_log
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            executions = [e for e in executions 
                         if datetime.fromisoformat(e['timestamp']) >= cutoff_date]
        
        # Filter by prompt name
        executions = [e for e in executions if e.get('prompt_name') == prompt_name]
        
        if not executions:
            return {"total_executions": 0}
        
        successful_executions = [e for e in executions if e.get('success', True)]
        
        return {
            "total_executions": len(executions),
            "successful_executions": len(successful_executions),
            "success_rate": len(successful_executions) / len(executions) if executions else 0,
            "average_execution_time_ms": self._safe_average([e.get('execution_time_ms') for e in successful_executions]),
            "average_output_length": self._safe_average([e.get('output_length') for e in successful_executions]),
            "average_quality_score": self._safe_average([e.get('quality_score') for e in successful_executions if e.get('quality_score')]),
            "latest_execution": executions[-1]["timestamp"] if executions else None,
            "first_execution": executions[0]["timestamp"] if executions else None,
            "time_period_days": days
        }

    def get_version_comparison(self, prompt_name: str) -> Dict[str, Any]:
        """Compare performance across different versions of a prompt"""
        executions = [e for e in self._performance_log if e.get('prompt_name') == prompt_name]
        
        if not executions:
            return {}
        
        # Group by version
        versions = {}
        for execution in executions:
            version = execution.get('prompt_version', 'unknown')
            if version not in versions:
                versions[version] = []
            versions[version].append(execution)
        
        # Calculate metrics for each version
        version_metrics = {}
        for version, version_executions in versions.items():
            successful = [e for e in version_executions if e.get('success', True)]
            version_metrics[version] = {
                "total_executions": len(version_executions),
                "success_rate": len(successful) / len(version_executions) if version_executions else 0,
                "average_execution_time_ms": self._safe_average([e.get('execution_time_ms') for e in successful]),
                "average_output_length": self._safe_average([e.get('output_length') for e in successful]),
                "average_quality_score": self._safe_average([e.get('quality_score') for e in successful if e.get('quality_score')]),
                "latest_execution": version_executions[-1]["timestamp"] if version_executions else None
            }
        
        return version_metrics

    def get_trend_analysis(self, prompt_name: str, days: int = 30) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        cutoff_date = datetime.now() - timedelta(days=days)
        executions = [e for e in self._performance_log 
                     if e.get('prompt_name') == prompt_name and
                        datetime.fromisoformat(e['timestamp']) >= cutoff_date]
        
        if len(executions) < 2:
            return {"insufficient_data": True}
        
        # Sort by timestamp
        executions.sort(key=lambda x: x['timestamp'])
        
        # Calculate daily metrics
        daily_metrics = {}
        for execution in executions:
            date = execution['timestamp'][:10]  # YYYY-MM-DD
            if date not in daily_metrics:
                daily_metrics[date] = []
            daily_metrics[date].append(execution)
        
        # Analyze trends
        daily_success_rates = []
        daily_avg_times = []
        
        for date, day_executions in sorted(daily_metrics.items()):
            successful = [e for e in day_executions if e.get('success', True)]
            success_rate = len(successful) / len(day_executions) if day_executions else 0
            avg_time = self._safe_average([e.get('execution_time_ms') for e in successful])
            
            daily_success_rates.append(success_rate)
            if avg_time:
                daily_avg_times.append(avg_time)
        
        return {
            "analysis_period_days": days,
            "total_executions": len(executions),
            "daily_success_rates": daily_success_rates,
            "daily_avg_times": daily_avg_times,
            "overall_trend": "improving" if len(daily_success_rates) > 1 and daily_success_rates[-1] > daily_success_rates[0] else "stable"
        }

    def export_performance_data(self, prompt_name: Optional[str] = None, 
                              format: str = "json") -> str:
        """Export performance data for analysis"""
        data = self._performance_log
        
        if prompt_name:
            data = [e for e in data if e.get('prompt_name') == prompt_name]
        
        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "csv":
            # Simple CSV export
            if not data:
                return ""
            
            headers = list(data[0].keys())
            csv_lines = [",".join(headers)]
            
            for row in data:
                csv_lines.append(",".join(str(row.get(h, "")) for h in headers))
            
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global performance tracker instance
performance_tracker = PromptPerformanceTracker()
