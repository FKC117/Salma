"""
UI Update Performance Tests

This module contains performance tests for UI update operations,
ensuring they meet the <1s target requirement.
"""

import time
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from analytics.models import Dataset, AnalysisSession, User

User = get_user_model()


class UIUpdatePerformanceTest(TestCase):
    """Test UI update performance requirements"""
    
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
    
    def test_dashboard_loading_performance(self):
        """Test dashboard loading performance (<1s)"""
        start_time = time.time()
        
        response = self.client.get('/')
        
        end_time = time.time()
        loading_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(loading_time, 1.0, f"Dashboard loading took {loading_time:.3f}s, should be <1s")
    
    def test_upload_form_loading_performance(self):
        """Test upload form loading performance (<1s)"""
        start_time = time.time()
        
        response = self.client.get('/upload-form/')
        
        end_time = time.time()
        loading_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(loading_time, 1.0, f"Upload form loading took {loading_time:.3f}s, should be <1s")
    
    def test_file_upload_ui_update_performance(self):
        """Test file upload UI update performance (<1s)"""
        csv_content = "name,age\nJohn,25\nJane,30"
        uploaded_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        start_time = time.time()
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'dataset_name': 'test_dataset'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(update_time, 1.0, f"File upload UI update took {update_time:.3f}s, should be <1s")
    
    def test_analysis_execution_ui_update_performance(self):
        """Test analysis execution UI update performance (<1s)"""
        start_time = time.time()
        
        response = self.client.post('/analysis/execute/', {
            'tool_name': 'descriptive_statistics',
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'parameters': json.dumps({'column': 'age'})
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertIn(response.status_code, [200, 201, 400])
        self.assertLess(update_time, 1.0, f"Analysis execution UI update took {update_time:.3f}s, should be <1s")
    
    def test_chat_message_ui_update_performance(self):
        """Test chat message UI update performance (<1s)"""
        start_time = time.time()
        
        response = self.client.post('/chat/messages/', {
            'message': 'Hello, analyze my data',
            'session_id': self.session.id
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertIn(response.status_code, [200, 201, 400])
        self.assertLess(update_time, 1.0, f"Chat message UI update took {update_time:.3f}s, should be <1s")
    
    def test_agent_run_ui_update_performance(self):
        """Test agent run UI update performance (<1s)"""
        start_time = time.time()
        
        response = self.client.post('/agent/run/', {
            'dataset_id': self.dataset.id,
            'session_id': self.session.id,
            'analysis_goal': 'Test analysis'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertIn(response.status_code, [200, 201, 400])
        self.assertLess(update_time, 1.0, f"Agent run UI update took {update_time:.3f}s, should be <1s")
    
    def test_tools_refresh_ui_update_performance(self):
        """Test tools refresh UI update performance (<1s)"""
        start_time = time.time()
        
        response = self.client.get('/tools/list/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(update_time, 1.0, f"Tools refresh UI update took {update_time:.3f}s, should be <1s")
    
    def test_audit_trail_ui_update_performance(self):
        """Test audit trail UI update performance (<1s)"""
        start_time = time.time()
        
        response = self.client.get('/audit/trail/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(update_time, 1.0, f"Audit trail UI update took {update_time:.3f}s, should be <1s")
    
    def test_session_creation_ui_update_performance(self):
        """Test session creation UI update performance (<1s)"""
        start_time = time.time()
        
        response = self.client.post('/sessions/create/', {
            'name': 'new_session',
            'dataset_id': self.dataset.id,
            'description': 'Test session'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertIn(response.status_code, [200, 201, 400])
        self.assertLess(update_time, 1.0, f"Session creation UI update took {update_time:.3f}s, should be <1s")
    
    def test_rag_operations_ui_update_performance(self):
        """Test RAG operations UI update performance (<1s)"""
        # Test RAG upsert
        start_time = time.time()
        
        response = self.client.post('/rag/upsert/', {
            'content': 'Test content',
            'metadata': json.dumps({'type': 'test'})
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertIn(response.status_code, [200, 201, 400])
        self.assertLess(update_time, 1.0, f"RAG upsert UI update took {update_time:.3f}s, should be <1s")
        
        # Test RAG search
        start_time = time.time()
        
        response = self.client.get('/rag/search/', {
            'query': 'test query'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(update_time, 1.0, f"RAG search UI update took {update_time:.3f}s, should be <1s")
    
    def test_three_panel_layout_ui_performance(self):
        """Test three-panel layout UI performance (<1s)"""
        start_time = time.time()
        
        response = self.client.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        loading_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(loading_time, 1.0, f"Three-panel layout loading took {loading_time:.3f}s, should be <1s")
        
        # Verify all panels are present
        self.assertContains(response, 'tools-panel')
        self.assertContains(response, 'dashboard-panel')
        self.assertContains(response, 'chat-panel')
    
    def test_dynamic_content_updates_performance(self):
        """Test dynamic content updates performance (<1s)"""
        # Test multiple UI updates in sequence
        updates = [
            ('/tools/list/', 'GET'),
            ('/audit/trail/', 'GET'),
            ('/sessions/create/', 'POST', {'name': 'test', 'dataset_id': self.dataset.id})
        ]
        
        for update in updates:
            start_time = time.time()
            
            if update[1] == 'GET':
                response = self.client.get(update[0], HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            else:
                response = self.client.post(update[0], update[2], HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            
            end_time = time.time()
            update_time = end_time - start_time
            
            self.assertLess(update_time, 1.0, f"Dynamic content update {update[0]} took {update_time:.3f}s, should be <1s")
    
    def test_ui_error_handling_performance(self):
        """Test UI error handling performance (<1s)"""
        # Test with invalid data
        start_time = time.time()
        
        response = self.client.post('/upload/', {
            'file': 'invalid',
            'dataset_name': ''
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        error_time = end_time - start_time
        
        # Error handling should also be fast
        self.assertLess(error_time, 1.0, f"UI error handling took {error_time:.3f}s, should be <1s")
    
    def test_ui_memory_usage(self):
        """Test UI memory usage efficiency"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform multiple UI operations
        for i in range(10):
            response = self.client.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 20MB)
        self.assertLess(memory_increase, 20 * 1024 * 1024, 
                       f"UI memory increase {memory_increase / 1024 / 1024:.1f}MB is too high")
    
    def test_ui_concurrent_updates_performance(self):
        """Test UI concurrent updates performance"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def ui_update(endpoint, method='GET', data=None):
            start_time = time.time()
            
            if method == 'GET':
                response = self.client.get(endpoint, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            else:
                response = self.client.post(endpoint, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            
            end_time = time.time()
            update_time = end_time - start_time
            
            results.put({
                'endpoint': endpoint,
                'status_code': response.status_code,
                'update_time': update_time
            })
        
        # Run multiple UI updates concurrently
        threads = []
        endpoints = [
            ('/tools/list/', 'GET'),
            ('/audit/trail/', 'GET'),
            ('/sessions/create/', 'POST', {'name': 'concurrent_test', 'dataset_id': self.dataset.id})
        ]
        
        for endpoint_info in endpoints:
            if len(endpoint_info) == 2:
                thread = threading.Thread(target=ui_update, args=(endpoint_info[0], endpoint_info[1]))
            else:
                thread = threading.Thread(target=ui_update, args=(endpoint_info[0], endpoint_info[1], endpoint_info[2]))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        while not results.empty():
            result = results.get()
            self.assertLess(result['update_time'], 1.0, 
                          f"Concurrent UI update {result['endpoint']} took {result['update_time']:.3f}s, should be <1s")
    
    def test_ui_loading_indicators_performance(self):
        """Test UI loading indicators performance"""
        # Test that loading indicators appear quickly
        start_time = time.time()
        
        response = self.client.get('/tools/list/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        loading_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(loading_time, 1.0, f"Loading indicators took {loading_time:.3f}s, should be <1s")
        
        # Response should include loading-related content
        self.assertContains(response, 'tools')
    
    def test_ui_form_validation_performance(self):
        """Test UI form validation performance"""
        start_time = time.time()
        
        response = self.client.post('/upload/', {
            'file': '',
            'dataset_name': ''
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        # Form validation should be fast
        self.assertLess(validation_time, 0.5, f"Form validation took {validation_time:.3f}s, should be <500ms")
    
    def test_ui_partial_updates_performance(self):
        """Test UI partial updates performance"""
        # Test that partial updates are fast
        start_time = time.time()
        
        response = self.client.get('/tools/list/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        end_time = time.time()
        update_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(update_time, 1.0, f"Partial update took {update_time:.3f}s, should be <1s")
        
        # Should return only partial content, not full page
        self.assertNotContains(response, '<html>')
        self.assertNotContains(response, '<head>')
