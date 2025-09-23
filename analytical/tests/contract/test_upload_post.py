"""
Contract Test: POST /api/upload/ (T013)
Tests the file upload API endpoint according to the API schema
"""

import pytest
import json
import tempfile
import os
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestUploadPostContract(TestCase):
    """Contract tests for POST /api/upload/ endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test CSV file
        self.csv_content = """name,age,city
John,25,New York
Jane,30,Los Angeles
Bob,35,Chicago"""
        
        self.csv_file = SimpleUploadedFile(
            "test_data.csv",
            self.csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        # Create test XLS file (simulated)
        self.xls_content = b"fake xls content"
        self.xls_file = SimpleUploadedFile(
            "test_data.xls",
            self.xls_content,
            content_type="application/vnd.ms-excel"
        )
        
        # Create test JSON file
        self.json_content = json.dumps([
            {"name": "John", "age": 25, "city": "New York"},
            {"name": "Jane", "age": 30, "city": "Los Angeles"},
            {"name": "Bob", "age": 35, "city": "Chicago"}
        ])
        
        self.json_file = SimpleUploadedFile(
            "test_data.json",
            self.json_content.encode('utf-8'),
            content_type="application/json"
        )
    
    def test_upload_csv_success(self):
        """Test successful CSV file upload"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 1,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city'],
                'row_count': 3,
                'file_size': 1024
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'Test dataset'
            }, format='multipart')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('dataset_id', response.data)
            self.assertIn('filename', response.data)
            self.assertIn('columns', response.data)
            self.assertIn('row_count', response.data)
            self.assertIn('file_size', response.data)
            self.assertIn('parquet_path', response.data)
            self.assertIn('uploaded_at', response.data)
            
            # Verify data types
            self.assertIsInstance(response.data['dataset_id'], int)
            self.assertIsInstance(response.data['filename'], str)
            self.assertIsInstance(response.data['columns'], list)
            self.assertIsInstance(response.data['row_count'], int)
            self.assertIsInstance(response.data['file_size'], int)
    
    def test_upload_xls_success(self):
        """Test successful XLS file upload"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 2,
                'filename': 'test_data.xls',
                'columns': ['name', 'age', 'city'],
                'row_count': 3,
                'file_size': 2048
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.xls_file,
                'description': 'Test XLS dataset'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('dataset_id', response.data)
            self.assertIn('filename', response.data)
    
    def test_upload_json_success(self):
        """Test successful JSON file upload"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 3,
                'filename': 'test_data.json',
                'columns': ['name', 'age', 'city'],
                'row_count': 3,
                'file_size': 512
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.json_file,
                'description': 'Test JSON dataset'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('dataset_id', response.data)
            self.assertIn('filename', response.data)
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"plain text content",
            content_type="text/plain"
        )
        
        response = self.client.post('/api/upload/', {
            'file': invalid_file,
            'description': 'Invalid file type'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Unsupported file type', response.data['error'])
    
    def test_upload_file_too_large(self):
        """Test upload with file exceeding size limit"""
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        large_file = SimpleUploadedFile(
            "large_file.csv",
            large_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/api/upload/', {
            'file': large_file,
            'description': 'Large file'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        self.assertIn('error', response.data)
        self.assertIn('File too large', response.data['error'])
    
    def test_upload_missing_file(self):
        """Test upload without file"""
        response = self.client.post('/api/upload/', {
            'description': 'No file provided'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('No file provided', response.data['error'])
    
    def test_upload_unauthenticated(self):
        """Test upload without authentication"""
        client = APIClient()  # No authentication
        
        response = client.post('/api/upload/', {
            'file': self.csv_file,
            'description': 'Unauthenticated upload'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_upload_storage_limit_exceeded(self):
        """Test upload when user storage limit is exceeded"""
        with patch('analytics.services.file_processing.FileProcessingService.check_storage_limit') as mock_check:
            mock_check.return_value = False
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'Storage limit exceeded'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            self.assertIn('error', response.data)
            self.assertIn('Storage limit exceeded', response.data['error'])
    
    def test_upload_processing_error(self):
        """Test upload when file processing fails"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': False,
                'error': 'Processing failed'
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'Processing error'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
            self.assertIn('Processing failed', response.data['error'])
    
    def test_upload_response_schema(self):
        """Test that response matches the expected schema"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 1,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city'],
                'row_count': 3,
                'file_size': 1024,
                'parquet_path': '/media/datasets/test_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z'
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'Schema test'
            }, format='multipart')
            
            # Verify all required fields are present
            required_fields = [
                'dataset_id', 'filename', 'columns', 'row_count', 
                'file_size', 'parquet_path', 'uploaded_at'
            ]
            
            for field in required_fields:
                self.assertIn(field, response.data, f"Missing required field: {field}")
            
            # Verify field types
            self.assertIsInstance(response.data['dataset_id'], int)
            self.assertIsInstance(response.data['filename'], str)
            self.assertIsInstance(response.data['columns'], list)
            self.assertIsInstance(response.data['row_count'], int)
            self.assertIsInstance(response.data['file_size'], int)
            self.assertIsInstance(response.data['parquet_path'], str)
            self.assertIsInstance(response.data['uploaded_at'], str)
    
    def test_upload_audit_logging(self):
        """Test that upload is properly logged for audit"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 1,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city'],
                'row_count': 3,
                'file_size': 1024
            }
            
            with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
                response = self.client.post('/api/upload/', {
                    'file': self.csv_file,
                    'description': 'Audit test'
                }, format='multipart')
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                self.assertEqual(call_args[1]['action'], 'file_upload')
                self.assertEqual(call_args[1]['resource'], 'dataset')
                self.assertEqual(call_args[1]['success'], True)
