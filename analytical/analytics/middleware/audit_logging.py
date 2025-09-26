"""
Audit Logging Middleware

This middleware provides comprehensive audit logging for all HTTP requests,
including request/response logging, user activity tracking, security event
logging, and compliance audit trails.
"""

import time
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Comprehensive audit logging middleware for compliance and security
    """
    
    # Sensitive headers to mask
    SENSITIVE_HEADERS = [
        'HTTP_AUTHORIZATION',
        'HTTP_COOKIE',
        'HTTP_X_AUTH_TOKEN',
        'HTTP_X_API_KEY',
        'HTTP_SESSION_ID',
    ]
    
    # Sensitive parameters to mask
    SENSITIVE_PARAMS = [
        'password',
        'token',
        'api_key',
        'secret',
        'auth',
        'session',
        'csrf',
        'ssn',
        'credit_card',
        'phone',
    ]
    
    # Paths that require detailed logging
    HIGH_PRIORITY_PATHS = [
        '/api/upload/',
        '/api/analysis/',
        '/api/agent/',
        '/api/auth/',
        '/admin/',
        '/accounts/',
    ]
    
    # Paths to exclude from audit logging
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/health/',
        '/metrics/',
    ]
    
    # HTTP methods that require audit logging
    AUDIT_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Load configuration
        self.audit_enabled = getattr(settings, 'AUDIT_LOGGING_ENABLED', True)
        self.log_requests = getattr(settings, 'AUDIT_LOG_REQUESTS', True)
        self.log_responses = getattr(settings, 'AUDIT_LOG_RESPONSES', True)
        self.log_get_requests = getattr(settings, 'AUDIT_LOG_GET_REQUESTS', False)
        self.mask_sensitive_data = getattr(settings, 'AUDIT_MASK_SENSITIVE_DATA', True)
        self.detailed_logging = getattr(settings, 'AUDIT_DETAILED_LOGGING', True)
        
        # Custom configuration
        self.custom_sensitive_params = getattr(settings, 'AUDIT_SENSITIVE_PARAMS', [])
        self.sensitive_params = self.SENSITIVE_PARAMS + self.custom_sensitive_params
        
        self.custom_excluded_paths = getattr(settings, 'AUDIT_EXCLUDED_PATHS', [])
        self.excluded_paths = self.EXCLUDED_PATHS + self.custom_excluded_paths
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process incoming request for audit logging"""
        if not self.audit_enabled:
            return None
        
        # Skip excluded paths
        if self._is_excluded_path(request.path):
            return None
        
        # Skip GET requests if not configured to log them
        if not self.log_get_requests and request.method == 'GET':
            return None
        
        try:
            # Generate correlation ID for this request
            correlation_id = str(uuid.uuid4())
            request.audit_correlation_id = correlation_id
            request.audit_start_time = time.time()
            
            # Log request
            if self.log_requests:
                self._log_request(request, correlation_id)
        
        except Exception as e:
            logger.error(f"Audit logging error in process_request: {str(e)}")
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process response for audit logging"""
        if not self.audit_enabled:
            return response
        
        # Skip if request was not processed for audit
        if not hasattr(request, 'audit_correlation_id'):
            return response
        
        try:
            # Calculate request duration
            if hasattr(request, 'audit_start_time'):
                duration = time.time() - request.audit_start_time
            else:
                duration = 0
            
            # Log response
            if self.log_responses:
                self._log_response(request, response, duration)
            
            # Log to audit trail if it's a significant action
            if self._is_significant_action(request, response):
                self._log_to_audit_trail(request, response, duration)
        
        except Exception as e:
            logger.error(f"Audit logging error in process_response: {str(e)}")
        
        return response
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path should be excluded from audit logging"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _is_high_priority_path(self, path: str) -> bool:
        """Check if path requires high priority logging"""
        return any(path.startswith(priority) for priority in self.HIGH_PRIORITY_PATHS)
    
    def _is_significant_action(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Determine if this is a significant action requiring audit trail entry"""
        # Always log high-priority paths
        if self._is_high_priority_path(request.path):
            return True
        
        # Log state-changing methods
        if request.method in self.AUDIT_METHODS:
            return True
        
        # Log failed requests
        if response.status_code >= 400:
            return True
        
        # Log authentication events
        if '/auth/' in request.path or '/login' in request.path or '/logout' in request.path:
            return True
        
        return False
    
    def _log_request(self, request: HttpRequest, correlation_id: str):
        """Log incoming request details"""
        try:
            # Prepare request data
            request_data = {
                'correlation_id': correlation_id,
                'timestamp': timezone.now().isoformat(),
                'method': request.method,
                'path': request.path,
                'full_path': request.get_full_path(),
                'remote_addr': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'content_type': request.content_type,
                'content_length': request.META.get('CONTENT_LENGTH', 0),
            }
            
            # Add user information
            if request.user.is_authenticated:
                request_data['user'] = {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'is_staff': request.user.is_staff,
                    'is_superuser': request.user.is_superuser,
                }
            else:
                request_data['user'] = {'authenticated': False}
            
            # Add session information
            if hasattr(request, 'session') and request.session.session_key:
                request_data['session_key'] = request.session.session_key
            
            # Add headers (masked)
            if self.detailed_logging:
                request_data['headers'] = self._mask_sensitive_headers(dict(request.META))
            
            # Add parameters (masked)
            if request.GET:
                request_data['get_params'] = self._mask_sensitive_params(dict(request.GET))
            
            if request.POST:
                request_data['post_params'] = self._mask_sensitive_params(dict(request.POST))
            
            # Add JSON body (masked) for API requests
            if request.content_type == 'application/json' and hasattr(request, 'body'):
                try:
                    json_data = json.loads(request.body.decode('utf-8'))
                    request_data['json_body'] = self._mask_sensitive_json(json_data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    request_data['json_body'] = {'error': 'Could not parse JSON body'}
            
            # Add file upload information
            if request.FILES:
                request_data['files'] = []
                for field_name, uploaded_file in request.FILES.items():
                    file_info = {
                        'field': field_name,
                        'name': uploaded_file.name,
                        'size': uploaded_file.size,
                        'content_type': uploaded_file.content_type,
                    }
                    request_data['files'].append(file_info)
            
            # Log the request
            logger.info(f"HTTP Request: {request.method} {request.path}", extra={
                'audit_type': 'http_request',
                'audit_data': request_data
            })
        
        except Exception as e:
            logger.error(f"Failed to log request: {str(e)}")
    
    def _log_response(self, request: HttpRequest, response: HttpResponse, duration: float):
        """Log response details"""
        try:
            # Prepare response data
            response_data = {
                'correlation_id': getattr(request, 'audit_correlation_id', ''),
                'timestamp': timezone.now().isoformat(),
                'status_code': response.status_code,
                'reason_phrase': response.reason_phrase,
                'content_type': response.get('Content-Type', ''),
                'content_length': len(response.content) if hasattr(response, 'content') else 0,
                'duration_ms': round(duration * 1000, 2),
            }
            
            # Add response headers (selective)
            if self.detailed_logging:
                response_headers = {}
                for header in ['Content-Type', 'Content-Length', 'Cache-Control', 'Location']:
                    if response.has_header(header):
                        response_headers[header] = response[header]
                response_data['headers'] = response_headers
            
            # Add response body for small JSON responses (masked)
            if (response.get('Content-Type', '').startswith('application/json') and 
                len(response.content) < 10000):  # Only for responses < 10KB
                try:
                    json_data = json.loads(response.content.decode('utf-8'))
                    response_data['json_body'] = self._mask_sensitive_json(json_data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    response_data['json_body'] = {'error': 'Could not parse JSON response'}
            
            # Log the response
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(log_level, f"HTTP Response: {response.status_code} for {request.method} {request.path}", extra={
                'audit_type': 'http_response',
                'audit_data': response_data
            })
        
        except Exception as e:
            logger.error(f"Failed to log response: {str(e)}")
    
    def _log_to_audit_trail(self, request: HttpRequest, response: HttpResponse, duration: float):
        """Log significant actions to the audit trail database"""
        try:
            from analytics.services.audit_trail_manager import AuditTrailManager
            
            audit_manager = AuditTrailManager()
            
            # Determine action type and category
            action_type, action_category = self._determine_action_type(request, response)
            
            # Prepare additional details
            additional_details = {
                'http_method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'content_type': request.content_type,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'correlation_id': getattr(request, 'audit_correlation_id', ''),
            }
            
            # Add file upload details
            if request.FILES:
                additional_details['files_uploaded'] = [
                    {'name': f.name, 'size': f.size} for f in request.FILES.values()
                ]
            
            # Add parameters (masked)
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.POST:
                    additional_details['form_data'] = self._mask_sensitive_params(dict(request.POST))
                
                if request.content_type == 'application/json' and hasattr(request, 'body'):
                    try:
                        json_data = json.loads(request.body.decode('utf-8'))
                        additional_details['json_data'] = self._mask_sensitive_json(json_data)
                    except:
                        pass
            
            # Log to audit trail
            audit_manager.log_action(
                user_id=request.user.id if request.user.is_authenticated else None,
                action_type=action_type,
                action_category=action_category,
                resource_type='http_request',
                resource_id=None,
                resource_name=request.path,
                action_description=f"{request.method} request to {request.path}",
                request=request,
                success=response.status_code < 400,
                error_message=f"HTTP {response.status_code}" if response.status_code >= 400 else None,
                execution_time_ms=int(duration * 1000),
                additional_details=additional_details
            )
        
        except Exception as e:
            logger.error(f"Failed to log to audit trail: {str(e)}")
    
    def _determine_action_type(self, request: HttpRequest, response: HttpResponse) -> tuple:
        """Determine action type and category for audit trail"""
        path = request.path.lower()
        method = request.method
        
        # Authentication actions
        if '/login' in path or '/auth/login' in path:
            return ('login', 'authentication')
        elif '/logout' in path or '/auth/logout' in path:
            return ('logout', 'authentication')
        elif '/register' in path or '/auth/register' in path:
            return ('register', 'authentication')
        
        # File operations
        elif '/upload' in path:
            return ('upload', 'data_management')
        elif '/download' in path:
            return ('download', 'data_management')
        
        # Analysis operations
        elif '/analysis' in path:
            return ('analysis', 'analysis')
        elif '/agent' in path:
            return ('agent_run', 'analysis')
        
        # Admin actions
        elif '/admin' in path:
            return ('admin_action', 'system')
        
        # API operations
        elif path.startswith('/api/'):
            if method == 'POST':
                return ('api_create', 'data_management')
            elif method == 'PUT':
                return ('api_update', 'data_management')
            elif method == 'PATCH':
                return ('api_partial_update', 'data_management')
            elif method == 'DELETE':
                return ('api_delete', 'data_management')
            else:
                return ('api_access', 'system')
        
        # Default
        return ('http_request', 'system')
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        # Check for forwarded IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return ip
    
    def _mask_sensitive_headers(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive headers"""
        if not self.mask_sensitive_data:
            return headers
        
        masked_headers = {}
        for key, value in headers.items():
            if key in self.SENSITIVE_HEADERS:
                masked_headers[key] = self._mask_value(str(value))
            else:
                masked_headers[key] = value
        
        return masked_headers
    
    def _mask_sensitive_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive parameters"""
        if not self.mask_sensitive_data:
            return params
        
        masked_params = {}
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in self.sensitive_params):
                masked_params[key] = self._mask_value(str(value))
            else:
                masked_params[key] = value
        
        return masked_params
    
    def _mask_sensitive_json(self, data: Any) -> Any:
        """Recursively mask sensitive data in JSON"""
        if not self.mask_sensitive_data:
            return data
        
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.sensitive_params):
                    masked_data[key] = self._mask_value(str(value))
                else:
                    masked_data[key] = self._mask_sensitive_json(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_json(item) for item in data]
        else:
            return data
    
    def _mask_value(self, value: str) -> str:
        """Mask a sensitive value"""
        if len(value) <= 4:
            return '*' * len(value)
        else:
            return value[:2] + '*' * (len(value) - 4) + value[-2:]


class SecurityEventLogger:
    """
    Specialized logger for security events
    """
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def log_authentication_attempt(self, request: HttpRequest, username: str, success: bool, reason: str = ''):
        """Log authentication attempts"""
        event_data = {
            'event_type': 'authentication_attempt',
            'username': username,
            'success': success,
            'reason': reason,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': timezone.now().isoformat(),
        }
        
        if success:
            self.logger.info(f"Successful authentication for {username}", extra={'security_event': event_data})
        else:
            self.logger.warning(f"Failed authentication for {username}: {reason}", extra={'security_event': event_data})
    
    def log_permission_denied(self, request: HttpRequest, resource: str, reason: str = ''):
        """Log permission denied events"""
        event_data = {
            'event_type': 'permission_denied',
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'resource': resource,
            'reason': reason,
            'ip_address': self._get_client_ip(request),
            'timestamp': timezone.now().isoformat(),
        }
        
        self.logger.warning(f"Permission denied for {event_data['user']} accessing {resource}", 
                          extra={'security_event': event_data})
    
    def log_suspicious_activity(self, request: HttpRequest, activity_type: str, details: Dict[str, Any]):
        """Log suspicious activities"""
        event_data = {
            'event_type': 'suspicious_activity',
            'activity_type': activity_type,
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'ip_address': self._get_client_ip(request),
            'timestamp': timezone.now().isoformat(),
            'details': details,
        }
        
        self.logger.warning(f"Suspicious activity detected: {activity_type}", 
                          extra={'security_event': event_data})
    
    def log_data_access(self, request: HttpRequest, resource_type: str, resource_id: str, action: str):
        """Log sensitive data access"""
        event_data = {
            'event_type': 'data_access',
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'ip_address': self._get_client_ip(request),
            'timestamp': timezone.now().isoformat(),
        }
        
        self.logger.info(f"Data access: {action} on {resource_type}:{resource_id}", 
                        extra={'security_event': event_data})
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


# Convenience functions
def get_security_logger() -> SecurityEventLogger:
    """Get security event logger instance"""
    return SecurityEventLogger()


def log_security_event(request: HttpRequest, event_type: str, details: Dict[str, Any]):
    """
    Convenience function to log security events
    
    Args:
        request: Django HttpRequest object
        event_type: Type of security event
        details: Event details dictionary
    """
    security_logger = SecurityEventLogger()
    security_logger.log_suspicious_activity(request, event_type, details)
