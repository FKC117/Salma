"""
Contract Test: POST /api/sessions/ (T014)
Tests the session creation API endpoint according to the API schema
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

class TestSessionsPostContract(TestCase):
    """Contract tests for POST /api/sessions/ endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock dataset
        self.dataset_id = 1
        self.dataset_name = "Test Dataset"
    
    def test_create_session_success(self):
        """Test successful session creation"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_123456789',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active'
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Test Session'
            }, format='json')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('session_id', response.data)
            self.assertIn('dataset_id', response.data)
            self.assertIn('dataset_name', response.data)
            self.assertIn('created_at', response.data)
            self.assertIn('status', response.data)
            
            # Verify data types
            self.assertIsInstance(response.data['session_id'], str)
            self.assertIsInstance(response.data['dataset_id'], int)
            self.assertIsInstance(response.data['dataset_name'], str)
            self.assertIsInstance(response.data['created_at'], str)
            self.assertIsInstance(response.data['status'], str)
    
    def test_create_session_with_dataset_override(self):
        """Test session creation with dataset override"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_987654321',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'override_existing': True
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Override Session',
                'override_existing': True
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('session_id', response.data)
            self.assertIn('override_existing', response.data)
    
    def test_create_session_missing_dataset_id(self):
        """Test session creation without dataset_id"""
        response = self.client.post('/api/sessions/', {
            'session_name': 'No Dataset Session'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('dataset_id is required', response.data['error'])
    
    def test_create_session_invalid_dataset_id(self):
        """Test session creation with invalid dataset_id"""
        response = self.client.post('/api/sessions/', {
            'dataset_id': 99999,  # Non-existent dataset
            'session_name': 'Invalid Dataset Session'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('Dataset not found', response.data['error'])
    
    def test_create_session_unauthenticated(self):
        """Test session creation without authentication"""
        client = APIClient()  # No authentication
        
        response = client.post('/api/sessions/', {
            'dataset_id': self.dataset_id,
            'session_name': 'Unauthenticated Session'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_session_unauthorized_dataset(self):
        """Test session creation with dataset user doesn't own"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        with patch('analytics.services.session_manager.SessionManager.check_dataset_access') as mock_check:
            mock_check.return_value = False
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Unauthorized Session'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn('error', response.data)
            self.assertIn('Access denied', response.data['error'])
    
    def test_create_session_existing_session(self):
        """Test session creation when session already exists"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': False,
                'error': 'Session already exists for this dataset'
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Existing Session'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
            self.assertIn('error', response.data)
            self.assertIn('Session already exists', response.data['error'])
    
    def test_create_session_with_analysis_history(self):
        """Test session creation with analysis history loading"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_with_history',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'analysis_history': [
                    {
                        'analysis_id': 1,
                        'tool_name': 'descriptive_stats',
                        'created_at': '2025-09-23T14:00:00Z',
                        'status': 'completed'
                    },
                    {
                        'analysis_id': 2,
                        'tool_name': 'correlation_matrix',
                        'created_at': '2025-09-23T14:30:00Z',
                        'status': 'completed'
                    }
                ]
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Session with History',
                'load_history': True
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('analysis_history', response.data)
            self.assertIsInstance(response.data['analysis_history'], list)
            self.assertEqual(len(response.data['analysis_history']), 2)
    
    def test_create_session_response_schema(self):
        """Test that response matches the expected schema"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_schema_test',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'user_id': self.user.id,
                'session_name': 'Schema Test Session'
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Schema Test Session'
            }, format='json')
            
            # Verify all required fields are present
            required_fields = [
                'session_id', 'dataset_id', 'dataset_name', 'created_at', 
                'status', 'user_id', 'session_name'
            ]
            
            for field in required_fields:
                self.assertIn(field, response.data, f"Missing required field: {field}")
            
            # Verify field types
            self.assertIsInstance(response.data['session_id'], str)
            self.assertIsInstance(response.data['dataset_id'], int)
            self.assertIsInstance(response.data['dataset_name'], str)
            self.assertIsInstance(response.data['created_at'], str)
            self.assertIsInstance(response.data['status'], str)
            self.assertIsInstance(response.data['user_id'], int)
            self.assertIsInstance(response.data['session_name'], str)
    
    def test_create_session_audit_logging(self):
        """Test that session creation is properly logged for audit"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_audit_test',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active'
            }
            
            with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
                response = self.client.post('/api/sessions/', {
                    'dataset_id': self.dataset_id,
                    'session_name': 'Audit Test Session'
                }, format='json')
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                self.assertEqual(call_args[1]['action'], 'session_create')
                self.assertEqual(call_args[1]['resource'], 'analysis_session')
                self.assertEqual(call_args[1]['success'], True)
    
    def test_create_session_with_custom_settings(self):
        """Test session creation with custom settings"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_custom_settings',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'settings': {
                    'auto_save': True,
                    'cache_results': True,
                    'max_history_items': 50
                }
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Custom Settings Session',
                'settings': {
                    'auto_save': True,
                    'cache_results': True,
                    'max_history_items': 50
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('settings', response.data)
            self.assertIsInstance(response.data['settings'], dict)
            self.assertTrue(response.data['settings']['auto_save'])
            self.assertTrue(response.data['settings']['cache_results'])
            self.assertEqual(response.data['settings']['max_history_items'], 50)
