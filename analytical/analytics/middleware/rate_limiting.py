"""
Rate Limiting Middleware

This middleware provides comprehensive rate limiting for API endpoints and user actions,
including per-user limits, per-IP limits, endpoint-specific limits, and sliding window
rate limiting using Redis for distributed systems.
"""

import time
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache, caches
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)
User = get_user_model()


class RateLimitingMiddleware(MiddlewareMixin):
    """
    Advanced rate limiting middleware with multiple strategies
    """
    
    # Default rate limits (requests per time window)
    DEFAULT_LIMITS = {
        # General API limits
        'api_general': {'requests': 1000, 'window': 3600},  # 1000 req/hour
        'api_auth': {'requests': 100, 'window': 3600},      # 100 auth req/hour
        
        # File upload limits
        'file_upload': {'requests': 50, 'window': 3600},    # 50 uploads/hour
        'file_large': {'requests': 10, 'window': 3600},     # 10 large files/hour
        
        # Analysis limits
        'analysis_execute': {'requests': 200, 'window': 3600},  # 200 analysis/hour
        'analysis_heavy': {'requests': 20, 'window': 3600},     # 20 heavy analysis/hour
        
        # AI/LLM limits
        'llm_chat': {'requests': 500, 'window': 3600},      # 500 chat messages/hour
        'llm_analysis': {'requests': 100, 'window': 3600},  # 100 AI analysis/hour
        
        # Agent limits
        'agent_run': {'requests': 50, 'window': 3600},      # 50 agent runs/hour
        'agent_expensive': {'requests': 10, 'window': 3600}, # 10 expensive runs/hour
        
        # Per-IP limits (for anonymous users)
        'ip_general': {'requests': 500, 'window': 3600},    # 500 req/hour per IP
        'ip_strict': {'requests': 100, 'window': 3600},     # 100 req/hour for sensitive endpoints
    }
    
    # Endpoint to rate limit mapping
    ENDPOINT_LIMITS = {
        # Authentication endpoints
        '/api/auth/login/': 'api_auth',
        '/api/auth/register/': 'api_auth',
        '/accounts/login/': 'api_auth',
        
        # File upload endpoints
        '/api/upload/': 'file_upload',
        '/api/upload/large/': 'file_large',
        
        # Analysis endpoints
        '/api/analysis/execute/': 'analysis_execute',
        '/api/analysis/heavy/': 'analysis_heavy',
        
        # AI endpoints
        '/api/chat/': 'llm_chat',
        '/api/llm/': 'llm_analysis',
        
        # Agent endpoints
        '/api/agent/run/': 'agent_run',
        '/api/agent/expensive/': 'agent_expensive',
    }
    
    # Burst limits (short-term limits)
    BURST_LIMITS = {
        'api_general': {'requests': 100, 'window': 60},     # 100 req/minute
        'file_upload': {'requests': 10, 'window': 60},     # 10 uploads/minute
        'llm_chat': {'requests': 30, 'window': 60},        # 30 messages/minute
        'agent_run': {'requests': 5, 'window': 60},        # 5 agent runs/minute
    }
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Load configuration
        self.rate_limiting_enabled = getattr(settings, 'RATE_LIMITING_ENABLED', True)
        self.use_redis = getattr(settings, 'RATE_LIMITING_USE_REDIS', True)
        self.strict_mode = getattr(settings, 'RATE_LIMITING_STRICT', False)
        self.is_development = getattr(settings, 'DEBUG', False)
        
        # Custom limits from settings
        self.custom_limits = getattr(settings, 'RATE_LIMITS', {})
        self.limits = {**self.DEFAULT_LIMITS, **self.custom_limits}
        
        # In development mode, increase limits significantly
        if self.is_development:
            self.limits = {
                'api_general': {'requests': 10000, 'window': 3600},  # 10K req/hour
                'api_auth': {'requests': 1000, 'window': 3600},     # 1K auth req/hour
                'file_upload': {'requests': 500, 'window': 3600},  # 500 uploads/hour
                'file_large': {'requests': 100, 'window': 3600},   # 100 large files/hour
                'analysis_execute': {'requests': 2000, 'window': 3600},  # 2K analysis/hour
                'analysis_heavy': {'requests': 200, 'window': 3600},     # 200 heavy analysis/hour
                'llm_chat': {'requests': 5000, 'window': 3600},   # 5K chat messages/hour
                'llm_analysis': {'requests': 1000, 'window': 3600},  # 1K AI analysis/hour
                'agent_run': {'requests': 500, 'window': 3600},    # 500 agent runs/hour
                'agent_expensive': {'requests': 100, 'window': 3600}, # 100 expensive runs/hour
                'ip_general': {'requests': 5000, 'window': 3600},  # 5K req/hour per IP
                'ip_strict': {'requests': 1000, 'window': 3600},   # 1K req/hour for sensitive endpoints
            }
        
        # Exempt paths
        self.exempt_paths = getattr(settings, 'RATE_LIMITING_EXEMPT_PATHS', [
            '/admin/',
            '/static/',
            '/media/',
            '/health/',
            '/metrics/',
        ])
        
        # Cache backend
        if self.use_redis:
            try:
                self.cache = caches['default']
                self.cache_prefix = 'analytical:ratelimit'
            except:
                logger.warning("Redis not available, falling back to default cache")
                self.cache = cache
                self.cache_prefix = 'ratelimit'
        else:
            self.cache = cache
            self.cache_prefix = 'ratelimit'
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process request for rate limiting"""
        if not self.rate_limiting_enabled:
            return None
        
        # Skip exempt paths
        if self._is_exempt_path(request.path):
            return None
        
        try:
            # Check rate limits
            rate_limit_result = self._check_rate_limits(request)
            
            if not rate_limit_result['allowed']:
                return self._handle_rate_limit_exceeded(request, rate_limit_result)
            
            # Store rate limit info in request
            request.rate_limit_info = rate_limit_result
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            if self.strict_mode:
                return JsonResponse({
                    'error': 'Rate limiting failed',
                    'message': 'Request could not be processed'
                }, status=500)
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process response to add rate limit headers"""
        if not self.rate_limiting_enabled or not hasattr(request, 'rate_limit_info'):
            return response
        
        try:
            # Add rate limit headers
            rate_info = request.rate_limit_info
            
            response['X-RateLimit-Limit'] = str(rate_info.get('limit', 0))
            response['X-RateLimit-Remaining'] = str(rate_info.get('remaining', 0))
            response['X-RateLimit-Reset'] = str(rate_info.get('reset_time', 0))
            response['X-RateLimit-Window'] = str(rate_info.get('window', 0))
            
            if 'retry_after' in rate_info:
                response['Retry-After'] = str(rate_info['retry_after'])
        
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {str(e)}")
        
        return response
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from rate limiting"""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    def _check_rate_limits(self, request: HttpRequest) -> Dict[str, Any]:
        """Check all applicable rate limits"""
        # Determine rate limit categories
        limit_categories = self._get_limit_categories(request)
        
        # Get identifier (user ID or IP)
        identifier = self._get_identifier(request)
        
        # Check each applicable limit
        for category in limit_categories:
            limit_result = self._check_single_limit(request, identifier, category)
            
            if not limit_result['allowed']:
                return limit_result
        
        # All limits passed
        return {
            'allowed': True,
            'limit': max([self.limits[cat]['requests'] for cat in limit_categories]),
            'remaining': min([self._get_remaining_requests(identifier, cat) for cat in limit_categories]),
            'reset_time': max([self._get_reset_time(identifier, cat) for cat in limit_categories]),
            'window': max([self.limits[cat]['window'] for cat in limit_categories]),
        }
    
    def _get_limit_categories(self, request: HttpRequest) -> List[str]:
        """Determine which rate limit categories apply to this request"""
        categories = []
        
        # Check endpoint-specific limits
        for endpoint, category in self.ENDPOINT_LIMITS.items():
            if request.path.startswith(endpoint):
                categories.append(category)
                break
        
        # Add general limits only for API endpoints
        if request.path.startswith('/api/'):
            categories.append('api_general')
        
        # Add IP-based limits for anonymous users only on API endpoints
        if not request.user.is_authenticated and request.path.startswith('/api/'):
            if any(request.path.startswith(ep) for ep in ['/api/auth/', '/api/upload/']):
                categories.append('ip_strict')
            else:
                categories.append('ip_general')
        
        # In development mode, be more lenient - don't apply default limits to non-API paths
        if not categories and not request.path.startswith('/api/'):
            # For non-API paths in development, return empty list (no rate limiting)
            return []
        
        # Default to general API limit only for API endpoints
        if not categories and request.path.startswith('/api/'):
            categories.append('api_general')
        
        return categories
    
    def _get_identifier(self, request: HttpRequest) -> str:
        """Get unique identifier for rate limiting"""
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        else:
            # Use IP address for anonymous users
            ip = self._get_client_ip(request)
            return f"ip:{ip}"
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        # Check for forwarded IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return ip
    
    def _check_single_limit(self, request: HttpRequest, identifier: str, category: str) -> Dict[str, Any]:
        """Check a single rate limit category"""
        if category not in self.limits:
            return {'allowed': True}
        
        limit_config = self.limits[category]
        requests_limit = limit_config['requests']
        window_seconds = limit_config['window']
        
        # Check main limit
        main_result = self._check_sliding_window(identifier, category, requests_limit, window_seconds)
        
        if not main_result['allowed']:
            return main_result
        
        # Check burst limit if exists
        if category in self.BURST_LIMITS:
            burst_config = self.BURST_LIMITS[category]
            burst_result = self._check_sliding_window(
                identifier, f"{category}:burst", 
                burst_config['requests'], 
                burst_config['window']
            )
            
            if not burst_result['allowed']:
                return {
                    **burst_result,
                    'limit_type': 'burst',
                    'burst_limit': True
                }
        
        return main_result
    
    def _check_sliding_window(self, identifier: str, category: str, limit: int, window: int) -> Dict[str, Any]:
        """Implement sliding window rate limiting"""
        current_time = int(time.time())
        window_start = current_time - window
        
        # Create cache key
        cache_key = f"{self.cache_prefix}:{identifier}:{category}"
        
        try:
            # Get current requests in window
            requests_data = self.cache.get(cache_key, [])
            
            # Filter requests within current window
            current_requests = [req_time for req_time in requests_data if req_time > window_start]
            
            # Check if limit exceeded
            if len(current_requests) >= limit:
                # Calculate retry after
                oldest_request = min(current_requests) if current_requests else current_time
                retry_after = max(0, oldest_request + window - current_time)
                
                return {
                    'allowed': False,
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': oldest_request + window,
                    'retry_after': retry_after,
                    'window': window,
                    'category': category
                }
            
            # Add current request
            current_requests.append(current_time)
            
            # Store updated requests list
            self.cache.set(cache_key, current_requests, window + 60)  # Extra 60s buffer
            
            # Calculate remaining requests
            remaining = max(0, limit - len(current_requests))
            
            return {
                'allowed': True,
                'limit': limit,
                'remaining': remaining,
                'reset_time': current_time + window,
                'window': window,
                'category': category
            }
        
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Fail open in case of cache errors
            return {'allowed': True}
    
    def _get_remaining_requests(self, identifier: str, category: str) -> int:
        """Get remaining requests for a category"""
        if category not in self.limits:
            return 0
        
        limit_config = self.limits[category]
        current_time = int(time.time())
        window_start = current_time - limit_config['window']
        
        cache_key = f"{self.cache_prefix}:{identifier}:{category}"
        
        try:
            requests_data = self.cache.get(cache_key, [])
            current_requests = [req_time for req_time in requests_data if req_time > window_start]
            return max(0, limit_config['requests'] - len(current_requests))
        except:
            return 0
    
    def _get_reset_time(self, identifier: str, category: str) -> int:
        """Get reset time for a category"""
        if category not in self.limits:
            return 0
        
        current_time = int(time.time())
        return current_time + self.limits[category]['window']
    
    def _handle_rate_limit_exceeded(self, request: HttpRequest, rate_result: Dict[str, Any]) -> HttpResponse:
        """Handle rate limit exceeded"""
        # Log rate limit violation
        identifier = self._get_identifier(request)
        logger.warning(f"Rate limit exceeded for {identifier} on {request.path}: {rate_result}")
        
        # Prepare error response
        error_data = {
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'limit': rate_result.get('limit', 0),
            'remaining': 0,
            'reset_time': rate_result.get('reset_time', 0),
            'retry_after': rate_result.get('retry_after', 60)
        }
        
        # Add burst limit info if applicable
        if rate_result.get('burst_limit'):
            error_data['message'] = 'Too many requests in a short time. Please slow down.'
            error_data['limit_type'] = 'burst'
        
        # Return JSON response for API requests
        if request.path.startswith('/api/') or request.content_type == 'application/json':
            response = JsonResponse(error_data, status=429)
        else:
            # Return HTML response for web requests
            html_content = f"""
            <html>
            <head><title>Rate Limited</title></head>
            <body>
                <h1>Rate Limited</h1>
                <p>{error_data['message']}</p>
                <p>Please try again in {error_data['retry_after']} seconds.</p>
            </body>
            </html>
            """
            response = HttpResponse(html_content, status=429, content_type='text/html')
        
        # Add rate limit headers
        response['X-RateLimit-Limit'] = str(rate_result.get('limit', 0))
        response['X-RateLimit-Remaining'] = '0'
        response['X-RateLimit-Reset'] = str(rate_result.get('reset_time', 0))
        response['Retry-After'] = str(rate_result.get('retry_after', 60))
        
        return response


class RateLimitManager:
    """
    Utility class for managing rate limits programmatically
    """
    
    def __init__(self):
        self.middleware = RateLimitingMiddleware(lambda r: None)
    
    def check_user_limit(self, user_id: int, category: str) -> Dict[str, Any]:
        """Check rate limit for a specific user"""
        identifier = f"user:{user_id}"
        
        if category not in self.middleware.limits:
            return {'error': f'Unknown rate limit category: {category}'}
        
        limit_config = self.middleware.limits[category]
        return self.middleware._check_sliding_window(
            identifier, category, 
            limit_config['requests'], 
            limit_config['window']
        )
    
    def check_ip_limit(self, ip_address: str, category: str) -> Dict[str, Any]:
        """Check rate limit for a specific IP"""
        identifier = f"ip:{ip_address}"
        
        if category not in self.middleware.limits:
            return {'error': f'Unknown rate limit category: {category}'}
        
        limit_config = self.middleware.limits[category]
        return self.middleware._check_sliding_window(
            identifier, category, 
            limit_config['requests'], 
            limit_config['window']
        )
    
    def reset_user_limits(self, user_id: int, category: Optional[str] = None) -> Dict[str, Any]:
        """Reset rate limits for a user"""
        identifier = f"user:{user_id}"
        reset_count = 0
        
        try:
            if category:
                # Reset specific category
                cache_key = f"{self.middleware.cache_prefix}:{identifier}:{category}"
                self.middleware.cache.delete(cache_key)
                reset_count = 1
            else:
                # Reset all categories (this is expensive, use sparingly)
                for cat in self.middleware.limits.keys():
                    cache_key = f"{self.middleware.cache_prefix}:{identifier}:{cat}"
                    self.middleware.cache.delete(cache_key)
                    reset_count += 1
            
            return {
                'success': True,
                'reset_count': reset_count,
                'message': f'Reset {reset_count} rate limit categories for user {user_id}'
            }
        
        except Exception as e:
            logger.error(f"Failed to reset rate limits: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_rate_limit_status(self, user_id: Optional[int] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive rate limit status"""
        if user_id:
            identifier = f"user:{user_id}"
        elif ip_address:
            identifier = f"ip:{ip_address}"
        else:
            return {'error': 'Either user_id or ip_address is required'}
        
        status = {}
        current_time = int(time.time())
        
        for category, config in self.middleware.limits.items():
            try:
                cache_key = f"{self.middleware.cache_prefix}:{identifier}:{category}"
                requests_data = self.middleware.cache.get(cache_key, [])
                
                window_start = current_time - config['window']
                current_requests = [req_time for req_time in requests_data if req_time > window_start]
                
                remaining = max(0, config['requests'] - len(current_requests))
                reset_time = current_time + config['window']
                
                status[category] = {
                    'limit': config['requests'],
                    'window': config['window'],
                    'used': len(current_requests),
                    'remaining': remaining,
                    'reset_time': reset_time,
                    'percentage_used': (len(current_requests) / config['requests']) * 100
                }
            
            except Exception as e:
                status[category] = {'error': str(e)}
        
        return {
            'identifier': identifier,
            'timestamp': current_time,
            'limits': status
        }


# Utility decorator for rate limiting specific views
def rate_limit(category: str, requests: Optional[int] = None, window: Optional[int] = None):
    """
    Decorator to apply rate limiting to specific views
    
    Args:
        category: Rate limit category name
        requests: Number of requests allowed (optional, uses default if not specified)
        window: Time window in seconds (optional, uses default if not specified)
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Create temporary middleware instance
            middleware = RateLimitingMiddleware(lambda r: None)
            
            # Override limits if specified
            if requests and window:
                middleware.limits[f"custom_{category}"] = {
                    'requests': requests,
                    'window': window
                }
                category_name = f"custom_{category}"
            else:
                category_name = category
            
            # Check rate limit
            identifier = middleware._get_identifier(request)
            result = middleware._check_single_limit(request, identifier, category_name)
            
            if not result['allowed']:
                return middleware._handle_rate_limit_exceeded(request, result)
            
            # Store rate limit info
            request.rate_limit_info = result
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# Convenience functions
def get_rate_limit_manager() -> RateLimitManager:
    """Get rate limit manager instance"""
    return RateLimitManager()


def check_rate_limit(request: HttpRequest, category: str) -> Dict[str, Any]:
    """
    Check rate limit for a request
    
    Args:
        request: Django HttpRequest object
        category: Rate limit category
        
    Returns:
        Rate limit check result
    """
    manager = RateLimitManager()
    
    if request.user.is_authenticated:
        return manager.check_user_limit(request.user.id, category)
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        return manager.check_ip_limit(ip, category)
