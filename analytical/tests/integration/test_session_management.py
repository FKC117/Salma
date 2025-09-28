"""
Integration Test: Analysis Session Management (T021)
Tests the complete analysis session management workflow
"""

import pytest
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestSessionManagementWorkflow(TestCase):
    """Integration tests for analysis session management workflow"""
    
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
    
    def test_complete_session_creation_workflow(self):
        """Test complete session creation workflow"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_123456789',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'session_info': {
                    'user_id': self.user.id,
                    'session_name': 'Test Session',
                    'dataset_columns': ['name', 'age', 'city', 'salary'],
                    'column_types': {
                        'name': 'categorical',
                        'age': 'numeric',
                        'city': 'categorical',
                        'salary': 'numeric'
                    },
                    'available_tools': [
                        'descriptive_stats',
                        'correlation_matrix',
                        'regression_analysis'
                    ]
                }
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Test Session'
            }, format='json')
            
            # Verify session creation
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('session_id', response.data)
            self.assertIn('session_info', response.data)
            self.assertIn('available_tools', response.data['session_info'])
            
            # Verify session manager was called
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            self.assertEqual(call_args[1]['user_id'], self.user.id)
            self.assertEqual(call_args[1]['dataset_id'], self.dataset_id)
    
    def test_session_creation_with_analysis_history(self):
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
                        'status': 'completed',
                        'results_summary': 'Basic statistics calculated',
                        'execution_time': 2.5
                    },
                    {
                        'analysis_id': 2,
                        'tool_name': 'correlation_matrix',
                        'created_at': '2025-09-23T14:30:00Z',
                        'status': 'completed',
                        'results_summary': 'Correlation matrix generated',
                        'execution_time': 3.2
                    }
                ],
                'history_summary': {
                    'total_analyses': 2,
                    'completed_analyses': 2,
                    'failed_analyses': 0,
                    'total_execution_time': 5.7,
                    'most_used_tool': 'descriptive_stats'
                }
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Session with History',
                'load_history': True
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('analysis_history', response.data)
            self.assertIn('history_summary', response.data)
            self.assertEqual(len(response.data['analysis_history']), 2)
            self.assertEqual(response.data['history_summary']['total_analyses'], 2)
    
    def test_session_creation_with_dataset_override(self):
        """Test session creation with dataset override functionality"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_override',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'override_info': {
                    'previous_session_id': 'sess_old_123',
                    'override_reason': 'User requested new session',
                    'previous_analyses_preserved': True,
                    'previous_analyses_count': 5
                }
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Override Session',
                'override_existing': True
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('override_info', response.data)
            self.assertTrue(response.data['override_info']['previous_analyses_preserved'])
    
    def test_session_creation_with_custom_settings(self):
        """Test session creation with custom settings"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_custom',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'settings': {
                    'auto_save': True,
                    'cache_results': True,
                    'max_history_items': 50,
                    'notification_preferences': {
                        'email_notifications': True,
                        'browser_notifications': False
                    },
                    'analysis_preferences': {
                        'default_tool': 'descriptive_stats',
                        'include_charts': True,
                        'include_llm_interpretation': True
                    }
                }
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Custom Settings Session',
                'settings': {
                    'auto_save': True,
                    'cache_results': True,
                    'max_history_items': 50,
                    'notification_preferences': {
                        'email_notifications': True,
                        'browser_notifications': False
                    }
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('settings', response.data)
            self.assertTrue(response.data['settings']['auto_save'])
            self.assertTrue(response.data['settings']['cache_results'])
            self.assertIn('notification_preferences', response.data['settings'])
    
    def test_session_creation_with_audit_logging(self):
        """Test session creation with comprehensive audit logging"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_audit',
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
            
            # Verify audit logging
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            self.assertEqual(call_args[1]['action'], 'session_create')
            self.assertEqual(call_args[1]['resource'], 'analysis_session')
            self.assertEqual(call_args[1]['success'], True)
            self.assertIn('dataset_id', call_args[1]['additional_details'])
    
    def test_session_creation_with_error_handling(self):
        """Test session creation with comprehensive error handling"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': False,
                'error': 'Dataset not accessible',
                'error_code': 'DATASET_ACCESS_DENIED',
                'error_details': {
                    'dataset_id': self.dataset_id,
                    'user_id': self.user.id,
                    'reason': 'Dataset belongs to another user',
                    'suggestion': 'Check dataset ownership or request access'
                }
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Error Test Session'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn('error', response.data)
            self.assertIn('error_code', response.data)
            self.assertIn('error_details', response.data)
            self.assertEqual(response.data['error_code'], 'DATASET_ACCESS_DENIED')
    
    def test_session_creation_with_concurrent_sessions(self):
        """Test session creation with concurrent session handling"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_concurrent',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'concurrent_info': {
                    'active_sessions_count': 3,
                    'max_concurrent_sessions': 5,
                    'session_priority': 'normal',
                    'resource_allocation': {
                        'memory_limit_mb': 512,
                        'cpu_limit_percent': 25
                    }
                }
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Concurrent Session'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('concurrent_info', response.data)
            self.assertIn('active_sessions_count', response.data['concurrent_info'])
            self.assertIn('resource_allocation', response.data['concurrent_info'])
    
    def test_session_creation_with_dataset_validation(self):
        """Test session creation with dataset validation"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_validated',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'dataset_validation': {
                    'is_valid': True,
                    'validation_checks': [
                        'File format supported',
                        'Data integrity verified',
                        'Column types detected',
                        'No security threats detected'
                    ],
                    'data_quality_score': 0.95,
                    'recommendations': [
                        'Consider data cleaning for missing values',
                        'Age column has some outliers'
                    ]
                }
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Validated Session'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('dataset_validation', response.data)
            self.assertTrue(response.data['dataset_validation']['is_valid'])
            self.assertIn('validation_checks', response.data['dataset_validation'])
            self.assertIn('recommendations', response.data['dataset_validation'])
    
    def test_session_creation_with_tool_compatibility(self):
        """Test session creation with tool compatibility analysis"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_tools',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'tool_compatibility': {
                    'compatible_tools': [
                        {
                            'tool_id': 'descriptive_stats',
                            'compatibility_score': 1.0,
                            'required_columns': ['numeric'],
                            'available_columns': ['age', 'salary']
                        },
                        {
                            'tool_id': 'correlation_matrix',
                            'compatibility_score': 0.9,
                            'required_columns': ['numeric'],
                            'available_columns': ['age', 'salary']
                        }
                    ],
                    'incompatible_tools': [
                        {
                            'tool_id': 'survival_analysis',
                            'reason': 'Missing time-to-event column',
                            'suggestion': 'Add time column for survival analysis'
                        }
                    ],
                    'recommended_tools': [
                        'descriptive_stats',
                        'correlation_matrix',
                        'regression_analysis'
                    ]
                }
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Tool Compatibility Session'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('tool_compatibility', response.data)
            self.assertIn('compatible_tools', response.data['tool_compatibility'])
            self.assertIn('recommended_tools', response.data['tool_compatibility'])
            self.assertEqual(len(response.data['tool_compatibility']['compatible_tools']), 2)
    
    def test_session_creation_workflow_integration(self):
        """Test complete session creation workflow integration"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_integration',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'workflow_status': {
                    'dataset_loaded': True,
                    'session_created': True,
                    'history_loaded': True,
                    'tools_analyzed': True,
                    'cache_initialized': True,
                    'audit_logged': True,
                    'user_notified': True
                },
                'session_summary': {
                    'total_analyses_available': 15,
                    'recommended_first_analysis': 'descriptive_stats',
                    'estimated_analysis_time': '2-5 minutes',
                    'complexity_level': 'beginner'
                }
            }
        
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
            with patch('analytics.services.notification_service.NotificationService.send_session_created') as mock_notify:
                response = self.client.post('/api/sessions/', {
                    'dataset_id': self.dataset_id,
                    'session_name': 'Integration Test Session'
                }, format='json')
                
                # Verify complete workflow
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertIn('workflow_status', response.data)
                self.assertTrue(response.data['workflow_status']['dataset_loaded'])
                self.assertTrue(response.data['workflow_status']['session_created'])
                self.assertTrue(response.data['workflow_status']['tools_analyzed'])
                
                # Verify audit logging
                mock_audit.assert_called_once()
                
                # Verify notification
                mock_notify.assert_called_once()
    
    def test_session_creation_with_user_preferences(self):
        """Test session creation with user preferences integration"""
        with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create:
            mock_create.return_value = {
                'success': True,
                'session_id': 'sess_preferences',
                'dataset_id': self.dataset_id,
                'dataset_name': self.dataset_name,
                'created_at': '2025-09-23T15:00:00Z',
                'status': 'active',
                'user_preferences': {
                    'default_analysis_tools': ['descriptive_stats', 'correlation_matrix'],
                    'preferred_chart_types': ['bar', 'scatter', 'heatmap'],
                    'analysis_depth': 'comprehensive',
                    'auto_save_interval': 300,  # 5 minutes
                    'notification_frequency': 'on_completion'
                },
                'personalized_recommendations': [
                    'Based on your history, try regression analysis',
                    'Your datasets often benefit from outlier detection',
                    'Consider time series analysis for temporal data'
                ]
            }
            
            response = self.client.post('/api/sessions/', {
                'dataset_id': self.dataset_id,
                'session_name': 'Preferences Session'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('user_preferences', response.data)
            self.assertIn('personalized_recommendations', response.data)
            self.assertIn('default_analysis_tools', response.data['user_preferences'])
            self.assertEqual(len(response.data['personalized_recommendations']), 3)
