"""
End-to-End Audit Trail Workflow Tests

This module contains comprehensive integration tests for the complete audit trail workflow,
from action logging through retrieval and compliance reporting.
"""

import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import datetime, timedelta

from analytics.models import (
    Dataset, AnalysisSession, AnalysisResult, AuditTrail, User
)

User = get_user_model()


class AuditTrailWorkflowTest(TestCase):
    """Test complete audit trail workflow"""
    
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
        
        # Create test session
        self.session = AnalysisSession.objects.create(
            name='test_session',
            user=self.user,
            primary_dataset=self.dataset,
            is_active=True
        )
    
    def test_file_upload_audit_trail(self):
        """Test audit trail for file upload workflow"""
        csv_content = "name,age\nJohn,25\nJane,30"
        uploaded_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        # Upload file
        response = self.client.post('/api/upload/', {
            'file': uploaded_file,
            'dataset_name': 'test_dataset'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify audit trail entries
        audit_entries = AuditTrail.objects.filter(
            user_id=self.user.id,
            action_type='CREATE',
            resource_type='Dataset'
        )
        self.assertTrue(audit_entries.exists())
        
        # Check audit entry details
        audit_entry = audit_entries.first()
        self.assertEqual(audit_entry.action_type, 'CREATE')
        self.assertEqual(audit_entry.resource_type, 'Dataset')
        self.assertIsNotNone(audit_entry.created_at)
    
    def test_analysis_execution_audit_trail(self):
        """Test audit trail for analysis execution"""
        # Execute analysis
        response = self.client.post('/api/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': {'column': 'age'}
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify audit trail entries
        audit_entries = AuditTrail.objects.filter(
            user_id=self.user.id,
            action_type='EXECUTE',
            resource_type='AnalysisResult'
        )
        self.assertTrue(audit_entries.exists())
    
    def test_session_management_audit_trail(self):
        """Test audit trail for session management"""
        # Create new session
        response = self.client.post('/api/sessions/', {
            'name': 'new_session',
            'dataset_id': self.dataset.id,
            'description': 'Test session'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify audit trail entries
        audit_entries = AuditTrail.objects.filter(
            user_id=self.user.id,
            action_type='CREATE',
            resource_type='AnalysisSession'
        )
        self.assertTrue(audit_entries.exists())
    
    def test_agent_run_audit_trail(self):
        """Test audit trail for agent runs"""
        # Start agent run
        response = self.client.post('/api/agent/run/', {
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'analysis_goal': 'Test analysis'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify audit trail entries
        audit_entries = AuditTrail.objects.filter(
            user_id=self.user.id,
            action_type='CREATE',
            resource_type='AgentRun'
        )
        self.assertTrue(audit_entries.exists())
    
    def test_audit_trail_retrieval(self):
        """Test audit trail retrieval"""
        # Create some audit entries
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='CREATE',
            action_category='data_management',
            resource_type='Dataset',
            resource_id=1,
            resource_name='test_dataset',
            action_description='Dataset created'
        )
        
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='EXECUTE',
            action_category='analysis',
            resource_type='AnalysisResult',
            resource_id=1,
            resource_name='test_analysis',
            action_description='Analysis executed'
        )
        
        # Retrieve audit trail
        response = self.client.get('/api/audit/trail/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['audit_entries']), 2)
    
    def test_audit_trail_filtering(self):
        """Test audit trail filtering"""
        # Create audit entries with different types
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='CREATE',
            action_category='data_management',
            resource_type='Dataset',
            resource_id=1,
            resource_name='dataset1'
        )
        
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='EXECUTE',
            action_category='analysis',
            resource_type='AnalysisResult',
            resource_id=1,
            resource_name='analysis1'
        )
        
        # Filter by action type
        response = self.client.get('/api/audit/trail/?action_type=CREATE')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # All returned entries should be CREATE actions
        for entry in data['audit_entries']:
            self.assertEqual(entry['action_type'], 'CREATE')
    
    def test_audit_trail_pagination(self):
        """Test audit trail pagination"""
        # Create multiple audit entries
        for i in range(25):
            AuditTrail.objects.create(
                user_id=self.user.id,
                action_type='CREATE',
                action_category='data_management',
                resource_type='Dataset',
                resource_id=i,
                resource_name=f'dataset_{i}'
            )
        
        # Test pagination
        response = self.client.get('/api/audit/trail/?page=1&page_size=10')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['audit_entries']), 10)
        self.assertTrue(data['has_next'])
    
    def test_audit_trail_date_range_filtering(self):
        """Test audit trail date range filtering"""
        # Create audit entries with different dates
        now = timezone.now()
        
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='CREATE',
            action_category='data_management',
            resource_type='Dataset',
            resource_id=1,
            resource_name='recent_dataset',
            created_at=now
        )
        
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='CREATE',
            action_category='data_management',
            resource_type='Dataset',
            resource_id=2,
            resource_name='old_dataset',
            created_at=now - timedelta(days=30)
        )
        
        # Filter by date range
        start_date = (now - timedelta(days=7)).isoformat()
        end_date = now.isoformat()
        
        response = self.client.get(f'/api/audit/trail/?start_date={start_date}&end_date={end_date}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Should only return recent entries
        for entry in data['audit_entries']:
            self.assertIn('recent_dataset', entry['resource_name'])
    
    def test_audit_trail_compliance_reporting(self):
        """Test audit trail compliance reporting"""
        # Create various audit entries
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='CREATE',
            action_category='data_management',
            resource_type='Dataset',
            resource_id=1,
            resource_name='dataset1',
            sensitive_data_accessed=True
        )
        
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='VIEW',
            action_category='data_access',
            resource_type='Dataset',
            resource_id=1,
            resource_name='dataset1',
            sensitive_data_accessed=True
        )
        
        # Generate compliance report
        response = self.client.get('/api/audit/compliance/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('sensitive_data_access_count', data)
        self.assertIn('total_actions', data)
    
    def test_audit_trail_error_logging(self):
        """Test audit trail error logging"""
        # Attempt invalid operation
        response = self.client.post('/api/upload/', {
            'file': 'invalid',
            'dataset_name': ''
        })
        
        # Should log error in audit trail
        error_entries = AuditTrail.objects.filter(
            user_id=self.user.id,
            success=False
        )
        self.assertTrue(error_entries.exists())
    
    def test_audit_trail_user_activity_summary(self):
        """Test audit trail user activity summary"""
        # Create various activities
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='CREATE',
            action_category='data_management',
            resource_type='Dataset',
            resource_id=1,
            resource_name='dataset1'
        )
        
        AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='EXECUTE',
            action_category='analysis',
            resource_type='AnalysisResult',
            resource_id=1,
            resource_name='analysis1'
        )
        
        # Get user activity summary
        response = self.client.get(f'/api/audit/user/{self.user.id}/summary/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('total_actions', data)
        self.assertIn('action_breakdown', data)
    
    def test_audit_trail_data_integrity(self):
        """Test audit trail data integrity"""
        # Create audit entry
        audit_entry = AuditTrail.objects.create(
            user_id=self.user.id,
            action_type='CREATE',
            action_category='data_management',
            resource_type='Dataset',
            resource_id=1,
            resource_name='test_dataset',
            action_description='Dataset created',
            before_snapshot={'old_value': None},
            after_snapshot={'new_value': 'test_dataset'}
        )
        
        # Verify data integrity
        self.assertEqual(audit_entry.user_id, self.user.id)
        self.assertEqual(audit_entry.action_type, 'CREATE')
        self.assertEqual(audit_entry.resource_type, 'Dataset')
        self.assertIsNotNone(audit_entry.created_at)
        self.assertTrue(audit_entry.success)
    
    def test_audit_trail_htmx_interface(self):
        """Test audit trail HTMX interface"""
        # Test audit trail page
        response = self.client.get('/audit/trail/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'audit')
    
    def test_audit_trail_performance(self):
        """Test audit trail performance with large dataset"""
        # Create many audit entries
        for i in range(100):
            AuditTrail.objects.create(
                user_id=self.user.id,
                action_type='CREATE',
                action_category='data_management',
                resource_type='Dataset',
                resource_id=i,
                resource_name=f'dataset_{i}'
            )
        
        # Test retrieval performance
        response = self.client.get('/api/audit/trail/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        # Should complete within reasonable time
        self.assertLess(len(data['audit_entries']), 100)  # Pagination should limit results
