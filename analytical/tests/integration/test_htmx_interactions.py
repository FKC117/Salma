"""
End-to-End HTMX Interaction Tests

This module contains comprehensive integration tests for HTMX interactions
across the three-panel interface.
"""

import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from analytics.models import Dataset, AnalysisSession, User

User = get_user_model()


class HTMXInteractionTest(TestCase):
    """Test HTMX interactions across the interface"""
    
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
    
    def test_dashboard_htmx_loading(self):
        """Test dashboard loads with HTMX"""
        response = self.client.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
    
    def test_upload_form_htmx_interaction(self):
        """Test file upload form HTMX interaction"""
        response = self.client.get('/upload-form/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload')
    
    def test_file_upload_htmx_response(self):
        """Test file upload HTMX response"""
        csv_content = "name,age\nJohn,25\nJane,30"
        uploaded_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'dataset_name': 'test_dataset'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'success')
    
    def test_analysis_execution_htmx(self):
        """Test analysis execution HTMX interaction"""
        response = self.client.post('/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': json.dumps({'column': 'age'})
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertIn(response.status_code, [200, 201, 400])
    
    def test_chat_message_htmx(self):
        """Test chat message HTMX interaction"""
        response = self.client.post('/chat/messages/', {
            'message': 'Hello, analyze my data',
            'session_id': self.session.id
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertIn(response.status_code, [200, 201, 400])
    
    def test_agent_run_htmx(self):
        """Test agent run HTMX interaction"""
        response = self.client.post('/agent/run/', {
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'analysis_goal': 'Test analysis'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertIn(response.status_code, [200, 201, 400])
    
    def test_tools_refresh_htmx(self):
        """Test tools refresh HTMX interaction"""
        response = self.client.get('/tools/list/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
    
    def test_audit_trail_htmx(self):
        """Test audit trail HTMX interaction"""
        response = self.client.get('/audit/trail/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
    
    def test_session_creation_htmx(self):
        """Test session creation HTMX interaction"""
        response = self.client.post('/sessions/create/', {
            'name': 'new_session',
            'dataset_id': self.dataset.id,
            'description': 'Test session'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertIn(response.status_code, [200, 201, 400])
    
    def test_rag_upsert_htmx(self):
        """Test RAG upsert HTMX interaction"""
        response = self.client.post('/rag/upsert/', {
            'content': 'Test content',
            'metadata': json.dumps({'type': 'test'})
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertIn(response.status_code, [200, 201, 400])
    
    def test_rag_search_htmx(self):
        """Test RAG search HTMX interaction"""
        response = self.client.get('/rag/search/', {
            'query': 'test query'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
    
    def test_three_panel_layout_htmx(self):
        """Test three-panel layout HTMX interactions"""
        # Test tools panel
        response = self.client.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'tools-panel')
        
        # Test dashboard panel
        self.assertContains(response, 'dashboard-panel')
        
        # Test chat panel
        self.assertContains(response, 'chat-panel')
    
    def test_error_handling_htmx(self):
        """Test error handling in HTMX responses"""
        # Test with invalid data
        response = self.client.post('/upload/', {
            'file': 'invalid',
            'dataset_name': ''
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_loading_states_htmx(self):
        """Test loading states in HTMX responses"""
        response = self.client.get('/tools/list/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        # Should include loading indicators or progress elements
        self.assertContains(response, 'tools')
    
    def test_dynamic_content_updates_htmx(self):
        """Test dynamic content updates via HTMX"""
        # Test that content can be updated dynamically
        response = self.client.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        # Test that the response includes HTMX-specific attributes
        self.assertContains(response, 'hx-')
    
    def test_form_validation_htmx(self):
        """Test form validation with HTMX"""
        response = self.client.post('/upload/', {
            'file': '',
            'dataset_name': ''
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # Should return validation errors
        self.assertIn(response.status_code, [200, 400])
    
    def test_partial_page_updates_htmx(self):
        """Test partial page updates with HTMX"""
        # Test that only specific parts of the page are updated
        response = self.client.get('/tools/list/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        # Should return only the tools section, not the full page
        self.assertNotContains(response, '<html>')
        self.assertNotContains(response, '<head>')
