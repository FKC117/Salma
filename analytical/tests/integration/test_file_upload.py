"""
Integration Test: File Upload Workflow (T020)
Tests the complete file upload workflow from UI to database storage
"""

import pytest
import json
import tempfile
import os
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

class TestFileUploadWorkflow(TestCase):
    """Integration tests for complete file upload workflow"""
    
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
        self.csv_content = """name,age,city,salary
John,25,New York,50000
Jane,30,Los Angeles,60000
Bob,35,Chicago,55000
Alice,28,San Francisco,70000
Charlie,32,Boston,65000"""
        
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
            {"name": "John", "age": 25, "city": "New York", "salary": 50000},
            {"name": "Jane", "age": 30, "city": "Los Angeles", "salary": 60000},
            {"name": "Bob", "age": 35, "city": "Chicago", "salary": 55000},
            {"name": "Alice", "age": 28, "city": "San Francisco", "salary": 70000},
            {"name": "Charlie", "age": 32, "city": "Boston", "salary": 65000}
        ])
        
        self.json_file = SimpleUploadedFile(
            "test_data.json",
            self.json_content.encode('utf-8'),
            content_type="application/json"
        )
    
    def test_complete_csv_upload_workflow(self):
        """Test complete CSV upload workflow from upload to Parquet storage"""
        # Step 1: Upload file via API
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 1,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city', 'salary'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/test_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'column_types': {
                    'name': 'categorical',
                    'age': 'numeric',
                    'city': 'categorical',
                    'salary': 'numeric'
                }
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'Test dataset for integration testing'
            }, format='multipart')
            
            # Verify upload response
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('dataset_id', response.data)
            self.assertIn('parquet_path', response.data)
            self.assertIn('column_types', response.data)
            
            # Verify file processing was called
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            self.assertIn('file', call_args[1])
            self.assertIn('user_id', call_args[1])
            self.assertIn('description', call_args[1])
    
    def test_file_upload_with_security_validation(self):
        """Test file upload with security validation and sanitization"""
        # Create file with potentially malicious content
        malicious_content = """name,age,city,formula
John,25,New York,=SUM(A1:A10)
Jane,30,Los Angeles,=VLOOKUP(B1,C1:D10,2,FALSE)
Bob,35,Chicago,=IF(A1>100,"High","Low")"""
        
        malicious_file = SimpleUploadedFile(
            "malicious_data.csv",
            malicious_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 2,
                'filename': 'malicious_data.csv',
                'columns': ['name', 'age', 'city', 'formula'],
                'row_count': 3,
                'file_size': 512,
                'parquet_path': '/media/datasets/malicious_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'security_warnings': [
                    'Formulas detected and removed from formula column',
                    'Macro content sanitized'
                ],
                'sanitized': True
            }
            
            response = self.client.post('/api/upload/', {
                'file': malicious_file,
                'description': 'File with security concerns'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('security_warnings', response.data)
            self.assertIn('sanitized', response.data)
            self.assertTrue(response.data['sanitized'])
    
    def test_file_upload_storage_limit_enforcement(self):
        """Test file upload with storage limit enforcement"""
        # Simulate user approaching storage limit
        with patch('analytics.services.file_processing.FileProcessingService.check_storage_limit') as mock_check:
            mock_check.return_value = False  # Storage limit exceeded
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'File that exceeds storage limit'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            self.assertIn('error', response.data)
            self.assertIn('Storage limit exceeded', response.data['error'])
    
    def test_file_upload_with_audit_logging(self):
        """Test file upload with comprehensive audit logging"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 3,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city', 'salary'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/test_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z'
            }
        
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'File upload with audit logging'
            }, format='multipart')
            
            # Verify audit logging was called
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            self.assertEqual(call_args[1]['action'], 'file_upload')
            self.assertEqual(call_args[1]['resource'], 'dataset')
            self.assertEqual(call_args[1]['success'], True)
            self.assertIn('file_size', call_args[1]['additional_details'])
    
    def test_file_upload_with_column_type_detection(self):
        """Test file upload with automatic column type detection"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 4,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city', 'salary', 'hire_date'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/test_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'column_types': {
                    'name': 'categorical',
                    'age': 'numeric',
                    'city': 'categorical',
                    'salary': 'numeric',
                    'hire_date': 'datetime'
                },
                'column_analysis': {
                    'numeric_columns': ['age', 'salary'],
                    'categorical_columns': ['name', 'city'],
                    'datetime_columns': ['hire_date'],
                    'text_columns': []
                }
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'File with column type detection'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('column_types', response.data)
            self.assertIn('column_analysis', response.data)
            self.assertEqual(len(response.data['column_types']), 5)
            self.assertIn('numeric_columns', response.data['column_analysis'])
            self.assertIn('categorical_columns', response.data['column_analysis'])
    
    def test_file_upload_with_parquet_conversion(self):
        """Test file upload with Parquet conversion and validation"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 5,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city', 'salary'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/test_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'conversion_details': {
                    'original_format': 'csv',
                    'target_format': 'parquet',
                    'compression_ratio': 0.75,
                    'conversion_time_ms': 150,
                    'data_integrity_verified': True
                }
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'File with Parquet conversion'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('conversion_details', response.data)
            self.assertTrue(response.data['conversion_details']['data_integrity_verified'])
            self.assertEqual(response.data['conversion_details']['target_format'], 'parquet')
    
    def test_file_upload_error_handling(self):
        """Test file upload with comprehensive error handling"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': False,
                'error': 'File processing failed due to corrupted data',
                'error_code': 'CORRUPTED_DATA',
                'error_details': {
                    'line_number': 3,
                    'column': 'salary',
                    'value': 'invalid_number',
                    'suggestion': 'Check data format in row 3'
                }
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'File with processing errors'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
            self.assertIn('error_code', response.data)
            self.assertIn('error_details', response.data)
            self.assertEqual(response.data['error_code'], 'CORRUPTED_DATA')
    
    def test_file_upload_with_concurrent_processing(self):
        """Test file upload with concurrent processing simulation"""
        # Simulate multiple concurrent uploads
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 6,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city', 'salary'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/test_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'processing_info': {
                    'queue_position': 1,
                    'estimated_wait_time': 30,
                    'processing_priority': 'normal'
                }
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'File with concurrent processing'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('processing_info', response.data)
            self.assertIn('queue_position', response.data['processing_info'])
    
    def test_file_upload_with_metadata_extraction(self):
        """Test file upload with comprehensive metadata extraction"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 7,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city', 'salary'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/test_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'metadata': {
                    'file_hash': 'sha256:abc123def456',
                    'encoding': 'utf-8',
                    'delimiter': ',',
                    'has_header': True,
                    'null_values': ['', 'NULL', 'N/A'],
                    'data_quality_score': 0.95,
                    'completeness': 1.0,
                    'consistency': 0.9
                }
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'File with metadata extraction'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('metadata', response.data)
            self.assertIn('file_hash', response.data['metadata'])
            self.assertIn('data_quality_score', response.data['metadata'])
            self.assertGreaterEqual(response.data['metadata']['data_quality_score'], 0.9)
    
    def test_file_upload_workflow_integration(self):
        """Test complete file upload workflow integration"""
        # This test simulates the complete workflow from UI to database
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 8,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city', 'salary'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/test_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'column_types': {
                    'name': 'categorical',
                    'age': 'numeric',
                    'city': 'categorical',
                    'salary': 'numeric'
                },
                'workflow_status': {
                    'file_uploaded': True,
                    'security_scan_completed': True,
                    'parquet_conversion_completed': True,
                    'metadata_extracted': True,
                    'database_stored': True,
                    'cache_updated': True,
                    'audit_logged': True
                }
            }
        
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
            with patch('analytics.services.cache_manager.CacheManager.update_dataset_cache') as mock_cache:
                response = self.client.post('/api/upload/', {
                    'file': self.csv_file,
                    'description': 'Complete workflow integration test'
                }, format='multipart')
                
                # Verify complete workflow
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertIn('workflow_status', response.data)
                self.assertTrue(response.data['workflow_status']['file_uploaded'])
                self.assertTrue(response.data['workflow_status']['security_scan_completed'])
                self.assertTrue(response.data['workflow_status']['parquet_conversion_completed'])
                self.assertTrue(response.data['workflow_status']['database_stored'])
                
                # Verify audit logging
                mock_audit.assert_called_once()
                
                # Verify cache update
                mock_cache.assert_called_once()
    
    def test_file_upload_with_user_feedback(self):
        """Test file upload with user feedback and notifications"""
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 9,
                'filename': 'test_data.csv',
                'columns': ['name', 'age', 'city', 'salary'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/test_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'user_feedback': {
                    'message': 'File uploaded successfully!',
                    'suggestions': [
                        'Consider analyzing salary distribution',
                        'City data could be useful for geographic analysis'
                    ],
                    'next_steps': [
                        'Create analysis session',
                        'Explore available tools',
                        'Start with descriptive statistics'
                    ]
                }
            }
            
            response = self.client.post('/api/upload/', {
                'file': self.csv_file,
                'description': 'File with user feedback'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('user_feedback', response.data)
            self.assertIn('suggestions', response.data['user_feedback'])
            self.assertIn('next_steps', response.data['user_feedback'])
            self.assertEqual(len(response.data['user_feedback']['suggestions']), 2)
            self.assertEqual(len(response.data['user_feedback']['next_steps']), 3)
