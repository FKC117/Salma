"""
Structured Logging Service (T011)
Handles comprehensive logging with correlation IDs and structured data
"""

import logging
import uuid
import json
import time
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import psutil
import os

class StructuredLogger:
    """Structured logging service with correlation IDs"""
    
    def __init__(self, name: str = 'analytics'):
        self.logger = logging.getLogger(name)
        self.correlation_id = None
        self.request_id = None
        self.user_id = None
        self.session_id = None
    
    def set_context(self, correlation_id: str = None, request_id: str = None, 
                   user_id: int = None, session_id: str = None):
        """Set logging context"""
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id
    
    def _format_message(self, message: str, level: str, extra_data: Dict = None) -> Dict:
        """Format message with structured data"""
        base_data = {
            'timestamp': timezone.now().isoformat(),
            'level': level,
            'message': message,
            'correlation_id': self.correlation_id,
            'request_id': self.request_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'service': 'analytics'
        }
        
        if extra_data:
            base_data.update(extra_data)
        
        return base_data
    
    def _log_structured(self, level: str, message: str, extra_data: Dict = None):
        """Log structured message"""
        structured_data = self._format_message(message, level, extra_data)
        
        # Log to file
        self.logger.log(getattr(logging, level.upper()), json.dumps(structured_data))
        
        # Also log to console in development
        if settings.DEBUG:
            print(f"[{level.upper()}] {message} | {self.correlation_id}")
    
    def info(self, message: str, extra_data: Dict = None):
        """Log info message"""
        self._log_structured('INFO', message, extra_data)
    
    def warning(self, message: str, extra_data: Dict = None):
        """Log warning message"""
        self._log_structured('WARNING', message, extra_data)
    
    def error(self, message: str, extra_data: Dict = None):
        """Log error message"""
        self._log_structured('ERROR', message, extra_data)
    
    def debug(self, message: str, extra_data: Dict = None):
        """Log debug message"""
        self._log_structured('DEBUG', message, extra_data)
    
    def critical(self, message: str, extra_data: Dict = None):
        """Log critical message"""
        self._log_structured('CRITICAL', message, extra_data)

class PerformanceLogger:
    """Performance monitoring and logging"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.start_times = {}
        self.metrics = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str, extra_data: Dict = None):
        """End timing and log performance"""
        if operation not in self.start_times:
            return
        
        duration = time.time() - self.start_times[operation]
        
        # Get system metrics
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        performance_data = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'memory_usage_mb': round(memory_info.used / 1024 / 1024, 2),
            'memory_percent': memory_info.percent,
            'cpu_percent': cpu_percent,
            'timestamp': timezone.now().isoformat()
        }
        
        if extra_data:
            performance_data.update(extra_data)
        
        self.logger.info(f"Performance: {operation}", performance_data)
        
        # Store metrics
        self.metrics[operation] = performance_data
        
        # Clean up
        del self.start_times[operation]
    
    def log_system_metrics(self):
        """Log current system metrics"""
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        system_data = {
            'memory_total_gb': round(memory_info.total / 1024 / 1024 / 1024, 2),
            'memory_used_gb': round(memory_info.used / 1024 / 1024 / 1024, 2),
            'memory_percent': memory_info.percent,
            'disk_total_gb': round(disk_info.total / 1024 / 1024 / 1024, 2),
            'disk_used_gb': round(disk_info.used / 1024 / 1024 / 1024, 2),
            'disk_percent': round((disk_info.used / disk_info.total) * 100, 2),
            'cpu_percent': cpu_percent,
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.info("System metrics", system_data)

class AuditLogger:
    """Audit trail logging"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def log_user_action(self, user_id: int, action: str, resource: str, 
                       details: Dict = None, success: bool = True):
        """Log user action for audit trail"""
        audit_data = {
            'action_type': 'user_action',
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'success': success,
            'details': details or {},
            'timestamp': timezone.now().isoformat()
        }
        
        level = 'INFO' if success else 'WARNING'
        self.logger._log_structured(level, f"User action: {action}", audit_data)
    
    def log_system_event(self, event: str, details: Dict = None, level: str = 'INFO'):
        """Log system event"""
        event_data = {
            'event_type': 'system_event',
            'event': event,
            'details': details or {},
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger._log_structured(level, f"System event: {event}", event_data)
    
    def log_security_event(self, event: str, details: Dict = None, severity: str = 'WARNING'):
        """Log security-related event"""
        security_data = {
            'event_type': 'security_event',
            'event': event,
            'severity': severity,
            'details': details or {},
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger._log_structured(severity, f"Security event: {event}", security_data)

class ErrorLogger:
    """Error tracking and logging"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def log_exception(self, exception: Exception, context: Dict = None):
        """Log exception with full context"""
        error_data = {
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'context': context or {},
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.error(f"Exception: {type(exception).__name__}", error_data)
    
    def log_validation_error(self, field: str, value: Any, error_message: str):
        """Log validation error"""
        validation_data = {
            'error_type': 'validation_error',
            'field': field,
            'value': str(value),
            'error_message': error_message,
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.warning(f"Validation error: {field}", validation_data)

# Global logging services
def get_logger(name: str = 'analytics') -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger(name)

def get_performance_logger(logger: StructuredLogger = None) -> PerformanceLogger:
    """Get performance logger instance"""
    if logger is None:
        logger = get_logger()
    return PerformanceLogger(logger)

def get_audit_logger(logger: StructuredLogger = None) -> AuditLogger:
    """Get audit logger instance"""
    if logger is None:
        logger = get_logger()
    return AuditLogger(logger)

def get_error_logger(logger: StructuredLogger = None) -> ErrorLogger:
    """Get error logger instance"""
    if logger is None:
        logger = get_logger()
    return ErrorLogger(logger)

# Decorator for automatic logging
def log_function_call(logger: StructuredLogger = None):
    """Decorator to automatically log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if logger is None:
                log = get_logger()
            else:
                log = logger
            
            func_name = f"{func.__module__}.{func.__name__}"
            log.info(f"Function call: {func_name}", {
                'function': func_name,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            })
            
            try:
                result = func(*args, **kwargs)
                log.info(f"Function success: {func_name}")
                return result
            except Exception as e:
                log.error(f"Function error: {func_name}", {
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                raise
        
        return wrapper
    return decorator
