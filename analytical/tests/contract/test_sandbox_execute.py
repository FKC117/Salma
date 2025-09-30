"""
Contract Test: POST /api/sandbox/execute/ (T104.12)
Tests the sandbox code execution API endpoint according to the API schema
"""

import pytest
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from analytics.models import AnalysisSession, Dataset

class TestSandboxExecuteContract(TestCase):
    """Contract tests for POST /api/sandbox/execute/ endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test dataset
        self.dataset = Dataset.objects.create(
            name='Test Dataset',
            user=self.user,
            row_count=100,
            column_count=5,
            file_size_bytes=1024,
            processing_status='completed'
        )
        
        # Create test session
        self.session = AnalysisSession.objects.create(
            name='Test Session',
            user=self.user,
            primary_dataset=self.dataset
        )
    
    def test_execute_sandbox_code_success(self):
        """Test successful sandbox code execution"""
        with patch('analytics.services.sandbox_executor.SandboxExecutor.execute_code') as mock_execute:
            # Mock successful execution result
            mock_execution = MagicMock()
            mock_execution.status = 'completed'
            mock_execution.output = 'Hello, World!'
            mock_execution.error_message = None
            mock_execution.execution_time_ms = 150
            mock_execution.memory_used_mb = 25.5
            
            mock_execute.return_value = mock_execution
            
            response = self.client.post('/api/sandbox/execute/', {
                'code': 'print("Hello, World!")',
                'language': 'python'
            }, format='json')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('success', response.data)
            self.assertTrue(response.data['success'])
            self.assertIn('status', response.data)
            self.assertEqual(response.data['status'], 'completed')
            self.assertIn('output', response.data)
            self.assertEqual(response.data['output'], 'Hello, World!')
            self.assertIn('execution_time_ms', response.data)
            self.assertIn('memory_used_mb', response.data)
    
    def test_execute_sandbox_code_with_structured_output(self):
        """Test sandbox code execution with structured output (plots, tables)"""
        with patch('analytics.services.sandbox_executor.SandboxExecutor.execute_code') as mock_execute:
            # Mock successful execution result with structured output
            mock_execution = MagicMock()
            mock_execution.status = 'completed'
            mock_execution.output = '{"plots": ["/media/plots/chart1.png"], "tables": [{"title": "Results", "data": [["A", "B"], [1, 2]]}]}'
            mock_execution.error_message = None
            mock_execution.execution_time_ms = 200
            mock_execution.memory_used_mb = 30.0
            
            mock_execute.return_value = mock_execution
            
            response = self.client.post('/api/sandbox/execute/', {
                'code': 'import json; print(json.dumps({"plots": ["/media/plots/chart1.png"], "tables": [{"title": "Results", "data": [["A", "B"], [1, 2]]}]}))',
                'language': 'python'
            }, format='json')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['status'], 'completed')
            self.assertIn('output', response.data)
    
    def test_execute_sandbox_code_failure(self):
        """Test failed sandbox code execution"""
        with patch('analytics.services.sandbox_executor.SandboxExecutor.execute_code') as mock_execute:
            # Mock failed execution result
            mock_execution = MagicMock()
            mock_execution.status = 'failed'
            mock_execution.output = ''
            mock_execution.error_message = 'NameError: name \'undefined_var\' is not defined'
            mock_execution.execution_time_ms = 100
            mock_execution.memory_used_mb = 15.0
            
            mock_execute.return_value = mock_execution
            
            response = self.client.post('/api/sandbox/execute/', {
                'code': 'print(undefined_var)',
                'language': 'python'
            }, format='json')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('success', response.data)
            self.assertFalse(response.data['success'])
            self.assertIn('status', response.data)
            self.assertEqual(response.data['status'], 'failed')
            self.assertIn('error', response.data)
            self.assertIn('NameError', response.data['error'])
    
    def test_execute_sandbox_code_missing_code(self):
        """Test sandbox execution without code"""
        response = self.client.post('/api/sandbox/execute/', {
            'language': 'python'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)
        self.assertIn('No code provided', response.data['error'])
    
    def test_execute_sandbox_code_empty_code(self):
        """Test sandbox execution with empty code"""
        response = self.client.post('/api/sandbox/execute/', {
            'code': '',
            'language': 'python'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('No code provided', response.data['error'])
    
    def test_execute_sandbox_code_unauthenticated(self):
        """Test sandbox execution without authentication"""
        client = APIClient()  # No authentication
        
        response = client.post('/api/sandbox/execute/', {
            'code': 'print("Hello, World!")',
            'language': 'python'
        }, format='json')
        
        # Should still work (fallback to default user in development)
        self.assertEqual(response.status_code, status.HTTP_200_OK)