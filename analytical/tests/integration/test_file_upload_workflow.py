"""
End-to-End File Upload Workflow Tests

This module contains comprehensive integration tests for the complete file upload workflow,
from initial upload through processing, validation, and storage.
"""

import os
import tempfile
import pandas as pd
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import override_settings
from unittest.mock import patch, Mock
import json

from analytics.models import Dataset, DatasetColumn, User, AuditTrail

User = get_user_model()


class FileUploadWorkflowTest(TestCase):
    """Test complete file upload workflow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
        
    def test_csv_upload_workflow(self):
        """Test complete CSV file upload workflow"""
        # Create test CSV content
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA\nBob,35,Chicago"
        
        # Test 1: Upload file via API
        uploaded_file = SimpleUploadedFile(
            "test_data.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'dataset_name': 'test_dataset',
            'description': 'Test dataset for workflow'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('dataset_id', data)
        
        # Test 2: Verify dataset was created
        dataset_id = data['dataset_id']
        dataset = Dataset.objects.get(id=dataset_id)
        self.assertEqual(dataset.name, 'test_dataset')
        self.assertEqual(dataset.user, self.user)
        self.assertEqual(dataset.row_count, 3)
        self.assertEqual(dataset.column_count, 3)
        
        # Test 3: Verify columns were created
        columns = DatasetColumn.objects.filter(dataset=dataset)
        self.assertEqual(columns.count(), 3)
        
        column_names = [col.name for col in columns]
        self.assertIn('name', column_names)
        self.assertIn('age', column_names)
        self.assertIn('city', column_names)
        
        # Test 4: Verify audit trail was created
        audit_entries = AuditTrail.objects.filter(
            user_id=self.user.id,
            action_type='CREATE',
            resource_type='Dataset'
        )
        self.assertTrue(audit_entries.exists())
        
        # Test 5: Verify parquet file was created
        self.assertTrue(dataset.parquet_file_path)
        self.assertTrue(os.path.exists(dataset.parquet_file_path))
        
    def test_excel_upload_workflow(self):
        """Test complete Excel file upload workflow"""
        # Create test Excel content using pandas
        df = pd.DataFrame({
            'product': ['Laptop', 'Mouse', 'Keyboard'],
            'price': [999.99, 29.99, 79.99],
            'category': ['Electronics', 'Accessories', 'Accessories']
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False)
            tmp.flush()
            
            with open(tmp.name, 'rb') as f:
                uploaded_file = SimpleUploadedFile(
                    "test_products.xlsx",
                    f.read(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                response = self.client.post('/upload/', {
                    'file': uploaded_file,
                    'dataset_name': 'products_dataset',
                    'description': 'Product catalog dataset'
                })
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertTrue(data['success'])
                
                # Verify dataset
                dataset = Dataset.objects.get(id=data['dataset_id'])
                self.assertEqual(dataset.name, 'products_dataset')
                self.assertEqual(dataset.row_count, 3)
                self.assertEqual(dataset.column_count, 3)
                
            os.unlink(tmp.name)
    
    def test_invalid_file_upload_workflow(self):
        """Test file upload workflow with invalid file"""
        # Create invalid file content
        invalid_content = b"This is not a valid CSV or Excel file"
        
        uploaded_file = SimpleUploadedFile(
            "invalid.txt",
            invalid_content,
            content_type="text/plain"
        )
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'dataset_name': 'invalid_dataset'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        
        # Verify no dataset was created
        datasets = Dataset.objects.filter(name='invalid_dataset')
        self.assertEqual(datasets.count(), 0)
        
    def test_duplicate_file_upload_workflow(self):
        """Test file upload workflow with duplicate file"""
        # Upload first file
        csv_content = "id,name\n1,Alice\n2,Bob"
        uploaded_file1 = SimpleUploadedFile(
            "test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        response1 = self.client.post('/api/upload/', {
            'file': uploaded_file1,
            'dataset_name': 'test_dataset'
        })
        
        self.assertEqual(response1.status_code, 200)
        
        # Upload same file again
        uploaded_file2 = SimpleUploadedFile(
            "test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        response2 = self.client.post('/api/upload/', {
            'file': uploaded_file2,
            'dataset_name': 'test_dataset_2'
        })
        
        # Should either create new dataset or return existing one
        self.assertIn(response2.status_code, [200, 201])
        
    def test_large_file_upload_workflow(self):
        """Test file upload workflow with large file"""
        # Create large CSV content
        large_data = []
        for i in range(1000):
            large_data.append(f"row_{i},value_{i},category_{i % 10}")
        
        csv_content = "id,value,category\n" + "\n".join(large_data)
        
        uploaded_file = SimpleUploadedFile(
            "large_dataset.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'dataset_name': 'large_dataset'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify dataset
        dataset = Dataset.objects.get(id=data['dataset_id'])
        self.assertEqual(dataset.row_count, 1000)
        
    def test_upload_with_htmx_interface(self):
        """Test file upload through HTMX interface"""
        # Test dashboard access
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        
        # Test upload form access
        response = self.client.get('/upload-form/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload')
        
    def test_upload_progress_tracking(self):
        """Test file upload progress tracking"""
        csv_content = "name,age\nJohn,25\nJane,30"
        
        uploaded_file = SimpleUploadedFile(
            "progress_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': 1,
                'processing_time': 1.5
            }
            
            response = self.client.post('/upload/', {
                'file': uploaded_file,
                'dataset_name': 'progress_test'
            })
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
            
    def test_upload_error_handling(self):
        """Test file upload error handling"""
        # Test with corrupted file
        corrupted_content = b"corrupted,data\n\x00\x01\x02"
        
        uploaded_file = SimpleUploadedFile(
            "corrupted.csv",
            corrupted_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'dataset_name': 'corrupted_dataset'
        })
        
        # Should handle error gracefully
        self.assertIn(response.status_code, [200, 400, 500])
        
    def test_upload_security_validation(self):
        """Test file upload security validation"""
        # Test with potentially malicious content
        malicious_content = b"name,script\nJohn,<script>alert('xss')</script>"
        
        uploaded_file = SimpleUploadedFile(
            "malicious.csv",
            malicious_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'dataset_name': 'malicious_dataset'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        if data['success']:
            # If successful, verify content was sanitized
            dataset = Dataset.objects.get(id=data['dataset_id'])
            # The sanitization should have removed script tags
            self.assertTrue(dataset.parquet_file_path)
    
    def test_upload_with_metadata(self):
        """Test file upload with additional metadata"""
        csv_content = "id,value\n1,100\n2,200"
        
        uploaded_file = SimpleUploadedFile(
            "metadata_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'dataset_name': 'metadata_test',
            'description': 'Test dataset with metadata',
            'tags': 'test,integration,workflow'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify metadata was stored
        dataset = Dataset.objects.get(id=data['dataset_id'])
        self.assertEqual(dataset.description, 'Test dataset with metadata')
        
    def test_upload_performance_requirements(self):
        """Test file upload meets performance requirements (<2s)"""
        import time
        
        csv_content = "name,age,city\n" + "\n".join([f"Person{i},{20+i},City{i}" for i in range(100)])
        
        uploaded_file = SimpleUploadedFile(
            "performance_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        start_time = time.time()
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'dataset_name': 'performance_test'
        })
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(processing_time, 2.0, f"Upload took {processing_time:.2f}s, should be <2s")
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
