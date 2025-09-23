"""
Contract Test: GET /api/audit/trail/ (T019)
Tests the audit trail API endpoint according to the API schema
"""

import pytest
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestAuditTrailContract(TestCase):
    """Contract tests for GET /api/audit/trail/ endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock audit trail data
        self.audit_records = [
            {
                'id': 1,
                'user_id': self.user.id,
                'action_type': 'file_upload',
                'action_category': 'data_management',
                'resource_type': 'dataset',
                'resource_id': 1,
                'resource_name': 'test_dataset.csv',
                'action_description': 'User uploaded dataset file',
                'ip_address': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'correlation_id': 'corr_123456789',
                'success': True,
                'execution_time_ms': 1500,
                'data_changed': True,
                'sensitive_data_accessed': False,
                'compliance_flags': ['gdpr'],
                'created_at': '2025-09-23T15:00:00Z'
            },
            {
                'id': 2,
                'user_id': self.user.id,
                'action_type': 'analysis_execute',
                'action_category': 'analysis',
                'resource_type': 'analysis_result',
                'resource_id': 1,
                'resource_name': 'descriptive_stats_analysis',
                'action_description': 'User executed descriptive statistics analysis',
                'ip_address': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'correlation_id': 'corr_987654321',
                'success': True,
                'execution_time_ms': 2500,
                'data_changed': True,
                'sensitive_data_accessed': True,
                'compliance_flags': ['gdpr', 'hipaa'],
                'created_at': '2025-09-23T15:05:00Z'
            },
            {
                'id': 3,
                'user_id': self.user.id,
                'action_type': 'chat_message',
                'action_category': 'analysis',
                'resource_type': 'chat_message',
                'resource_id': 1,
                'resource_name': 'chat_message_1',
                'action_description': 'User sent chat message to AI assistant',
                'ip_address': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'correlation_id': 'corr_456789123',
                'success': True,
                'execution_time_ms': 800,
                'data_changed': False,
                'sensitive_data_accessed': False,
                'compliance_flags': [],
                'created_at': '2025-09-23T15:10:00Z'
            }
        ]
    
    def test_get_audit_trail_success(self):
        """Test successful audit trail retrieval"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            mock_get.return_value = {
                'success': True,
                'records': self.audit_records,
                'total_count': 3,
                'page': 1,
                'page_size': 20,
                'total_pages': 1
            }
            
            response = self.client.get('/api/audit/trail/')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('records', response.data)
            self.assertIn('total_count', response.data)
            self.assertIn('page', response.data)
            self.assertIn('page_size', response.data)
            self.assertIn('total_pages', response.data)
            
            # Verify data types
            self.assertIsInstance(response.data['records'], list)
            self.assertIsInstance(response.data['total_count'], int)
            self.assertIsInstance(response.data['page'], int)
            self.assertIsInstance(response.data['page_size'], int)
            self.assertIsInstance(response.data['total_pages'], int)
            
            # Verify record structure
            record = response.data['records'][0]
            required_fields = [
                'id', 'user_id', 'action_type', 'action_category', 'resource_type',
                'resource_id', 'resource_name', 'action_description', 'ip_address',
                'user_agent', 'correlation_id', 'success', 'execution_time_ms',
                'data_changed', 'sensitive_data_accessed', 'compliance_flags', 'created_at'
            ]
            
            for field in required_fields:
                self.assertIn(field, record, f"Missing required field: {field}")
    
    def test_get_audit_trail_with_filters(self):
        """Test audit trail retrieval with filters"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            filtered_records = [self.audit_records[0]]  # Only file_upload
            mock_get.return_value = {
                'success': True,
                'records': filtered_records,
                'total_count': 1,
                'page': 1,
                'page_size': 20,
                'total_pages': 1
            }
            
            response = self.client.get('/api/audit/trail/', {
                'action_type': 'file_upload',
                'action_category': 'data_management',
                'success': 'true',
                'start_date': '2025-09-23T00:00:00Z',
                'end_date': '2025-09-23T23:59:59Z'
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['records']), 1)
            self.assertEqual(response.data['records'][0]['action_type'], 'file_upload')
    
    def test_get_audit_trail_with_pagination(self):
        """Test audit trail retrieval with pagination"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            mock_get.return_value = {
                'success': True,
                'records': self.audit_records[:2],  # First 2 records
                'total_count': 3,
                'page': 1,
                'page_size': 2,
                'total_pages': 2
            }
            
            response = self.client.get('/api/audit/trail/', {
                'page': 1,
                'page_size': 2
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['records']), 2)
            self.assertEqual(response.data['page'], 1)
            self.assertEqual(response.data['page_size'], 2)
            self.assertEqual(response.data['total_pages'], 2)
    
    def test_get_audit_trail_by_user(self):
        """Test audit trail retrieval filtered by user"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            mock_get.return_value = {
                'success': True,
                'records': self.audit_records,
                'total_count': 3,
                'page': 1,
                'page_size': 20,
                'total_pages': 1
            }
            
            response = self.client.get('/api/audit/trail/', {
                'user_id': self.user.id
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['records']), 3)
            # All records should belong to the same user
            for record in response.data['records']:
                self.assertEqual(record['user_id'], self.user.id)
    
    def test_get_audit_trail_by_correlation_id(self):
        """Test audit trail retrieval filtered by correlation ID"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            correlation_records = [self.audit_records[0]]
            mock_get.return_value = {
                'success': True,
                'records': correlation_records,
                'total_count': 1,
                'page': 1,
                'page_size': 20,
                'total_pages': 1
            }
            
            response = self.client.get('/api/audit/trail/', {
                'correlation_id': 'corr_123456789'
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['records']), 1)
            self.assertEqual(response.data['records'][0]['correlation_id'], 'corr_123456789')
    
    def test_get_audit_trail_unauthenticated(self):
        """Test audit trail retrieval without authentication"""
        client = APIClient()  # No authentication
        
        response = client.get('/api/audit/trail/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_audit_trail_unauthorized_user(self):
        """Test audit trail retrieval for user without permission"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.check_access_permission') as mock_check:
            mock_check.return_value = False
            
            response = self.client.get('/api/audit/trail/', {
                'user_id': other_user.id
            })
            
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn('error', response.data)
            self.assertIn('Access denied', response.data['error'])
    
    def test_get_audit_trail_empty_result(self):
        """Test audit trail retrieval with no records"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            mock_get.return_value = {
                'success': True,
                'records': [],
                'total_count': 0,
                'page': 1,
                'page_size': 20,
                'total_pages': 0
            }
            
            response = self.client.get('/api/audit/trail/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['records']), 0)
            self.assertEqual(response.data['total_count'], 0)
    
    def test_get_audit_trail_with_sensitive_data_masking(self):
        """Test audit trail with sensitive data masking"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            masked_records = [
                {
                    'id': 1,
                    'user_id': self.user.id,
                    'action_type': 'file_upload',
                    'action_category': 'data_management',
                    'resource_type': 'dataset',
                    'resource_id': 1,
                    'resource_name': 'test_dataset.csv',
                    'action_description': 'User uploaded dataset file',
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'correlation_id': 'corr_123456789',
                    'success': True,
                    'execution_time_ms': 1500,
                    'data_changed': True,
                    'sensitive_data_accessed': True,
                    'compliance_flags': ['gdpr'],
                    'created_at': '2025-09-23T15:00:00Z',
                    'before_snapshot': '***MASKED***',
                    'after_snapshot': '***MASKED***'
                }
            ]
            
            mock_get.return_value = {
                'success': True,
                'records': masked_records,
                'total_count': 1,
                'page': 1,
                'page_size': 20,
                'total_pages': 1
            }
            
            response = self.client.get('/api/audit/trail/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            record = response.data['records'][0]
            self.assertIn('before_snapshot', record)
            self.assertIn('after_snapshot', record)
            self.assertEqual(record['before_snapshot'], '***MASKED***')
            self.assertEqual(record['after_snapshot'], '***MASKED***')
    
    def test_get_audit_trail_response_schema(self):
        """Test that response matches the expected schema"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            mock_get.return_value = {
                'success': True,
                'records': self.audit_records,
                'total_count': 3,
                'page': 1,
                'page_size': 20,
                'total_pages': 1
            }
            
            response = self.client.get('/api/audit/trail/')
            
            # Verify all required fields are present
            required_fields = ['records', 'total_count', 'page', 'page_size', 'total_pages']
            
            for field in required_fields:
                self.assertIn(field, response.data, f"Missing required field: {field}")
            
            # Verify field types
            self.assertIsInstance(response.data['records'], list)
            self.assertIsInstance(response.data['total_count'], int)
            self.assertIsInstance(response.data['page'], int)
            self.assertIsInstance(response.data['page_size'], int)
            self.assertIsInstance(response.data['total_pages'], int)
            
            # Verify record has all required fields
            record = response.data['records'][0]
            self.assertIsInstance(record['id'], int)
            self.assertIsInstance(record['user_id'], int)
            self.assertIsInstance(record['action_type'], str)
            self.assertIsInstance(record['action_category'], str)
            self.assertIsInstance(record['resource_type'], str)
            self.assertIsInstance(record['resource_id'], int)
            self.assertIsInstance(record['resource_name'], str)
            self.assertIsInstance(record['action_description'], str)
            self.assertIsInstance(record['ip_address'], str)
            self.assertIsInstance(record['user_agent'], str)
            self.assertIsInstance(record['correlation_id'], str)
            self.assertIsInstance(record['success'], bool)
            self.assertIsInstance(record['execution_time_ms'], int)
            self.assertIsInstance(record['data_changed'], bool)
            self.assertIsInstance(record['sensitive_data_accessed'], bool)
            self.assertIsInstance(record['compliance_flags'], list)
            self.assertIsInstance(record['created_at'], str)
    
    def test_get_audit_trail_audit_logging(self):
        """Test that audit trail access is properly logged"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            mock_get.return_value = {
                'success': True,
                'records': self.audit_records,
                'total_count': 3,
                'page': 1,
                'page_size': 20,
                'total_pages': 1
            }
            
            with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
                response = self.client.get('/api/audit/trail/')
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                self.assertEqual(call_args[1]['action'], 'audit_trail_access')
                self.assertEqual(call_args[1]['resource'], 'audit_trail')
                self.assertEqual(call_args[1]['success'], True)
    
    def test_get_audit_trail_with_compliance_flags(self):
        """Test audit trail retrieval filtered by compliance flags"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            gdpr_records = [self.audit_records[0], self.audit_records[1]]  # Records with GDPR flag
            mock_get.return_value = {
                'success': True,
                'records': gdpr_records,
                'total_count': 2,
                'page': 1,
                'page_size': 20,
                'total_pages': 1
            }
            
            response = self.client.get('/api/audit/trail/', {
                'compliance_flags': 'gdpr'
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['records']), 2)
            # All records should have GDPR compliance flag
            for record in response.data['records']:
                self.assertIn('gdpr', record['compliance_flags'])
    
    def test_get_audit_trail_with_error_filter(self):
        """Test audit trail retrieval filtered by error status"""
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.get_audit_trail') as mock_get:
            error_records = [
                {
                    'id': 4,
                    'user_id': self.user.id,
                    'action_type': 'file_upload',
                    'action_category': 'data_management',
                    'resource_type': 'dataset',
                    'resource_id': 2,
                    'resource_name': 'invalid_file.txt',
                    'action_description': 'User attempted to upload invalid file',
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'correlation_id': 'corr_error_test',
                    'success': False,
                    'error_message': 'Unsupported file type',
                    'execution_time_ms': 100,
                    'data_changed': False,
                    'sensitive_data_accessed': False,
                    'compliance_flags': [],
                    'created_at': '2025-09-23T15:15:00Z'
                }
            ]
            
            mock_get.return_value = {
                'success': True,
                'records': error_records,
                'total_count': 1,
                'page': 1,
                'page_size': 20,
                'total_pages': 1
            }
            
            response = self.client.get('/api/audit/trail/', {
                'success': 'false'
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['records']), 1)
            self.assertFalse(response.data['records'][0]['success'])
            self.assertIn('error_message', response.data['records'][0])
