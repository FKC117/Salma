"""
Analysis Execution Performance Tests

This module contains performance tests for analysis execution operations,
ensuring they meet the <500ms target requirement.
"""

import time
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock

from analytics.models import (
    Dataset, DatasetColumn, AnalysisTool, AnalysisSession, 
    AnalysisResult, User
)

User = get_user_model()


class AnalysisExecutionPerformanceTest(TestCase):
    """Test analysis execution performance requirements"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
        
        # Create test dataset
        self.dataset = Dataset.objects.create(
            name='test_dataset',
            user=self.user,
            file_size_bytes=1000,
            parquet_size_bytes=500,
            row_count=1000,
            column_count=5
        )
        
        # Create test columns
        for i in range(5):
            DatasetColumn.objects.create(
                dataset=self.dataset,
                name=f'column_{i}',
                column_type='numeric',
                data_type='float64',
                is_numeric=True,
                is_categorical=False
            )
        
        # Create test analysis tool
        self.tool = AnalysisTool.objects.create(
            name='descriptive_statistics',
            display_name='Descriptive Statistics',
            description='Calculate descriptive statistics',
            tool_type='statistical',
            parameters_schema={'column': {'type': 'string', 'required': True}}
        )
        
        # Create test session
        self.session = AnalysisSession.objects.create(
            name='test_session',
            user=self.user,
            primary_dataset=self.dataset,
            is_active=True
        )
    
    def test_descriptive_statistics_performance(self):
        """Test descriptive statistics performance (<500ms)"""
        start_time = time.time()
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'column_0'}
        })
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5, f"Descriptive statistics took {execution_time:.3f}s, should be <500ms")
    
    def test_correlation_analysis_performance(self):
        """Test correlation analysis performance (<500ms)"""
        # Create correlation tool
        correlation_tool = AnalysisTool.objects.create(
            name='correlation_analysis',
            display_name='Correlation Analysis',
            description='Calculate correlations',
            tool_type='statistical',
            parameters_schema={'columns': {'type': 'array', 'required': True}}
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'correlation_analysis',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'columns': ['column_0', 'column_1']}
        })
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5, f"Correlation analysis took {execution_time:.3f}s, should be <500ms")
    
    def test_visualization_performance(self):
        """Test visualization generation performance (<500ms)"""
        # Create visualization tool
        viz_tool = AnalysisTool.objects.create(
            name='create_histogram',
            display_name='Create Histogram',
            description='Generate histogram',
            tool_type='visualization',
            parameters_schema={'column': {'type': 'string', 'required': True}}
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'create_histogram',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'column_0'}
        })
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5, f"Visualization took {execution_time:.3f}s, should be <500ms")
    
    def test_ml_analysis_performance(self):
        """Test ML analysis performance (<500ms)"""
        # Create ML tool
        ml_tool = AnalysisTool.objects.create(
            name='linear_regression',
            display_name='Linear Regression',
            description='Perform linear regression',
            tool_type='ml',
            parameters_schema={
                'target_column': {'type': 'string', 'required': True},
                'feature_columns': {'type': 'array', 'required': True}
            }
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'linear_regression',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {
                'target_column': 'column_0',
                'feature_columns': ['column_1', 'column_2']
            }
        })
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5, f"ML analysis took {execution_time:.3f}s, should be <500ms")
    
    def test_concurrent_analysis_performance(self):
        """Test concurrent analysis performance"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def run_analysis(column_name):
            start_time = time.time()
            
            response = self.client.post('/api/analysis/execute/', {
                'tool_name': 'descriptive_statistics',
                'dataset_id': self.dataset.id,
                'session_id': self.session.id,
                'parameters': {'column': column_name}
            })
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            results.put({
                'status_code': response.status_code,
                'execution_time': execution_time,
                'column': column_name
            })
        
        # Run multiple analyses concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_analysis, args=(f'column_{i}',))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        while not results.empty():
            result = results.get()
            self.assertEqual(result['status_code'], 200)
            self.assertLess(result['execution_time'], 0.5, 
                          f"Concurrent analysis on {result['column']} took {result['execution_time']:.3f}s, should be <500ms")
    
    def test_analysis_with_caching_performance(self):
        """Test analysis with caching performance"""
        # First execution
        start_time = time.time()
        
        response1 = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'column_0'}
        })
        
        end_time = time.time()
        first_execution_time = end_time - start_time
        
        self.assertEqual(response1.status_code, 200)
        self.assertLess(first_execution_time, 0.5, f"First execution took {first_execution_time:.3f}s, should be <500ms")
        
        # Second execution (should use cache)
        start_time = time.time()
        
        response2 = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'column_0'}
        })
        
        end_time = time.time()
        second_execution_time = end_time - start_time
        
        self.assertEqual(response2.status_code, 200)
        # Cached execution should be faster
        self.assertLess(second_execution_time, first_execution_time, 
                       f"Cached execution should be faster: {second_execution_time:.3f}s vs {first_execution_time:.3f}s")
    
    def test_analysis_memory_usage(self):
        """Test analysis memory usage efficiency"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'column_0'}
        })
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        self.assertEqual(response.status_code, 200)
        # Memory increase should be reasonable (less than 50MB)
        self.assertLess(memory_increase, 50 * 1024 * 1024, 
                       f"Memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_analysis_error_performance(self):
        """Test analysis error handling performance"""
        start_time = time.time()
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'nonexistent_column'}
        })
        
        end_time = time.time()
        error_time = end_time - start_time
        
        # Error handling should also be fast
        self.assertLess(error_time, 0.2, f"Error handling took {error_time:.3f}s, should be <200ms")
    
    def test_analysis_with_large_dataset_performance(self):
        """Test analysis performance with large dataset"""
        # Create large dataset
        large_dataset = Dataset.objects.create(
            name='large_dataset',
            user=self.user,
            file_size_bytes=10000000,
            parquet_size_bytes=5000000,
            row_count=100000,
            column_count=10
        )
        
        # Create columns for large dataset
        for i in range(10):
            DatasetColumn.objects.create(
                dataset=large_dataset,
                name=f'large_column_{i}',
                column_type='numeric',
                data_type='float64',
                is_numeric=True,
                is_categorical=False
            )
        
        start_time = time.time()
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': large_dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'large_column_0'}
        })
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # Large dataset analysis might take longer, but should still be reasonable
        self.assertLess(execution_time, 1.0, f"Large dataset analysis took {execution_time:.3f}s, should be <1s")
    
    def test_analysis_result_retrieval_performance(self):
        """Test analysis result retrieval performance"""
        # Execute analysis first
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'column_0'}
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        result_id = data['result_id']
        
        # Test result retrieval performance
        start_time = time.time()
        
        result = AnalysisResult.objects.get(id=result_id)
        
        end_time = time.time()
        retrieval_time = end_time - start_time
        
        # Result retrieval should be very fast
        self.assertLess(retrieval_time, 0.1, f"Result retrieval took {retrieval_time:.3f}s, should be <100ms")
        self.assertIsNotNone(result.result_data)
    
    def test_analysis_batch_execution_performance(self):
        """Test batch analysis execution performance"""
        # Create multiple tools
        tools = []
        for i in range(5):
            tool = AnalysisTool.objects.create(
                name=f'analysis_tool_{i}',
                display_name=f'Analysis Tool {i}',
                description=f'Test analysis tool {i}',
                tool_type='statistical',
                parameters_schema={'column': {'type': 'string', 'required': True}}
            )
            tools.append(tool)
        
        start_time = time.time()
        
        # Execute multiple analyses
        for i, tool in enumerate(tools):
            response = self.client.post('/api/analysis/execute/', {
                'tool_name': tool.name,
                'dataset_id': self.dataset.id,
                'session_id': self.session.id,
                'parameters': {'column': f'column_{i}'}
            })
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Total time for 5 analyses should be reasonable
        self.assertLess(total_time, 2.0, f"Batch analysis took {total_time:.3f}s for 5 analyses, should be <2s")
    
    def test_analysis_with_complex_parameters_performance(self):
        """Test analysis with complex parameters performance"""
        # Create tool with complex parameters
        complex_tool = AnalysisTool.objects.create(
            name='complex_analysis',
            display_name='Complex Analysis',
            description='Complex analysis with many parameters',
            tool_type='statistical',
            parameters_schema={
                'columns': {'type': 'array', 'required': True},
                'method': {'type': 'string', 'required': True},
                'options': {'type': 'object', 'required': False}
            }
        )
        
        start_time = time.time()
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'complex_analysis',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {
                'columns': ['column_0', 'column_1', 'column_2'],
                'method': 'advanced',
                'options': {'precision': 'high', 'include_plots': True}
            }
        })
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5, f"Complex analysis took {execution_time:.3f}s, should be <500ms")
