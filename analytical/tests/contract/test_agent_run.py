"""
Contract Test: POST /api/agent/run/ (T018)
Tests the agentic AI run API endpoint according to the API schema
"""

import pytest
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestAgentRunContract(TestCase):
    """Contract tests for POST /api/agent/run/ endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock dataset and session
        self.dataset_id = 1
        self.session_id = 'sess_123456789'
        self.goal = 'Analyze the relationship between age and salary in the dataset'
    
    def test_start_agent_run_success(self):
        """Test successful agent run start"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': True,
                'agent_run_id': 1,
                'status': 'planning',
                'correlation_id': 'agent_123456789',
                'estimated_completion_time': 300,  # 5 minutes
                'progress_url': '/api/agent/run/1/status/',
                'goal': self.goal,
                'constraints': {
                    'max_steps': 20,
                    'max_cost': 10000,
                    'max_time': 1800
                },
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal,
                'constraints': {
                    'max_steps': 20,
                    'max_cost': 10000,
                    'max_time': 1800
                },
                'agent_config': {
                    'agent_version': '1.0',
                    'llm_model': 'gemini-1.5-flash',
                    'planning_mode': 'balanced',
                    'auto_retry': True,
                    'human_feedback': False
                }
            }, format='json')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('agent_run_id', response.data)
            self.assertIn('status', response.data)
            self.assertIn('correlation_id', response.data)
            self.assertIn('estimated_completion_time', response.data)
            self.assertIn('progress_url', response.data)
            self.assertIn('goal', response.data)
            self.assertIn('constraints', response.data)
            self.assertIn('created_at', response.data)
            
            # Verify data types
            self.assertIsInstance(response.data['agent_run_id'], int)
            self.assertIsInstance(response.data['status'], str)
            self.assertIsInstance(response.data['correlation_id'], str)
            self.assertIsInstance(response.data['estimated_completion_time'], int)
            self.assertIsInstance(response.data['progress_url'], str)
            self.assertIsInstance(response.data['goal'], str)
            self.assertIsInstance(response.data['constraints'], dict)
            self.assertIsInstance(response.data['created_at'], str)
    
    def test_start_agent_run_with_default_constraints(self):
        """Test agent run start with default constraints"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': True,
                'agent_run_id': 2,
                'status': 'planning',
                'correlation_id': 'agent_987654321',
                'estimated_completion_time': 600,  # 10 minutes
                'progress_url': '/api/agent/run/2/status/',
                'goal': self.goal,
                'constraints': {
                    'max_steps': 20,
                    'max_cost': 10000,
                    'max_time': 1800
                },
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('constraints', response.data)
            self.assertEqual(response.data['constraints']['max_steps'], 20)
            self.assertEqual(response.data['constraints']['max_cost'], 10000)
            self.assertEqual(response.data['constraints']['max_time'], 1800)
    
    def test_start_agent_run_missing_dataset_id(self):
        """Test agent run start without dataset_id"""
        response = self.client.post('/api/agent/run/', {
            'goal': self.goal
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('dataset_id is required', response.data['error'])
    
    def test_start_agent_run_missing_goal(self):
        """Test agent run start without goal"""
        response = self.client.post('/api/agent/run/', {
            'dataset_id': self.dataset_id
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('goal is required', response.data['error'])
    
    def test_start_agent_run_empty_goal(self):
        """Test agent run start with empty goal"""
        response = self.client.post('/api/agent/run/', {
            'dataset_id': self.dataset_id,
            'goal': ''
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Goal cannot be empty', response.data['error'])
    
    def test_start_agent_run_invalid_dataset_id(self):
        """Test agent run start with invalid dataset_id"""
        response = self.client.post('/api/agent/run/', {
            'dataset_id': 99999,  # Non-existent dataset
            'goal': self.goal
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('Dataset not found', response.data['error'])
    
    def test_start_agent_run_unauthenticated(self):
        """Test agent run start without authentication"""
        client = APIClient()  # No authentication
        
        response = client.post('/api/agent/run/', {
            'dataset_id': self.dataset_id,
            'goal': self.goal
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_start_agent_run_unauthorized_dataset(self):
        """Test agent run start with dataset user doesn't own"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.check_dataset_access') as mock_check:
            mock_check.return_value = False
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn('error', response.data)
            self.assertIn('Access denied', response.data['error'])
    
    def test_start_agent_run_existing_active_run(self):
        """Test agent run start when user has active run"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': False,
                'error': 'User already has an active agent run'
            }
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
            self.assertIn('error', response.data)
            self.assertIn('User already has an active agent run', response.data['error'])
    
    def test_start_agent_run_planning_failed(self):
        """Test agent run start when planning fails"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': False,
                'error': 'Failed to create analysis plan',
                'agent_run_id': 3,
                'status': 'failed'
            }
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
            self.assertIn('Failed to create analysis plan', response.data['error'])
    
    def test_start_agent_run_with_custom_config(self):
        """Test agent run start with custom agent configuration"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': True,
                'agent_run_id': 4,
                'status': 'planning',
                'correlation_id': 'agent_custom_config',
                'estimated_completion_time': 900,  # 15 minutes
                'progress_url': '/api/agent/run/4/status/',
                'goal': self.goal,
                'constraints': {
                    'max_steps': 50,
                    'max_cost': 50000,
                    'max_time': 3600
                },
                'agent_config': {
                    'agent_version': '1.0',
                    'llm_model': 'gemini-1.5-flash',
                    'planning_mode': 'aggressive',
                    'auto_retry': True,
                    'human_feedback': True
                },
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal,
                'constraints': {
                    'max_steps': 50,
                    'max_cost': 50000,
                    'max_time': 3600
                },
                'agent_config': {
                    'agent_version': '1.0',
                    'llm_model': 'gemini-1.5-flash',
                    'planning_mode': 'aggressive',
                    'auto_retry': True,
                    'human_feedback': True
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('agent_config', response.data)
            self.assertEqual(response.data['agent_config']['planning_mode'], 'aggressive')
            self.assertTrue(response.data['agent_config']['human_feedback'])
    
    def test_start_agent_run_response_schema(self):
        """Test that response matches the expected schema"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': True,
                'agent_run_id': 5,
                'status': 'planning',
                'correlation_id': 'agent_schema_test',
                'estimated_completion_time': 300,
                'progress_url': '/api/agent/run/5/status/',
                'goal': self.goal,
                'constraints': {
                    'max_steps': 20,
                    'max_cost': 10000,
                    'max_time': 1800
                },
                'agent_config': {
                    'agent_version': '1.0',
                    'llm_model': 'gemini-1.5-flash',
                    'planning_mode': 'balanced',
                    'auto_retry': True,
                    'human_feedback': False
                },
                'created_at': '2025-09-23T15:00:00Z',
                'user_id': self.user.id,
                'dataset_id': self.dataset_id
            }
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal
            }, format='json')
            
            # Verify all required fields are present
            required_fields = [
                'agent_run_id', 'status', 'correlation_id', 'estimated_completion_time',
                'progress_url', 'goal', 'constraints', 'agent_config', 'created_at',
                'user_id', 'dataset_id'
            ]
            
            for field in required_fields:
                self.assertIn(field, response.data, f"Missing required field: {field}")
            
            # Verify field types
            self.assertIsInstance(response.data['agent_run_id'], int)
            self.assertIsInstance(response.data['status'], str)
            self.assertIsInstance(response.data['correlation_id'], str)
            self.assertIsInstance(response.data['estimated_completion_time'], int)
            self.assertIsInstance(response.data['progress_url'], str)
            self.assertIsInstance(response.data['goal'], str)
            self.assertIsInstance(response.data['constraints'], dict)
            self.assertIsInstance(response.data['agent_config'], dict)
            self.assertIsInstance(response.data['created_at'], str)
            self.assertIsInstance(response.data['user_id'], int)
            self.assertIsInstance(response.data['dataset_id'], int)
    
    def test_start_agent_run_audit_logging(self):
        """Test that agent run start is properly logged for audit"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': True,
                'agent_run_id': 6,
                'status': 'planning',
                'correlation_id': 'agent_audit_test',
                'estimated_completion_time': 300,
                'progress_url': '/api/agent/run/6/status/',
                'goal': self.goal,
                'constraints': {
                    'max_steps': 20,
                    'max_cost': 10000,
                    'max_time': 1800
                },
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
                response = self.client.post('/api/agent/run/', {
                    'dataset_id': self.dataset_id,
                    'goal': self.goal
                }, format='json')
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                self.assertEqual(call_args[1]['action'], 'agent_run_start')
                self.assertEqual(call_args[1]['resource'], 'agent_run')
                self.assertEqual(call_args[1]['success'], True)
    
    def test_start_agent_run_with_celery_integration(self):
        """Test agent run start with Celery task integration"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': True,
                'agent_run_id': 7,
                'status': 'planning',
                'correlation_id': 'agent_celery_test',
                'estimated_completion_time': 300,
                'progress_url': '/api/agent/run/7/status/',
                'goal': self.goal,
                'constraints': {
                    'max_steps': 20,
                    'max_cost': 10000,
                    'max_time': 1800
                },
                'celery_task_id': 'celery_task_123456789',
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('celery_task_id', response.data)
            self.assertIsInstance(response.data['celery_task_id'], str)
    
    def test_start_agent_run_with_resource_validation(self):
        """Test agent run start with resource constraint validation"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': False,
                'error': 'Resource constraints exceeded',
                'validation_errors': {
                    'max_steps': 'Maximum steps cannot exceed 100',
                    'max_cost': 'Maximum cost cannot exceed 100000 tokens',
                    'max_time': 'Maximum time cannot exceed 3600 seconds'
                }
            }
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal,
                'constraints': {
                    'max_steps': 150,  # Exceeds limit
                    'max_cost': 150000,  # Exceeds limit
                    'max_time': 7200  # Exceeds limit
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)
            self.assertIn('validation_errors', response.data)
            self.assertIn('max_steps', response.data['validation_errors'])
            self.assertIn('max_cost', response.data['validation_errors'])
            self.assertIn('max_time', response.data['validation_errors'])
