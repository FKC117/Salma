"""
File Upload Performance Tests

This module contains performance tests for file upload operations,
ensuring they meet the <2s target requirement.
"""

import os
import tempfile
import time
import pandas as pd
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from unittest.mock import patch

from analytics.models import Dataset, User

User = get_user_model()


class FileUploadPerformanceTest(TestCase):
    """Test file upload performance requirements"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
    
    def test_small_csv_upload_performance(self):
        """Test small CSV upload performance (<2s)"""
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA"
        
        uploaded_file = SimpleUploadedFile(
            "small_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'small_test'
        })
        
        end_time = time.time()
        upload_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(upload_time, 2.0, f"Small CSV upload took {upload_time:.2f}s, should be <2s")
    
    def test_medium_csv_upload_performance(self):
        """Test medium CSV upload performance (<2s)"""
        # Create medium-sized CSV (1000 rows)
        data = []
        for i in range(1000):
            data.append(f"Person{i},{20 + (i % 50)},{'City' + str(i % 10)}")
        
        csv_content = "name,age,city\n" + "\n".join(data)
        
        uploaded_file = SimpleUploadedFile(
            "medium_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'medium_test'
        })
        
        end_time = time.time()
        upload_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(upload_time, 2.0, f"Medium CSV upload took {upload_time:.2f}s, should be <2s")
    
    def test_large_csv_upload_performance(self):
        """Test large CSV upload performance (<2s)"""
        # Create large CSV (5000 rows)
        data = []
        for i in range(5000):
            data.append(f"Person{i},{20 + (i % 50)},{'City' + str(i % 10)},{1000 + (i % 5000)}")
        
        csv_content = "name,age,city,income\n" + "\n".join(data)
        
        uploaded_file = SimpleUploadedFile(
            "large_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'large_test'
        })
        
        end_time = time.time()
        upload_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(upload_time, 2.0, f"Large CSV upload took {upload_time:.2f}s, should be <2s")
    
    def test_excel_upload_performance(self):
        """Test Excel upload performance (<2s)"""
        # Create Excel file with pandas
        df = pd.DataFrame({
            'product': [f'Product{i}' for i in range(1000)],
            'price': [100 + (i % 1000) for i in range(1000)],
            'category': [f'Category{i % 10}' for i in range(1000)]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False)
            tmp.flush()
            
            with open(tmp.name, 'rb') as f:
                uploaded_file = SimpleUploadedFile(
                    "test_performance.xlsx",
                    f.read(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                start_time = time.time()
                
                response = self.client.post('/api/upload/', {
                    'file': uploaded_file,
                    'dataset_name': 'excel_test'
                })
                
                end_time = time.time()
                upload_time = end_time - start_time
                
                self.assertEqual(response.status_code, 200)
                self.assertLess(upload_time, 2.0, f"Excel upload took {upload_time:.2f}s, should be <2s")
            
            os.unlink(tmp.name)
    
    def test_concurrent_upload_performance(self):
        """Test concurrent upload performance"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def upload_file(file_content, filename):
            uploaded_file = SimpleUploadedFile(
                filename,
                file_content.encode(),
                content_type="text/csv"
            )
            
            start_time = time.time()
            
            response = self.client.post('/api/upload/', {
                'file': uploaded_file,
                'dataset_name': f'concurrent_{filename}'
            })
            
            end_time = time.time()
            upload_time = end_time - start_time
            
            results.put({
                'status_code': response.status_code,
                'upload_time': upload_time,
                'filename': filename
            })
        
        # Create multiple upload threads
        csv_content = "name,age\nJohn,25\nJane,30"
        threads = []
        
        for i in range(3):
            thread = threading.Thread(
                target=upload_file,
                args=(csv_content, f'concurrent_{i}.csv')
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        while not results.empty():
            result = results.get()
            self.assertEqual(result['status_code'], 200)
            self.assertLess(result['upload_time'], 2.0, 
                          f"Concurrent upload {result['filename']} took {result['upload_time']:.2f}s, should be <2s")
    
    def test_upload_with_processing_performance(self):
        """Test upload with processing performance (<2s)"""
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA\nBob,35,Chicago"
        
        uploaded_file = SimpleUploadedFile(
            "processing_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'processing_test',
            'process_immediately': True
        })
        
        end_time = time.time()
        upload_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(upload_time, 2.0, f"Upload with processing took {upload_time:.2f}s, should be <2s")
    
    def test_upload_memory_usage(self):
        """Test upload memory usage efficiency"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large file
        data = []
        for i in range(10000):
            data.append(f"Row{i},{i},{i*2},{i*3}")
        
        csv_content = "col1,col2,col3,col4\n" + "\n".join(data)
        
        uploaded_file = SimpleUploadedFile(
            "memory_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'memory_test'
        })
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        self.assertEqual(response.status_code, 200)
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024, 
                       f"Memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_upload_error_performance(self):
        """Test upload error handling performance"""
        # Test with invalid file
        invalid_content = b"This is not a valid CSV file"
        
        uploaded_file = SimpleUploadedFile(
            "invalid.txt",
            invalid_content,
            content_type="text/plain"
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'invalid_test'
        })
        
        end_time = time.time()
        error_time = end_time - start_time
        
        # Error handling should also be fast
        self.assertLess(error_time, 1.0, f"Error handling took {error_time:.2f}s, should be <1s")
    
    def test_upload_with_validation_performance(self):
        """Test upload with validation performance"""
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA"
        
        uploaded_file = SimpleUploadedFile(
            "validation_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'validation_test',
            'validate_data': True,
            'check_pii': True
        })
        
        end_time = time.time()
        upload_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(upload_time, 2.0, f"Upload with validation took {upload_time:.2f}s, should be <2s")
    
    def test_upload_parquet_conversion_performance(self):
        """Test upload with Parquet conversion performance"""
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA\nBob,35,Chicago"
        
        uploaded_file = SimpleUploadedFile(
            "parquet_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'parquet_test',
            'convert_to_parquet': True
        })
        
        end_time = time.time()
        upload_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(upload_time, 2.0, f"Upload with Parquet conversion took {upload_time:.2f}s, should be <2s")
        
        # Verify Parquet file was created
        data = response.json()
        if data['success']:
            dataset = Dataset.objects.get(id=data['dataset_id'])
            self.assertTrue(dataset.parquet_file_path)
            self.assertTrue(os.path.exists(dataset.parquet_file_path))
