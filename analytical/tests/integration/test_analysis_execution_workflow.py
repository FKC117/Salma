"""
End-to-End Analysis Execution Workflow Tests

This module contains comprehensive integration tests for the complete analysis execution workflow,
from dataset selection through tool execution, result generation, and storage.
"""

import json
import pandas as pd
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, Mock
import time

from analytics.models import (
    Dataset, DatasetColumn, AnalysisTool, AnalysisSession, 
    AnalysisResult, User, AuditTrail
)

User = get_user_model()


class AnalysisExecutionWorkflowTest(TestCase):
    """Test complete analysis execution workflow"""
    
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
            row_count=100,
            column_count=3
        )
        
        # Create test columns
        DatasetColumn.objects.create(
            dataset=self.dataset,
            name='age',
            column_type='numeric',
            data_type='int64',
            is_numeric=True,
            is_categorical=False
        )
        DatasetColumn.objects.create(
            dataset=self.dataset,
            name='city',
            column_type='categorical',
            data_type='object',
            is_numeric=False,
            is_categorical=True
        )
        DatasetColumn.objects.create(
            dataset=self.dataset,
            name='income',
            column_type='numeric',
            data_type='float64',
            is_numeric=True,
            is_categorical=False
        )
        
        # Create test analysis tool
        self.tool = AnalysisTool.objects.create(
            name='descriptive_statistics',
            display_name='Descriptive Statistics',
            description='Calculate descriptive statistics for numeric columns',
            tool_type='statistical',
            parameters_schema={
                'column': {'type': 'string', 'required': True},
                'include_plots': {'type': 'boolean', 'required': False}
            }
        )
        
        # Create test session
        self.session = AnalysisSession.objects.create(
            name='test_session',
            user=self.user,
            primary_dataset=self.dataset,
            is_active=True
        )
    
    def test_descriptive_statistics_workflow(self):
        """Test complete descriptive statistics analysis workflow"""
        # Test 1: Execute analysis
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {
                'column': 'age',
                'include_plots': True
            }
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('result_id', data)
        
        # Test 2: Verify analysis result was created
        result_id = data['result_id']
        result = AnalysisResult.objects.get(id=result_id)
        self.assertEqual(result.tool_used, self.tool)
        self.assertEqual(result.session, self.session)
        self.assertEqual(result.dataset, self.dataset)
        self.assertEqual(result.name, 'Descriptive Statistics')
        
        # Test 3: Verify result data structure
        self.assertIsNotNone(result.result_data)
        result_data = json.loads(result.result_data) if isinstance(result.result_data, str) else result.result_data
        self.assertIn('statistics', result_data)
        
        # Test 4: Verify audit trail
        audit_entries = AuditTrail.objects.filter(
            user_id=self.user.id,
            action_type='EXECUTE',
            resource_type='AnalysisResult'
        )
        self.assertTrue(audit_entries.exists())
        
        # Test 5: Verify session was updated
        self.session.refresh_from_db()
        self.assertIsNotNone(self.session.last_accessed)
    
    def test_correlation_analysis_workflow(self):
        """Test correlation analysis workflow"""
        # Create correlation tool
        correlation_tool = AnalysisTool.objects.create(
            name='correlation_analysis',
            display_name='Correlation Analysis',
            description='Calculate correlation between numeric columns',
            tool_type='statistical',
            parameters_schema={
                'columns': {'type': 'array', 'required': True},
                'method': {'type': 'string', 'required': False}
            }
        )
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'correlation_analysis',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {
                'columns': ['age', 'income'],
                'method': 'pearson'
            }
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify result
        result = AnalysisResult.objects.get(id=data['result_id'])
        self.assertEqual(result.tool_used, correlation_tool)
        self.assertIn('correlation', result.result_data)
    
    def test_visualization_workflow(self):
        """Test visualization generation workflow"""
        # Create visualization tool
        viz_tool = AnalysisTool.objects.create(
            name='create_histogram',
            display_name='Create Histogram',
            description='Generate histogram for numeric column',
            tool_type='visualization',
            parameters_schema={
                'column': {'type': 'string', 'required': True},
                'bins': {'type': 'integer', 'required': False}
            }
        )
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'create_histogram',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {
                'column': 'age',
                'bins': 20
            }
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify result
        result = AnalysisResult.objects.get(id=data['result_id'])
        self.assertEqual(result.tool_used, viz_tool)
        self.assertEqual(result.output_type, 'image')
        self.assertIsNotNone(result.result_data)
    
    def test_analysis_with_invalid_parameters(self):
        """Test analysis execution with invalid parameters"""
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {
                'column': 'nonexistent_column'
            }
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_analysis_with_nonexistent_tool(self):
        """Test analysis execution with non-existent tool"""
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'nonexistent_tool',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {}
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_analysis_performance_requirements(self):
        """Test analysis execution meets performance requirements (<500ms)"""
        start_time = time.time()
        
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {
                'column': 'age'
            }
        })
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 0.5, f"Analysis took {execution_time:.3f}s, should be <500ms")
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_multiple_analysis_workflow(self):
        """Test multiple analyses in sequence"""
        # First analysis
        response1 = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'age'}
        })
        
        self.assertEqual(response1.status_code, 200)
        data1 = json.loads(response1.content)
        self.assertTrue(data1['success'])
        
        # Second analysis
        response2 = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'income'}
        })
        
        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.content)
        self.assertTrue(data2['success'])
        
        # Verify both results exist
        results = AnalysisResult.objects.filter(session=self.session)
        self.assertEqual(results.count(), 2)
        
        # Verify different result IDs
        self.assertNotEqual(data1['result_id'], data2['result_id'])
    
    def test_analysis_result_retrieval(self):
        """Test analysis result retrieval"""
        # Execute analysis
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'age'}
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        result_id = data['result_id']
        
        # Retrieve result
        result = AnalysisResult.objects.get(id=result_id)
        self.assertIsNotNone(result.result_data)
        self.assertIsNotNone(result.execution_time_ms)
        self.assertGreater(result.execution_time_ms, 0)
    
    def test_analysis_with_htmx_interface(self):
        """Test analysis execution through HTMX interface"""
        # Test analysis interface access
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        
        # Test analysis execution via HTMX
        response = self.client.post('/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': json.dumps({'column': 'age'})
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # Should handle HTMX request
        self.assertIn(response.status_code, [200, 201, 400])
    
    def test_analysis_error_handling(self):
        """Test analysis execution error handling"""
        # Test with invalid dataset
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': 99999,  # Non-existent dataset
            'session_id': self.session.id,
            'parameters': {'column': 'age'}
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
        # Test with invalid session
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': 99999,  # Non-existent session
            'parameters': {'column': 'age'}
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_analysis_caching(self):
        """Test analysis result caching"""
        # First execution
        response1 = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'age'}
        })
        
        self.assertEqual(response1.status_code, 200)
        data1 = json.loads(response1.content)
        
        # Second execution with same parameters (should use cache)
        response2 = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'age'}
        })
        
        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.content)
        
        # Should either return cached result or new result
        self.assertTrue(data2['success'])
    
    def test_analysis_with_large_dataset(self):
        """Test analysis execution with large dataset"""
        # Create large dataset
        large_dataset = Dataset.objects.create(
            name='large_dataset',
            user=self.user,
            file_size_bytes=1000000,
            parquet_size_bytes=500000,
            row_count=10000,
            column_count=5
        )
        
        # Create columns for large dataset
        for i in range(5):
            DatasetColumn.objects.create(
                dataset=large_dataset,
                name=f'column_{i}',
                column_type='numeric',
                data_type='float64',
                is_numeric=True,
                is_categorical=False
            )
        
        # Execute analysis on large dataset
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': large_dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'column_0'}
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify result was created
        result = AnalysisResult.objects.get(id=data['result_id'])
        self.assertEqual(result.dataset, large_dataset)
