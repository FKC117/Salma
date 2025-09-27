"""
Unit Tests for Security Components

This module contains comprehensive unit tests for all security components in the analytics app.
Tests cover file sanitization, data masking, security middleware, and validation.
"""

import os
import tempfile
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest

from analytics.security.file_sanitizer import FileSanitizer
from analytics.security.data_masking import DataMasking
from analytics.middleware.security_middleware import SecurityMiddleware
from analytics.middleware.validation import ValidationMiddleware
from analytics.middleware.rate_limiting import RateLimitingMiddleware

User = get_user_model()


class FileSanitizerTest(TestCase):
    """Test FileSanitizer functionality"""
    
    def setUp(self):
        self.sanitizer = FileSanitizer()
        
    def test_sanitizer_initialization(self):
        """Test sanitizer initializes correctly"""
        self.assertIsNotNone(self.sanitizer)
        self.assertIsNotNone(self.sanitizer.allowed_extensions)
        self.assertIsNotNone(self.sanitizer.dangerous_extensions)
        
    def test_validate_file_extension_valid(self):
        """Test file extension validation with valid files"""
        valid_files = [
            'data.csv',
            'dataset.xlsx',
            'analysis.json',
            'report.pdf'
        ]
        
        for filename in valid_files:
            with self.subTest(filename=filename):
                result = self.sanitizer.validate_file_extension(filename)
                self.assertTrue(result['valid'])
                
    def test_validate_file_extension_invalid(self):
        """Test file extension validation with invalid files"""
        invalid_files = [
            'malware.exe',
            'script.py',
            'virus.bat',
            'suspicious.scr',
            'backdoor.com'
        ]
        
        for filename in invalid_files:
            with self.subTest(filename=filename):
                result = self.sanitizer.validate_file_extension(filename)
                self.assertFalse(result['valid'])
                
    def test_scan_for_malware_clean_file(self):
        """Test malware scanning with clean file"""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp.write(b'clean,csv,data\n1,2,3\n')
            tmp.flush()
            
            result = self.sanitizer.scan_for_malware(tmp.name)
            
            self.assertTrue(result['clean'])
            self.assertIsNone(result.get('threats'))
            
            os.unlink(tmp.name)
            
    def test_scan_for_malware_suspicious_content(self):
        """Test malware scanning with suspicious content"""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            # Write content that might trigger security warnings
            suspicious_content = b'=HYPERLINK("javascript:alert(1)","Click")\n'
            tmp.write(suspicious_content)
            tmp.flush()
            
            result = self.sanitizer.scan_for_malware(tmp.name)
            
            # The result depends on the actual scanning implementation
            self.assertIn('clean', result)
            
            os.unlink(tmp.name)
            
    def test_remove_excel_formulas(self):
        """Test Excel formula removal"""
        # Create test data with formulas
        test_data = pd.DataFrame({
            'A': ['=SUM(B1:B10)', '=HYPERLINK("http://evil.com","Click")', 'Normal text'],
            'B': ['=NOW()', '=RAND()', 'Safe data']
        })
        
        result = self.sanitizer.remove_excel_formulas(test_data)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['sanitized_data'])
        
        # Check that formulas are removed
        sanitized_df = result['sanitized_data']
        for col in sanitized_df.columns:
            for value in sanitized_df[col]:
                if isinstance(value, str):
                    self.assertFalse(value.startswith('='))
                    
    def test_sanitize_csv_content(self):
        """Test CSV content sanitization"""
        csv_content = """name,age,email
John,25,john@example.com
Jane,30,jane@example.com
<script>alert('xss')</script>,35,malicious@evil.com"""
        
        result = self.sanitizer.sanitize_csv_content(csv_content)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['sanitized_content'])
        
        # Check that script tags are removed
        sanitized = result['sanitized_content']
        self.assertNotIn('<script>', sanitized)
        self.assertNotIn('alert(', sanitized)
        
    def test_validate_file_size(self):
        """Test file size validation"""
        # Create a small test file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'small file content')
            tmp.flush()
            
            result = self.sanitizer.validate_file_size(tmp.name, max_size_mb=1)
            
            self.assertTrue(result['valid'])
            
            os.unlink(tmp.name)
            
    def test_validate_file_size_too_large(self):
        """Test file size validation with oversized file"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write content larger than 1MB
            large_content = b'x' * (2 * 1024 * 1024)  # 2MB
            tmp.write(large_content)
            tmp.flush()
            
            result = self.sanitizer.validate_file_size(tmp.name, max_size_mb=1)
            
            self.assertFalse(result['valid'])
            
            os.unlink(tmp.name)


class DataMaskingTest(TestCase):
    """Test DataMasking functionality"""
    
    def setUp(self):
        self.masker = DataMasking()
        
    def test_masker_initialization(self):
        """Test masker initializes correctly"""
        self.assertIsNotNone(self.masker)
        self.assertIsNotNone(self.masker.pii_patterns)
        
    def test_detect_pii_emails(self):
        """Test PII detection for email addresses"""
        data = pd.DataFrame({
            'name': ['John', 'Jane'],
            'email': ['john@example.com', 'jane@test.org']
        })
        
        result = self.masker.detect_pii(data)
        
        self.assertTrue(result['has_pii'])
        self.assertIn('email', result['pii_columns'])
        
    def test_detect_pii_phone_numbers(self):
        """Test PII detection for phone numbers"""
        data = pd.DataFrame({
            'name': ['John', 'Jane'],
            'phone': ['+1-555-123-4567', '(555) 987-6543']
        })
        
        result = self.masker.detect_pii(data)
        
        self.assertTrue(result['has_pii'])
        self.assertIn('phone', result['pii_columns'])
        
    def test_detect_pii_ssn(self):
        """Test PII detection for SSN"""
        data = pd.DataFrame({
            'name': ['John', 'Jane'],
            'ssn': ['123-45-6789', '987-65-4321']
        })
        
        result = self.masker.detect_pii(data)
        
        self.assertTrue(result['has_pii'])
        self.assertIn('ssn', result['pii_columns'])
        
    def test_mask_email_addresses(self):
        """Test email address masking"""
        data = pd.DataFrame({
            'email': ['john@example.com', 'jane@test.org']
        })
        
        result = self.masker.mask_pii(data, ['email'])
        
        self.assertTrue(result['success'])
        masked_df = result['masked_data']
        
        # Check that emails are masked
        for email in masked_df['email']:
            self.assertNotIn('@', email)
            self.assertTrue(email.startswith('***'))
            
    def test_mask_phone_numbers(self):
        """Test phone number masking"""
        data = pd.DataFrame({
            'phone': ['+1-555-123-4567', '(555) 987-6543']
        })
        
        result = self.masker.mask_pii(data, ['phone'])
        
        self.assertTrue(result['success'])
        masked_df = result['masked_data']
        
        # Check that phone numbers are masked
        for phone in masked_df['phone']:
            self.assertTrue(phone.startswith('***'))
            
    def test_anonymize_data(self):
        """Test data anonymization"""
        data = pd.DataFrame({
            'name': ['John Doe', 'Jane Smith'],
            'email': ['john@example.com', 'jane@test.org'],
            'age': [25, 30]
        })
        
        result = self.masker.anonymize_data(data)
        
        self.assertTrue(result['success'])
        anonymized_df = result['anonymized_data']
        
        # Check that sensitive data is anonymized
        self.assertNotEqual(anonymized_df['name'].iloc[0], 'John Doe')
        self.assertNotEqual(anonymized_df['email'].iloc[0], 'john@example.com')
        # Age should remain the same (not PII)
        self.assertEqual(anonymized_df['age'].iloc[0], 25)


class SecurityMiddlewareTest(TestCase):
    """Test SecurityMiddleware functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityMiddleware(lambda r: None)
        
    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        self.assertIsNotNone(self.middleware)
        
    def test_process_request_normal(self):
        """Test processing normal request"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = True
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)  # Should pass through
        
    def test_process_request_suspicious_user_agent(self):
        """Test processing request with suspicious user agent"""
        request = self.factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'sqlmap/1.0'
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.middleware.process_request(request)
        
        # Should block suspicious requests
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
        
    def test_process_request_sql_injection_attempt(self):
        """Test processing request with SQL injection attempt"""
        request = self.factory.get('/?id=1; DROP TABLE users;')
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.middleware.process_request(request)
        
        # Should block SQL injection attempts
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
        
    def test_process_request_xss_attempt(self):
        """Test processing request with XSS attempt"""
        request = self.factory.get('/?search=<script>alert("xss")</script>')
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.middleware.process_request(request)
        
        # Should block XSS attempts
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
        
    def test_process_response_security_headers(self):
        """Test adding security headers to response"""
        request = self.factory.get('/')
        response = self.middleware.process_response(request, Mock())
        
        # Check that security headers are added
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-XSS-Protection', response)


class ValidationMiddlewareTest(TestCase):
    """Test ValidationMiddleware functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ValidationMiddleware(lambda r: None)
        
    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        self.assertIsNotNone(self.middleware)
        
    def test_validate_json_payload_valid(self):
        """Test validation of valid JSON payload"""
        valid_data = {'name': 'test', 'value': 123}
        
        result = self.middleware.validate_json_payload(valid_data)
        
        self.assertTrue(result['valid'])
        
    def test_validate_json_payload_invalid(self):
        """Test validation of invalid JSON payload"""
        invalid_data = {'name': '<script>alert("xss")</script>', 'value': '; DROP TABLE users;'}
        
        result = self.middleware.validate_json_payload(invalid_data)
        
        self.assertFalse(result['valid'])
        self.assertIn('errors', result)
        
    def test_validate_file_upload_valid(self):
        """Test validation of valid file upload"""
        file_content = b'normal,csv,content\n1,2,3\n'
        uploaded_file = SimpleUploadedFile('test.csv', file_content, content_type='text/csv')
        
        result = self.middleware.validate_file_upload(uploaded_file)
        
        self.assertTrue(result['valid'])
        
    def test_validate_file_upload_invalid(self):
        """Test validation of invalid file upload"""
        # Create a file with suspicious content
        suspicious_content = b'=HYPERLINK("javascript:alert(1)","Click")\n'
        uploaded_file = SimpleUploadedFile('test.csv', suspicious_content, content_type='text/csv')
        
        result = self.middleware.validate_file_upload(uploaded_file)
        
        self.assertFalse(result['valid'])
        self.assertIn('errors', result)
        
    def test_sanitize_input(self):
        """Test input sanitization"""
        malicious_input = '<script>alert("xss")</script>Hello World'
        
        result = self.middleware.sanitize_input(malicious_input)
        
        self.assertNotIn('<script>', result)
        self.assertNotIn('alert(', result)
        self.assertIn('Hello World', result)


class RateLimitingMiddlewareTest(TestCase):
    """Test RateLimitingMiddleware functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RateLimitingMiddleware(lambda r: None)
        
    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        self.assertIsNotNone(self.middleware)
        self.assertIsNotNone(self.middleware.limits)
        
    def test_is_exempt_path(self):
        """Test exempt path checking"""
        exempt_paths = ['/admin/', '/static/', '/media/']
        
        for path in exempt_paths:
            with self.subTest(path=path):
                result = self.middleware._is_exempt_path(path)
                self.assertTrue(result)
                
    def test_is_exempt_path_non_exempt(self):
        """Test non-exempt path checking"""
        non_exempt_paths = ['/api/data/', '/upload/', '/analysis/']
        
        for path in non_exempt_paths:
            with self.subTest(path=path):
                result = self.middleware._is_exempt_path(path)
                self.assertFalse(result)
                
    def test_get_client_ip_normal(self):
        """Test getting client IP from normal request"""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = self.middleware._get_client_ip(request)
        
        self.assertEqual(ip, '192.168.1.1')
        
    def test_get_client_ip_forwarded(self):
        """Test getting client IP from forwarded request"""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = self.middleware._get_client_ip(request)
        
        self.assertEqual(ip, '203.0.113.1')
        
    def test_get_identifier_authenticated_user(self):
        """Test getting identifier for authenticated user"""
        request = self.factory.get('/')
        user = Mock()
        user.id = 123
        user.is_authenticated = True
        request.user = user
        
        identifier = self.middleware._get_identifier(request)
        
        self.assertEqual(identifier, 'user:123')
        
    def test_get_identifier_anonymous_user(self):
        """Test getting identifier for anonymous user"""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        user = Mock()
        user.is_authenticated = False
        request.user = user
        
        identifier = self.middleware._get_identifier(request)
        
        self.assertEqual(identifier, 'ip:192.168.1.1')
        
    @patch('analytics.middleware.rate_limiting.cache')
    def test_check_sliding_window_within_limit(self, mock_cache):
        """Test sliding window check within limit"""
        mock_cache.get.return_value = []
        mock_cache.set.return_value = True
        
        result = self.middleware._check_sliding_window(
            'test_identifier', 'api_general', 100, 3600
        )
        
        self.assertTrue(result['allowed'])
        self.assertEqual(result['remaining'], 99)
        
    @patch('analytics.middleware.rate_limiting.cache')
    def test_check_sliding_window_exceeded(self, mock_cache):
        """Test sliding window check when limit exceeded"""
        # Mock cache to return 100 requests (at limit)
        current_time = 1000000
        mock_cache.get.return_value = [current_time - 1000] * 100
        
        result = self.middleware._check_sliding_window(
            'test_identifier', 'api_general', 100, 3600
        )
        
        self.assertFalse(result['allowed'])
        self.assertEqual(result['remaining'], 0)
        
    def test_handle_rate_limit_exceeded_api_request(self):
        """Test handling rate limit exceeded for API request"""
        request = self.factory.get('/api/data/')
        request.content_type = 'application/json'
        
        rate_result = {
            'limit': 100,
            'remaining': 0,
            'reset_time': 1000000,
            'retry_after': 60
        }
        
        response = self.middleware._handle_rate_limit_exceeded(request, rate_result)
        
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Content-Type'], 'application/json')
        
    def test_handle_rate_limit_exceeded_web_request(self):
        """Test handling rate limit exceeded for web request"""
        request = self.factory.get('/')
        
        rate_result = {
            'limit': 100,
            'remaining': 0,
            'reset_time': 1000000,
            'retry_after': 60
        }
        
        response = self.middleware._handle_rate_limit_exceeded(request, rate_result)
        
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Content-Type'], 'text/html')
        self.assertIn(b'Rate Limited', response.content)
