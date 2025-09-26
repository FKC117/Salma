"""
Input Validation Middleware

This middleware provides comprehensive input validation for all incoming requests,
including parameter validation, SQL injection prevention, XSS protection,
and data type validation.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, URLValidator
import bleach

logger = logging.getLogger(__name__)


class InputValidationMiddleware(MiddlewareMixin):
    """
    Comprehensive input validation middleware
    """
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bCREATE\b|\bALTER\b)',
        r'(\bOR\s+1\s*=\s*1\b|\bAND\s+1\s*=\s*1\b)',
        r'(\b--\b|\b#\b|/\*|\*/)',
        r'(\bxp_cmdshell\b|\bsp_executesql\b)',
        r'(\bEXEC\b|\bEXECUTE\b)(\s+|\()',
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r'(\beval\b|\bexec\b|\bsystem\b|\bshell_exec\b)',
        r'(\|\||&&|;|\||`)',
        r'(\$\(|\${)',
        r'(\bcat\b|\bls\b|\bpwd\b|\bwhoami\b|\bps\b)',
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./',
        r'\.\.\\',
        r'%2e%2e%2f',
        r'%2e%2e%5c',
    ]
    
    # Maximum lengths for different input types
    MAX_LENGTHS = {
        'username': 150,
        'email': 254,
        'password': 128,
        'filename': 255,
        'text_field': 1000,
        'textarea': 10000,
        'url': 2048,
        'json': 100000,  # 100KB
        'general': 500,
    }
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Load configuration
        self.validation_enabled = getattr(settings, 'INPUT_VALIDATION_ENABLED', True)
        self.strict_mode = getattr(settings, 'INPUT_VALIDATION_STRICT', False)
        self.log_violations = getattr(settings, 'INPUT_VALIDATION_LOG', True)
        
        # Exempt paths (admin, API docs, etc.)
        self.exempt_paths = getattr(settings, 'INPUT_VALIDATION_EXEMPT_PATHS', [
            '/admin/',
            '/api/docs/',
            '/static/',
            '/media/',
        ])
        
        # Initialize validators
        self.url_validator = URLValidator()
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process incoming request for validation"""
        if not self.validation_enabled:
            return None
        
        # Skip exempt paths
        if self._is_exempt_path(request.path):
            return None
        
        try:
            # Validate request parameters
            validation_result = self._validate_request(request)
            
            if not validation_result['is_valid']:
                return self._handle_validation_error(request, validation_result)
            
            # Store validation results in request for later use
            request.validation_result = validation_result
            
        except Exception as e:
            logger.error(f"Input validation error: {str(e)}")
            if self.strict_mode:
                return JsonResponse({
                    'error': 'Input validation failed',
                    'message': 'Request could not be validated'
                }, status=400)
        
        return None
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from validation"""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    def _validate_request(self, request: HttpRequest) -> Dict[str, Any]:
        """Comprehensive request validation"""
        validation_result = {
            'is_valid': True,
            'violations': [],
            'warnings': [],
            'sanitized_data': {},
            'validation_level': 'basic'
        }
        
        # Validate GET parameters
        if request.GET:
            get_validation = self._validate_parameters(dict(request.GET), 'GET')
            validation_result['violations'].extend(get_validation['violations'])
            validation_result['sanitized_data']['GET'] = get_validation['sanitized']
        
        # Validate POST parameters
        if request.POST:
            post_validation = self._validate_parameters(dict(request.POST), 'POST')
            validation_result['violations'].extend(post_validation['violations'])
            validation_result['sanitized_data']['POST'] = post_validation['sanitized']
        
        # Validate JSON body
        if request.content_type == 'application/json':
            json_validation = self._validate_json_body(request)
            validation_result['violations'].extend(json_validation['violations'])
            validation_result['sanitized_data']['JSON'] = json_validation['sanitized']
        
        # Validate headers
        header_validation = self._validate_headers(request)
        validation_result['violations'].extend(header_validation['violations'])
        
        # Validate file uploads
        if request.FILES:
            file_validation = self._validate_files(request.FILES)
            validation_result['violations'].extend(file_validation['violations'])
        
        # Determine if request is valid
        critical_violations = [v for v in validation_result['violations'] if v['severity'] == 'critical']
        validation_result['is_valid'] = len(critical_violations) == 0
        
        # Log violations if enabled
        if self.log_violations and validation_result['violations']:
            self._log_violations(request, validation_result['violations'])
        
        return validation_result
    
    def _validate_parameters(self, params: Dict[str, Any], param_type: str) -> Dict[str, Any]:
        """Validate GET/POST parameters"""
        violations = []
        sanitized = {}
        
        for key, value in params.items():
            # Convert list values to string for validation
            if isinstance(value, list):
                value = ' '.join(str(v) for v in value)
            
            value_str = str(value)
            
            # Length validation
            if len(value_str) > self.MAX_LENGTHS.get('general', 500):
                violations.append({
                    'type': 'length_exceeded',
                    'parameter': key,
                    'param_type': param_type,
                    'severity': 'warning',
                    'message': f'Parameter {key} exceeds maximum length'
                })
            
            # SQL injection detection
            sql_violations = self._detect_sql_injection(key, value_str)
            violations.extend(sql_violations)
            
            # XSS detection
            xss_violations = self._detect_xss(key, value_str)
            violations.extend(xss_violations)
            
            # Command injection detection
            cmd_violations = self._detect_command_injection(key, value_str)
            violations.extend(cmd_violations)
            
            # Path traversal detection
            path_violations = self._detect_path_traversal(key, value_str)
            violations.extend(path_violations)
            
            # Sanitize value
            sanitized[key] = self._sanitize_value(value_str)
        
        return {
            'violations': violations,
            'sanitized': sanitized
        }
    
    def _validate_json_body(self, request: HttpRequest) -> Dict[str, Any]:
        """Validate JSON request body"""
        violations = []
        sanitized = {}
        
        try:
            if hasattr(request, 'body') and request.body:
                # Check JSON size
                if len(request.body) > self.MAX_LENGTHS.get('json', 100000):
                    violations.append({
                        'type': 'json_too_large',
                        'severity': 'critical',
                        'message': 'JSON body exceeds maximum size'
                    })
                    return {'violations': violations, 'sanitized': {}}
                
                # Parse JSON
                json_data = json.loads(request.body.decode('utf-8'))
                
                # Recursively validate JSON structure
                sanitized = self._validate_json_recursive(json_data, violations)
        
        except json.JSONDecodeError as e:
            violations.append({
                'type': 'invalid_json',
                'severity': 'critical',
                'message': f'Invalid JSON format: {str(e)}'
            })
        except Exception as e:
            violations.append({
                'type': 'json_validation_error',
                'severity': 'warning',
                'message': f'JSON validation error: {str(e)}'
            })
        
        return {
            'violations': violations,
            'sanitized': sanitized
        }
    
    def _validate_json_recursive(self, data: Any, violations: List[Dict]) -> Any:
        """Recursively validate JSON data"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Validate key
                key_str = str(key)
                if len(key_str) > 100:  # Reasonable key length limit
                    violations.append({
                        'type': 'json_key_too_long',
                        'severity': 'warning',
                        'message': f'JSON key too long: {key_str[:50]}...'
                    })
                
                # Recursively validate value
                sanitized[key] = self._validate_json_recursive(value, violations)
            return sanitized
        
        elif isinstance(data, list):
            return [self._validate_json_recursive(item, violations) for item in data]
        
        elif isinstance(data, str):
            # Validate string values
            if len(data) > self.MAX_LENGTHS.get('text_field', 1000):
                violations.append({
                    'type': 'json_string_too_long',
                    'severity': 'warning',
                    'message': f'JSON string value too long'
                })
            
            # Check for malicious patterns
            self._detect_sql_injection('json_value', data, violations)
            self._detect_xss('json_value', data, violations)
            self._detect_command_injection('json_value', data, violations)
            
            return self._sanitize_value(data)
        
        else:
            return data
    
    def _validate_headers(self, request: HttpRequest) -> Dict[str, Any]:
        """Validate HTTP headers"""
        violations = []
        
        # Check for suspicious headers
        suspicious_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'X-Originating-IP',
        ]
        
        for header in suspicious_headers:
            value = request.META.get(f'HTTP_{header.upper().replace("-", "_")}')
            if value:
                # Validate IP format if it's an IP header
                if 'IP' in header:
                    if not self._is_valid_ip(value):
                        violations.append({
                            'type': 'invalid_ip_header',
                            'header': header,
                            'severity': 'warning',
                            'message': f'Invalid IP format in {header}: {value}'
                        })
        
        # Check User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if len(user_agent) > 1000:  # Reasonable User-Agent length
            violations.append({
                'type': 'user_agent_too_long',
                'severity': 'warning',
                'message': 'User-Agent header too long'
            })
        
        return {'violations': violations}
    
    def _validate_files(self, files: Dict) -> Dict[str, Any]:
        """Validate uploaded files"""
        violations = []
        
        for field_name, uploaded_file in files.items():
            # Check filename
            if hasattr(uploaded_file, 'name') and uploaded_file.name:
                filename = uploaded_file.name
                
                # Check for path traversal in filename
                if self._detect_path_traversal_in_string(filename):
                    violations.append({
                        'type': 'malicious_filename',
                        'field': field_name,
                        'severity': 'critical',
                        'message': f'Malicious filename detected: {filename}'
                    })
                
                # Check filename length
                if len(filename) > self.MAX_LENGTHS.get('filename', 255):
                    violations.append({
                        'type': 'filename_too_long',
                        'field': field_name,
                        'severity': 'warning',
                        'message': f'Filename too long: {filename}'
                    })
        
        return {'violations': violations}
    
    def _detect_sql_injection(self, param_name: str, value: str, violations: List[Dict] = None) -> List[Dict]:
        """Detect SQL injection patterns"""
        if violations is None:
            violations = []
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                violations.append({
                    'type': 'sql_injection',
                    'parameter': param_name,
                    'severity': 'critical',
                    'message': f'Potential SQL injection detected in {param_name}',
                    'pattern': pattern,
                    'value_snippet': value[:100]
                })
        
        return violations
    
    def _detect_xss(self, param_name: str, value: str, violations: List[Dict] = None) -> List[Dict]:
        """Detect XSS patterns"""
        if violations is None:
            violations = []
        
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                violations.append({
                    'type': 'xss_attempt',
                    'parameter': param_name,
                    'severity': 'critical',
                    'message': f'Potential XSS attempt detected in {param_name}',
                    'pattern': pattern,
                    'value_snippet': value[:100]
                })
        
        return violations
    
    def _detect_command_injection(self, param_name: str, value: str, violations: List[Dict] = None) -> List[Dict]:
        """Detect command injection patterns"""
        if violations is None:
            violations = []
        
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                violations.append({
                    'type': 'command_injection',
                    'parameter': param_name,
                    'severity': 'critical',
                    'message': f'Potential command injection detected in {param_name}',
                    'pattern': pattern,
                    'value_snippet': value[:100]
                })
        
        return violations
    
    def _detect_path_traversal(self, param_name: str, value: str, violations: List[Dict] = None) -> List[Dict]:
        """Detect path traversal patterns"""
        if violations is None:
            violations = []
        
        if self._detect_path_traversal_in_string(value):
            violations.append({
                'type': 'path_traversal',
                'parameter': param_name,
                'severity': 'critical',
                'message': f'Path traversal attempt detected in {param_name}',
                'value_snippet': value[:100]
            })
        
        return violations
    
    def _detect_path_traversal_in_string(self, value: str) -> bool:
        """Check if string contains path traversal patterns"""
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def _sanitize_value(self, value: str) -> str:
        """Sanitize input value"""
        # HTML escape and clean
        sanitized = bleach.clean(value, tags=[], attributes={}, strip=True)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _handle_validation_error(self, request: HttpRequest, validation_result: Dict[str, Any]) -> HttpResponse:
        """Handle validation errors"""
        critical_violations = [v for v in validation_result['violations'] if v['severity'] == 'critical']
        
        if critical_violations:
            # Log security incident
            logger.warning(f"Security violation detected from {request.META.get('REMOTE_ADDR', 'unknown')}: "
                         f"{len(critical_violations)} critical violations")
            
            # Return appropriate error response
            if request.content_type == 'application/json' or request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Input validation failed',
                    'message': 'Request contains potentially malicious content',
                    'violations': len(critical_violations)
                }, status=400)
            else:
                # For web requests, return a simple error page
                return HttpResponse(
                    '<h1>Bad Request</h1><p>Your request could not be processed due to security restrictions.</p>',
                    status=400,
                    content_type='text/html'
                )
        
        return None
    
    def _log_violations(self, request: HttpRequest, violations: List[Dict[str, Any]]):
        """Log validation violations"""
        for violation in violations:
            log_data = {
                'violation_type': violation['type'],
                'severity': violation['severity'],
                'parameter': violation.get('parameter', 'unknown'),
                'message': violation['message'],
                'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                'path': request.path,
                'method': request.method,
            }
            
            if violation['severity'] == 'critical':
                logger.warning(f"Security violation: {log_data}")
            else:
                logger.info(f"Input validation warning: {log_data}")


# Utility functions for manual validation
def validate_input_string(value: str, max_length: int = 500, allow_html: bool = False) -> Dict[str, Any]:
    """
    Utility function to validate a single string input
    
    Args:
        value: String to validate
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags
        
    Returns:
        Validation result dictionary
    """
    validator = InputValidationMiddleware(lambda r: None)
    violations = []
    
    # Length check
    if len(value) > max_length:
        violations.append({
            'type': 'length_exceeded',
            'severity': 'warning',
            'message': f'String exceeds maximum length of {max_length}'
        })
    
    # Security checks
    validator._detect_sql_injection('input', value, violations)
    validator._detect_xss('input', value, violations)
    validator._detect_command_injection('input', value, violations)
    validator._detect_path_traversal('input', value, violations)
    
    # Sanitize
    sanitized = validator._sanitize_value(value)
    if not allow_html:
        sanitized = bleach.clean(sanitized, tags=[], attributes={}, strip=True)
    
    return {
        'is_valid': len([v for v in violations if v['severity'] == 'critical']) == 0,
        'violations': violations,
        'sanitized_value': sanitized,
        'original_length': len(value),
        'sanitized_length': len(sanitized)
    }


def validate_email_input(email: str) -> Dict[str, Any]:
    """
    Validate email input
    
    Args:
        email: Email string to validate
        
    Returns:
        Validation result dictionary
    """
    violations = []
    
    # Basic validation
    basic_result = validate_input_string(email, max_length=254)
    violations.extend(basic_result['violations'])
    
    # Email format validation
    try:
        validate_email(email)
        email_valid = True
    except ValidationError:
        email_valid = False
        violations.append({
            'type': 'invalid_email',
            'severity': 'critical',
            'message': 'Invalid email format'
        })
    
    return {
        'is_valid': email_valid and basic_result['is_valid'],
        'violations': violations,
        'sanitized_value': basic_result['sanitized_value']
    }


def validate_url_input(url: str) -> Dict[str, Any]:
    """
    Validate URL input
    
    Args:
        url: URL string to validate
        
    Returns:
        Validation result dictionary
    """
    violations = []
    
    # Basic validation
    basic_result = validate_input_string(url, max_length=2048)
    violations.extend(basic_result['violations'])
    
    # URL format validation
    url_validator = URLValidator()
    try:
        url_validator(url)
        url_valid = True
    except ValidationError:
        url_valid = False
        violations.append({
            'type': 'invalid_url',
            'severity': 'critical',
            'message': 'Invalid URL format'
        })
    
    return {
        'is_valid': url_valid and basic_result['is_valid'],
        'violations': violations,
        'sanitized_value': basic_result['sanitized_value']
    }
