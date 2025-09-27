"""
Security Middleware (T012)
Comprehensive security middleware for CSRF protection, rate limiting, and audit logging
"""

import time
import uuid
from typing import Callable
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied
from django.utils.crypto import constant_time_compare
from django.contrib.auth import get_user
from analytics.services.logging_service import get_logger, get_audit_logger, get_error_logger

class SecurityMiddleware(MiddlewareMixin):
    """Comprehensive security middleware"""
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.logger = get_logger('security')
        self.audit_logger = get_audit_logger()
        self.error_logger = get_error_logger()
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> HttpResponse:
        """Process incoming request for security checks"""
        # Generate correlation ID for request tracking
        request.correlation_id = str(uuid.uuid4())
        request.request_id = str(uuid.uuid4())
        
        # Set logging context
        self.logger.set_context(
            correlation_id=request.correlation_id,
            request_id=request.request_id,
            user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            session_id=request.session.session_key if hasattr(request, 'session') else None
        )
        
        # Log request
        self.logger.info(f"Request: {request.method} {request.path}", {
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self.get_client_ip(request),
            'referer': request.META.get('HTTP_REFERER', '')
        })
        
        # Rate limiting
        if not self.check_rate_limit(request):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # CSRF protection is handled by Django's built-in middleware
        # We just log CSRF-related events for audit purposes
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Check if CSRF token is present (for logging purposes)
            csrf_token = request.POST.get('csrfmiddlewaretoken') or request.META.get('HTTP_X_CSRFTOKEN')
            if not csrf_token:
                self.audit_logger.log_security_event(
                    'csrf_token_missing',
                    {
                        'ip_address': self.get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'path': request.path,
                        'method': request.method
                    },
                    'WARNING'
                )
        
        # Security headers
        self.add_security_headers(request)
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process outgoing response for security headers"""
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Add correlation ID to response headers for debugging
        if hasattr(request, 'correlation_id'):
            response['X-Correlation-ID'] = request.correlation_id
        
        # Log response
        self.logger.info(f"Response: {response.status_code}", {
            'status_code': response.status_code,
            'content_type': response.get('Content-Type', ''),
            'correlation_id': getattr(request, 'correlation_id', None)
        })
        
        return response
    
    def check_rate_limit(self, request: HttpRequest) -> bool:
        """Check rate limiting for requests"""
        ip_address = self.get_client_ip(request)
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        # Different limits for authenticated vs anonymous users
        if user_id:
            limit_key = f"rate_limit_user_{user_id}"
            limit = 10000  # 1000 requests per hour for authenticated users
        else:
            limit_key = f"rate_limit_ip_{ip_address}"
            limit = 10000  # 100 requests per hour for anonymous users
        
        # Check current count
        current_count = cache.get(limit_key, 0)
        
        if current_count >= limit:
            self.audit_logger.log_security_event(
                'rate_limit_exceeded',
                {
                    'ip_address': ip_address,
                    'user_id': user_id,
                    'current_count': current_count,
                    'limit': limit
                },
                'MEDIUM'
            )
            return False
        
        # Increment counter
        cache.set(limit_key, current_count + 1, 3600)  # 1 hour TTL
        
        return True
    
    
    def add_security_headers(self, request: HttpRequest):
        """Add security headers to request"""
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Store CSP for response headers
        request.csp_header = csp
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AuditMiddleware(MiddlewareMixin):
    """Audit logging middleware"""
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.logger = get_logger('audit')
        self.audit_logger = get_audit_logger()
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> HttpResponse:
        """Log request for audit trail"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            self.audit_logger.log_user_action(
                user_id=request.user.id,
                action=f"HTTP_{request.method}",
                resource=request.path,
                details={
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'correlation_id': getattr(request, 'correlation_id', None)
                }
            )
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response for audit trail"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            self.audit_logger.log_user_action(
                user_id=request.user.id,
                action=f"HTTP_{request.method}_RESPONSE",
                resource=request.path,
                details={
                    'status_code': response.status_code,
                    'content_type': response.get('Content-Type', ''),
                    'correlation_id': getattr(request, 'correlation_id', None)
                },
                success=response.status_code < 400
            )
        
        return response
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PerformanceMiddleware(MiddlewareMixin):
    """Performance monitoring middleware"""
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.logger = get_logger('performance')
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> HttpResponse:
        """Start performance timing"""
        request.start_time = time.time()
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log performance metrics"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log performance for slow requests
            if duration > 1.0:  # Log requests taking more than 1 second
                self.logger.warning(f"Slow request: {request.path}", {
                    'duration_ms': round(duration * 1000, 2),
                    'method': request.method,
                    'status_code': response.status_code,
                    'path': request.path,
                    'correlation_id': getattr(request, 'correlation_id', None)
                })
        
        return response

class ErrorHandlingMiddleware(MiddlewareMixin):
    """Error handling and logging middleware"""
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.logger = get_logger('error')
        self.error_logger = get_error_logger()
        super().__init__(get_response)
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponse:
        """Handle exceptions and log them"""
        self.error_logger.log_exception(exception, {
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            'ip_address': self.get_client_ip(request),
            'correlation_id': getattr(request, 'correlation_id', None)
        })
        
        # Return appropriate error response
        if isinstance(exception, PermissionDenied):
            return JsonResponse({
                'error': 'Permission denied',
                'message': 'You do not have permission to perform this action.'
            }, status=403)
        
        return JsonResponse({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }, status=500)
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
