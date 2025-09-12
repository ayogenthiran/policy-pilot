"""
Metrics and monitoring utilities for Policy Pilot RAG backend.
Handles performance tracking, resource monitoring, and structured logging.
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    operation: str
    duration: float
    timestamp: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    timestamp: float


class MetricsCollector:
    """Collects and manages performance metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        """
        Initialize metrics collector.
        
        Args:
            max_metrics: Maximum number of metrics to store in memory
        """
        self.max_metrics = max_metrics
        self.metrics: List[PerformanceMetric] = []
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        logger.info(f"MetricsCollector initialized with max_metrics={max_metrics}")
    
    def record_metric(self, operation: str, duration: float, success: bool = True, 
                     error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a performance metric.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            success: Whether the operation was successful
            error: Error message if operation failed
            metadata: Additional metadata
        """
        try:
            with self.lock:
                metric = PerformanceMetric(
                    operation=operation,
                    duration=duration,
                    timestamp=time.time(),
                    success=success,
                    error=error,
                    metadata=metadata or {}
                )
                
                self.metrics.append(metric)
                
                # Remove old metrics if over limit
                if len(self.metrics) > self.max_metrics:
                    self.metrics = self.metrics[-self.max_metrics:]
                
                logger.debug(f"Recorded metric: {operation} ({duration:.3f}s, success={success})")
                
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
    
    def get_metrics_summary(self, operation: Optional[str] = None, 
                           last_n_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get metrics summary.
        
        Args:
            operation: Filter by operation name
            last_n_minutes: Filter by last N minutes
            
        Returns:
            Metrics summary
        """
        try:
            with self.lock:
                current_time = time.time()
                
                # Filter metrics
                filtered_metrics = self.metrics
                
                if operation:
                    filtered_metrics = [m for m in filtered_metrics if m.operation == operation]
                
                if last_n_minutes:
                    cutoff_time = current_time - (last_n_minutes * 60)
                    filtered_metrics = [m for m in filtered_metrics if m.timestamp >= cutoff_time]
                
                if not filtered_metrics:
                    return {
                        'total_operations': 0,
                        'success_rate': 0.0,
                        'average_duration': 0.0,
                        'min_duration': 0.0,
                        'max_duration': 0.0,
                        'operations': {}
                    }
                
                # Calculate statistics
                total_operations = len(filtered_metrics)
                successful_operations = sum(1 for m in filtered_metrics if m.success)
                success_rate = successful_operations / total_operations if total_operations > 0 else 0.0
                
                durations = [m.duration for m in filtered_metrics]
                average_duration = sum(durations) / len(durations) if durations else 0.0
                min_duration = min(durations) if durations else 0.0
                max_duration = max(durations) if durations else 0.0
                
                # Group by operation
                operations = {}
                for metric in filtered_metrics:
                    if metric.operation not in operations:
                        operations[metric.operation] = {
                            'count': 0,
                            'success_count': 0,
                            'total_duration': 0.0,
                            'errors': []
                        }
                    
                    ops = operations[metric.operation]
                    ops['count'] += 1
                    ops['total_duration'] += metric.duration
                    
                    if metric.success:
                        ops['success_count'] += 1
                    else:
                        ops['errors'].append(metric.error)
                
                # Calculate per-operation statistics
                for op_name, op_data in operations.items():
                    op_data['success_rate'] = op_data['success_count'] / op_data['count']
                    op_data['average_duration'] = op_data['total_duration'] / op_data['count']
                
                return {
                    'total_operations': total_operations,
                    'success_rate': success_rate,
                    'average_duration': average_duration,
                    'min_duration': min_duration,
                    'max_duration': max_duration,
                    'operations': operations,
                    'uptime_seconds': current_time - self.start_time
                }
                
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {'error': str(e)}
    
    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        try:
            with self.lock:
                self.metrics.clear()
                logger.info("Metrics cleared")
        except Exception as e:
            logger.error(f"Failed to clear metrics: {e}")


class SystemMonitor:
    """Monitors system resources."""
    
    def __init__(self):
        """Initialize system monitor."""
        self.logger = get_logger(__name__)
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Get current system metrics.
        
        Returns:
            System metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_gb=memory_available_gb,
                disk_usage_percent=disk_usage_percent,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_gb=0.0,
                disk_usage_percent=0.0,
                timestamp=time.time()
            )
    
    def log_system_metrics(self) -> None:
        """Log current system metrics."""
        try:
            metrics = self.get_system_metrics()
            
            logger.info(
                f"System metrics - CPU: {metrics.cpu_percent:.1f}%, "
                f"Memory: {metrics.memory_percent:.1f}% ({metrics.memory_available_gb:.1f}GB available), "
                f"Disk: {metrics.disk_usage_percent:.1f}%"
            )
            
        except Exception as e:
            logger.error(f"Failed to log system metrics: {e}")


class StructuredLogger:
    """Enhanced structured logging with context."""
    
    def __init__(self):
        """Initialize structured logger."""
        self.logger = get_logger(__name__)
    
    def log_operation(self, operation: str, duration: float, success: bool = True,
                     error: Optional[str] = None, **kwargs) -> None:
        """
        Log operation with structured data.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            success: Whether operation was successful
            error: Error message if failed
            **kwargs: Additional context data
        """
        try:
            log_data = {
                'operation': operation,
                'duration': duration,
                'success': success,
                'timestamp': datetime.now().isoformat(),
                **kwargs
            }
            
            if error:
                log_data['error'] = error
            
            if success:
                self.logger.info(f"Operation completed: {operation}", extra=log_data)
            else:
                self.logger.error(f"Operation failed: {operation}", extra=log_data)
                
        except Exception as e:
            self.logger.error(f"Failed to log operation: {e}")
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       duration: float, client_ip: Optional[str] = None) -> None:
        """
        Log API request with structured data.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration: Request duration
            client_ip: Client IP address
        """
        try:
            log_data = {
                'type': 'api_request',
                'method': method,
                'path': path,
                'status_code': status_code,
                'duration': duration,
                'client_ip': client_ip,
                'timestamp': datetime.now().isoformat()
            }
            
            if 200 <= status_code < 300:
                self.logger.info(f"API request: {method} {path} - {status_code}", extra=log_data)
            elif 400 <= status_code < 500:
                self.logger.warning(f"API request: {method} {path} - {status_code}", extra=log_data)
            else:
                self.logger.error(f"API request: {method} {path} - {status_code}", extra=log_data)
                
        except Exception as e:
            self.logger.error(f"Failed to log API request: {e}")
    
    def log_document_processing(self, document_id: str, filename: str, 
                              chunks_count: int, duration: float, success: bool = True,
                              error: Optional[str] = None) -> None:
        """
        Log document processing with structured data.
        
        Args:
            document_id: Document ID
            filename: Document filename
            chunks_count: Number of chunks created
            duration: Processing duration
            success: Whether processing was successful
            error: Error message if failed
        """
        try:
            log_data = {
                'type': 'document_processing',
                'document_id': document_id,
                'filename': filename,
                'chunks_count': chunks_count,
                'duration': duration,
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            
            if error:
                log_data['error'] = error
            
            if success:
                self.logger.info(f"Document processed: {filename} ({chunks_count} chunks)", extra=log_data)
            else:
                self.logger.error(f"Document processing failed: {filename}", extra=log_data)
                
        except Exception as e:
            self.logger.error(f"Failed to log document processing: {e}")
    
    def log_search_query(self, query: str, results_count: int, duration: float,
                        search_type: str, success: bool = True, error: Optional[str] = None) -> None:
        """
        Log search query with structured data.
        
        Args:
            query: Search query
            results_count: Number of results returned
            duration: Query duration
            search_type: Type of search performed
            success: Whether query was successful
            error: Error message if failed
        """
        try:
            log_data = {
                'type': 'search_query',
                'query': query[:100],  # Truncate for privacy
                'results_count': results_count,
                'duration': duration,
                'search_type': search_type,
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            
            if error:
                log_data['error'] = error
            
            if success:
                self.logger.info(f"Search query: {search_type} - {results_count} results", extra=log_data)
            else:
                self.logger.error(f"Search query failed: {search_type}", extra=log_data)
                
        except Exception as e:
            self.logger.error(f"Failed to log search query: {e}")


# Global instances
metrics_collector = MetricsCollector()
system_monitor = SystemMonitor()
structured_logger = StructuredLogger()
