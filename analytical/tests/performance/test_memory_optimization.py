"""
Memory Usage Optimization Tests

This module contains performance tests for memory usage optimization,
ensuring efficient memory management across the application.
"""

import os
import psutil
import time
import pandas as pd
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from analytics.models import Dataset, AnalysisSession, User

User = get_user_model()


class MemoryOptimizationTest(TestCase):
    """Test memory usage optimization"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
        
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss
    
    def test_file_upload_memory_usage(self):
        """Test file upload memory usage optimization"""
        # Create large CSV file
        data = []
        for i in range(10000):
            data.append(f"Row{i},{i},{i*2},{i*3},{i*4}")
        
        csv_content = "col1,col2,col3,col4,col5\n" + "\n".join(data)
        
        uploaded_file = SimpleUploadedFile(
            "large_memory_test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        memory_before = self.process.memory_info().rss
        
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'memory_test'
        })
        
        memory_after = self.process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        self.assertEqual(response.status_code, 200)
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024, 
                       f"File upload memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_analysis_execution_memory_usage(self):
        """Test analysis execution memory usage optimization"""
        # Create dataset
        dataset = Dataset.objects.create(
            name='memory_test_dataset',
            user=self.user,
            file_size_bytes=1000000,
            parquet_size_bytes=500000,
            row_count=50000,
            column_count=10
        )
        
        # Create session
        session = AnalysisSession.objects.create(
            name='memory_test_session',
            user=self.user,
            primary_dataset=dataset,
            is_active=True
        )
        
        memory_before = self.process.memory_info().rss
        
        # Execute multiple analyses
        for i in range(5):
            response = self.client.post('/api/analysis/execute/', {
                'tool_name': 'descriptive_statistics',
                'dataset_id': dataset.id,
                'session_id': session.id,
                'parameters': {'column': f'column_{i}'}
            })
            self.assertEqual(response.status_code, 200)
        
        memory_after = self.process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        # Memory increase should be reasonable (less than 50MB)
        self.assertLess(memory_increase, 50 * 1024 * 1024, 
                       f"Analysis execution memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_concurrent_operations_memory_usage(self):
        """Test concurrent operations memory usage"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def memory_intensive_operation(operation_id):
            memory_before = self.process.memory_info().rss
            
            # Simulate memory-intensive operation
            csv_content = "name,age,city\n" + "\n".join([f"Person{i},{20+i},City{i}" for i in range(1000)])
            
            uploaded_file = SimpleUploadedFile(
                f"concurrent_test_{operation_id}.csv",
                csv_content.encode(),
                content_type="text/csv"
            )
            
            response = self.client.post('/api/upload/', {
                'file': uploaded_file,
                'dataset_name': f'concurrent_test_{operation_id}'
            })
            
            memory_after = self.process.memory_info().rss
            memory_increase = memory_after - memory_before
            
            results.put({
                'operation_id': operation_id,
                'status_code': response.status_code,
                'memory_increase': memory_increase
            })
        
        # Run multiple operations concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=memory_intensive_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        total_memory_increase = 0
        while not results.empty():
            result = results.get()
            self.assertEqual(result['status_code'], 200)
            total_memory_increase += result['memory_increase']
        
        # Total memory increase should be reasonable
        self.assertLess(total_memory_increase, 200 * 1024 * 1024, 
                       f"Concurrent operations memory increase {total_memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_memory_cleanup_after_operations(self):
        """Test memory cleanup after operations"""
        initial_memory = self.process.memory_info().rss
        
        # Perform multiple operations
        for i in range(10):
            csv_content = f"name,age\nPerson{i},{20+i}"
            uploaded_file = SimpleUploadedFile(
                f"cleanup_test_{i}.csv",
                csv_content.encode(),
                content_type="text/csv"
            )
            
            response = self.client.post('/api/upload/', {
                'file': uploaded_file,
                'dataset_name': f'cleanup_test_{i}'
            })
            self.assertEqual(response.status_code, 200)
        
        # Force garbage collection
        import gc
        gc.collect()
        
        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should be cleaned up reasonably well
        self.assertLess(memory_increase, 50 * 1024 * 1024, 
                       f"Memory cleanup failed, increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_large_dataset_memory_usage(self):
        """Test large dataset memory usage optimization"""
        # Create very large dataset
        large_dataset = Dataset.objects.create(
            name='large_memory_dataset',
            user=self.user,
            file_size_bytes=100000000,  # 100MB
            parquet_size_bytes=50000000,  # 50MB
            row_count=1000000,  # 1M rows
            column_count=20
        )
        
        session = AnalysisSession.objects.create(
            name='large_memory_session',
            user=self.user,
            primary_dataset=large_dataset,
            is_active=True
        )
        
        memory_before = self.process.memory_info().rss
        
        # Perform analysis on large dataset
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': large_dataset.id,
            'session_id': session.id,
            'parameters': {'column': 'column_0'}
        })
        
        memory_after = self.process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        self.assertEqual(response.status_code, 200)
        # Memory increase should be reasonable even for large datasets
        self.assertLess(memory_increase, 200 * 1024 * 1024, 
                       f"Large dataset memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_caching_memory_usage(self):
        """Test caching memory usage optimization"""
        dataset = Dataset.objects.create(
            name='caching_test_dataset',
            user=self.user,
            file_size_bytes=1000000,
            parquet_size_bytes=500000,
            row_count=10000,
            column_count=5
        )
        
        session = AnalysisSession.objects.create(
            name='caching_test_session',
            user=self.user,
            primary_dataset=dataset,
            is_active=True
        )
        
        memory_before = self.process.memory_info().rss
        
        # Execute same analysis multiple times (should use cache)
        for i in range(5):
            response = self.client.post('/api/analysis/execute/', {
                'tool_name': 'descriptive_statistics',
                'dataset_id': dataset.id,
                'session_id': session.id,
                'parameters': {'column': 'column_0'}
            })
            self.assertEqual(response.status_code, 200)
        
        memory_after = self.process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        # Caching should not significantly increase memory usage
        self.assertLess(memory_increase, 20 * 1024 * 1024, 
                       f"Caching memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_ui_rendering_memory_usage(self):
        """Test UI rendering memory usage optimization"""
        memory_before = self.process.memory_info().rss
        
        # Perform multiple UI operations
        for i in range(20):
            response = self.client.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            
            response = self.client.get('/tools/list/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
        
        memory_after = self.process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        # UI rendering should not significantly increase memory usage
        self.assertLess(memory_increase, 30 * 1024 * 1024, 
                       f"UI rendering memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_database_query_memory_usage(self):
        """Test database query memory usage optimization"""
        # Create multiple datasets
        for i in range(50):
            Dataset.objects.create(
                name=f'db_memory_test_{i}',
                user=self.user,
                file_size_bytes=10000,
                parquet_size_bytes=5000,
                row_count=1000,
                column_count=5
            )
        
        memory_before = self.process.memory_info().rss
        
        # Perform database queries
        datasets = Dataset.objects.filter(user=self.user)
        self.assertEqual(datasets.count(), 50)
        
        # Perform complex queries
        for dataset in datasets:
            sessions = AnalysisSession.objects.filter(primary_dataset=dataset)
            # This should not load all data into memory
        
        memory_after = self.process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        # Database queries should not significantly increase memory usage
        self.assertLess(memory_increase, 10 * 1024 * 1024, 
                       f"Database query memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_agent_run_memory_usage(self):
        """Test agent run memory usage optimization"""
        dataset = Dataset.objects.create(
            name='agent_memory_test',
            user=self.user,
            file_size_bytes=1000000,
            parquet_size_bytes=500000,
            row_count=10000,
            column_count=10
        )
        
        session = AnalysisSession.objects.create(
            name='agent_memory_session',
            user=self.user,
            primary_dataset=dataset,
            is_active=True
        )
        
        memory_before = self.process.memory_info().rss
        
        # Run agent
        response = self.client.post('/api/agent/run/', {
            'dataset_id': dataset.id,
            'session_id': session.id,
            'analysis_goal': 'Test memory usage'
        })
        
        memory_after = self.process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        self.assertEqual(response.status_code, 200)
        # Agent run should not significantly increase memory usage
        self.assertLess(memory_increase, 50 * 1024 * 1024, 
                       f"Agent run memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks"""
        initial_memory = self.process.memory_info().rss
        
        # Perform operations multiple times
        for cycle in range(5):
            # Upload file
            csv_content = f"name,age\nPerson{cycle},{20+cycle}"
            uploaded_file = SimpleUploadedFile(
                f"leak_test_{cycle}.csv",
                csv_content.encode(),
                content_type="text/csv"
            )
            
            response = self.client.post('/api/upload/', {
                'file': uploaded_file,
                'dataset_name': f'leak_test_{cycle}'
            })
            self.assertEqual(response.status_code, 200)
            
            # Perform analysis
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    dataset_id = data['dataset_id']
                    session = AnalysisSession.objects.create(
                        name=f'leak_session_{cycle}',
                        user=self.user,
                        primary_dataset_id=dataset_id,
                        is_active=True
                    )
                    
                    analysis_response = self.client.post('/api/analysis/execute/', {
                        'tool_name': 'descriptive_statistics',
                        'dataset_id': dataset_id,
                        'session_id': session.id,
                        'parameters': {'column': 'name'}
                    })
                    self.assertEqual(analysis_response.status_code, 200)
            
            # Force garbage collection
            import gc
            gc.collect()
        
        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (no significant leaks)
        self.assertLess(memory_increase, 30 * 1024 * 1024, 
                       f"Potential memory leak detected, increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_memory_usage_under_load(self):
        """Test memory usage under load"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def load_test_operation(operation_id):
            memory_before = self.process.memory_info().rss
            
            # Simulate load
            csv_content = "name,age,city\n" + "\n".join([f"Person{i},{20+i},City{i}" for i in range(1000)])
            
            uploaded_file = SimpleUploadedFile(
                f"load_test_{operation_id}.csv",
                csv_content.encode(),
                content_type="text/csv"
            )
            
            response = self.client.post('/api/upload/', {
                'file': uploaded_file,
                'dataset_name': f'load_test_{operation_id}'
            })
            
            memory_after = self.process.memory_info().rss
            memory_increase = memory_after - memory_before
            
            results.put({
                'operation_id': operation_id,
                'status_code': response.status_code,
                'memory_increase': memory_increase
            })
        
        # Run load test
        threads = []
        for i in range(10):
            thread = threading.Thread(target=load_test_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        total_memory_increase = 0
        while not results.empty():
            result = results.get()
            self.assertEqual(result['status_code'], 200)
            total_memory_increase += result['memory_increase']
        
        # Total memory increase should be reasonable under load
        self.assertLess(total_memory_increase, 300 * 1024 * 1024, 
                       f"Load test memory increase {total_memory_increase / 1024 / 1024:.1f}MB is too high")
