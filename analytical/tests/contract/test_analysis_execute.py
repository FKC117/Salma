"""
Contract Test: POST /api/analysis/execute/ (T015)
Tests the analysis execution API endpoint according to the API schema
"""

import pytest
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestAnalysisExecuteContract(TestCase):
    """Contract tests for POST /api/analysis/execute/ endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock session and dataset
        self.session_id = 'sess_123456789'
        self.dataset_id = 1
        self.tool_name = 'descriptive_stats'
    
    def test_execute_analysis_success(self):
        """Test successful analysis execution"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'analysis_id': 1,
                'tool_name': self.tool_name,
                'status': 'completed',
                'results': {
                    'summary': 'Descriptive statistics calculated',
                    'tables': [
                        {
                            'title': 'Summary Statistics',
                            'data': [
                                {'column': 'age', 'mean': 30.0, 'std': 5.0, 'min': 25, 'max': 35},
                                {'column': 'salary', 'mean': 50000.0, 'std': 10000.0, 'min': 40000, 'max': 60000}
                            ]
                        }
                    ],
                    'charts': [
                        {
                            'title': 'Age Distribution',
                            'type': 'histogram',
                            'image_url': '/media/charts/age_histogram.png'
                        }
                    ]
                },
                'execution_time': 2.5,
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            response = self.client.post('/api/analysis/execute/', {
                'session_id': self.session_id,
                'tool_name': self.tool_name,
                'parameters': {
                    'columns': ['age', 'salary'],
                    'include_charts': True
                }
            }, format='json')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('analysis_id', response.data)
            self.assertIn('tool_name', response.data)
            self.assertIn('status', response.data)
            self.assertIn('results', response.data)
            self.assertIn('execution_time', response.data)
            self.assertIn('created_at', response.data)
            
            # Verify data types
            self.assertIsInstance(response.data['analysis_id'], int)
            self.assertIsInstance(response.data['tool_name'], str)
            self.assertIsInstance(response.data['status'], str)
            self.assertIsInstance(response.data['results'], dict)
            self.assertIsInstance(response.data['execution_time'], float)
            self.assertIsInstance(response.data['created_at'], str)
    
    def test_execute_analysis_with_caching(self):
        """Test analysis execution with cached results"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'analysis_id': 1,
                'tool_name': self.tool_name,
                'status': 'completed',
                'results': {
                    'summary': 'Cached results',
                    'tables': []
                },
                'execution_time': 0.1,  # Very fast due to caching
                'created_at': '2025-09-23T15:00:00Z',
                'cached': True
            }
            
            response = self.client.post('/api/analysis/execute/', {
                'session_id': self.session_id,
                'tool_name': self.tool_name,
                'parameters': {
                    'columns': ['age', 'salary']
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('cached', response.data)
            self.assertTrue(response.data['cached'])
    
    def test_execute_analysis_missing_session_id(self):
        """Test analysis execution without session_id"""
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': self.tool_name,
            'parameters': {
                'columns': ['age', 'salary']
            }
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('session_id is required', response.data['error'])
    
    def test_execute_analysis_missing_tool_name(self):
        """Test analysis execution without tool_name"""
        response = self.client.post('/api/analysis/execute/', {
            'session_id': self.session_id,
            'parameters': {
                'columns': ['age', 'salary']
            }
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('tool_name is required', response.data['error'])
    
    def test_execute_analysis_invalid_session(self):
        """Test analysis execution with invalid session_id"""
        response = self.client.post('/api/analysis/execute/', {
            'session_id': 'invalid_session',
            'tool_name': self.tool_name,
            'parameters': {
                'columns': ['age', 'salary']
            }
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('Session not found', response.data['error'])
    
    def test_execute_analysis_invalid_tool(self):
        """Test analysis execution with invalid tool_name"""
        response = self.client.post('/api/analysis/execute/', {
            'session_id': self.session_id,
            'tool_name': 'invalid_tool',
            'parameters': {
                'columns': ['age', 'salary']
            }
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('Tool not found', response.data['error'])
    
    def test_execute_analysis_unauthenticated(self):
        """Test analysis execution without authentication"""
        client = APIClient()  # No authentication
        
        response = client.post('/api/analysis/execute/', {
            'session_id': self.session_id,
            'tool_name': self.tool_name,
            'parameters': {
                'columns': ['age', 'salary']
            }
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_execute_analysis_unauthorized_session(self):
        """Test analysis execution with session user doesn't own"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.check_session_access') as mock_check:
            mock_check.return_value = False
            
            response = self.client.post('/api/analysis/execute/', {
                'session_id': self.session_id,
                'tool_name': self.tool_name,
                'parameters': {
                    'columns': ['age', 'salary']
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn('error', response.data)
            self.assertIn('Access denied', response.data['error'])
    
    def test_execute_analysis_processing_error(self):
        """Test analysis execution when processing fails"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
            mock_execute.return_value = {
                'success': False,
                'error': 'Analysis processing failed',
                'analysis_id': 1,
                'status': 'failed'
            }
            
            response = self.client.post('/api/analysis/execute/', {
                'session_id': self.session_id,
                'tool_name': self.tool_name,
                'parameters': {
                    'columns': ['age', 'salary']
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
            self.assertIn('Analysis processing failed', response.data['error'])
    
    def test_execute_analysis_with_images(self):
        """Test analysis execution that generates images"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'analysis_id': 1,
                'tool_name': 'correlation_matrix',
                'status': 'completed',
                'results': {
                    'summary': 'Correlation matrix generated',
                    'tables': [
                        {
                            'title': 'Correlation Matrix',
                            'data': [
                                {'var1': 'age', 'var2': 'salary', 'correlation': 0.75}
                            ]
                        }
                    ],
                    'charts': [
                        {
                            'title': 'Correlation Heatmap',
                            'type': 'heatmap',
                            'image_url': '/media/charts/correlation_heatmap.png',
                            'image_data': 'base64_encoded_image_data'
                        }
                    ]
                },
                'execution_time': 3.2,
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            response = self.client.post('/api/analysis/execute/', {
                'session_id': self.session_id,
                'tool_name': 'correlation_matrix',
                'parameters': {
                    'columns': ['age', 'salary'],
                    'include_heatmap': True
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('charts', response.data['results'])
            self.assertEqual(len(response.data['results']['charts']), 1)
            self.assertIn('image_url', response.data['results']['charts'][0])
            self.assertIn('image_data', response.data['results']['charts'][0])
    
    def test_execute_analysis_response_schema(self):
        """Test that response matches the expected schema"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'analysis_id': 1,
                'tool_name': self.tool_name,
                'status': 'completed',
                'results': {
                    'summary': 'Test analysis',
                    'tables': [],
                    'charts': []
                },
                'execution_time': 1.5,
                'created_at': '2025-09-23T15:00:00Z',
                'user_id': self.user.id,
                'session_id': self.session_id
            }
            
            response = self.client.post('/api/analysis/execute/', {
                'session_id': self.session_id,
                'tool_name': self.tool_name,
                'parameters': {
                    'columns': ['age', 'salary']
                }
            }, format='json')
            
            # Verify all required fields are present
            required_fields = [
                'analysis_id', 'tool_name', 'status', 'results', 
                'execution_time', 'created_at', 'user_id', 'session_id'
            ]
            
            for field in required_fields:
                self.assertIn(field, response.data, f"Missing required field: {field}")
            
            # Verify field types
            self.assertIsInstance(response.data['analysis_id'], int)
            self.assertIsInstance(response.data['tool_name'], str)
            self.assertIsInstance(response.data['status'], str)
            self.assertIsInstance(response.data['results'], dict)
            self.assertIsInstance(response.data['execution_time'], float)
            self.assertIsInstance(response.data['created_at'], str)
            self.assertIsInstance(response.data['user_id'], int)
            self.assertIsInstance(response.data['session_id'], str)
    
    def test_execute_analysis_audit_logging(self):
        """Test that analysis execution is properly logged for audit"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'analysis_id': 1,
                'tool_name': self.tool_name,
                'status': 'completed',
                'results': {'summary': 'Test analysis'},
                'execution_time': 1.5,
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
                response = self.client.post('/api/analysis/execute/', {
                    'session_id': self.session_id,
                    'tool_name': self.tool_name,
                    'parameters': {
                        'columns': ['age', 'salary']
                    }
                }, format='json')
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                self.assertEqual(call_args[1]['action'], 'analysis_execute')
                self.assertEqual(call_args[1]['resource'], 'analysis_result')
                self.assertEqual(call_args[1]['success'], True)
    
    def test_execute_analysis_with_llm_interpretation(self):
        """Test analysis execution with LLM interpretation"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'analysis_id': 1,
                'tool_name': self.tool_name,
                'status': 'completed',
                'results': {
                    'summary': 'Descriptive statistics calculated',
                    'tables': [
                        {
                            'title': 'Summary Statistics',
                            'data': [{'column': 'age', 'mean': 30.0, 'std': 5.0}]
                        }
                    ],
                    'charts': [],
                    'llm_interpretation': {
                        'summary': 'The data shows a normal distribution with moderate variability',
                        'insights': [
                            'The mean age is 30 years',
                            'Standard deviation indicates moderate spread',
                            'No significant outliers detected'
                        ],
                        'recommendations': [
                            'Consider further analysis of age groups',
                            'Investigate correlation with other variables'
                        ]
                    }
                },
                'execution_time': 4.2,  # Longer due to LLM processing
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            response = self.client.post('/api/analysis/execute/', {
                'session_id': self.session_id,
                'tool_name': self.tool_name,
                'parameters': {
                    'columns': ['age', 'salary'],
                    'include_llm_interpretation': True
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('llm_interpretation', response.data['results'])
            self.assertIn('summary', response.data['results']['llm_interpretation'])
            self.assertIn('insights', response.data['results']['llm_interpretation'])
            self.assertIn('recommendations', response.data['results']['llm_interpretation'])
