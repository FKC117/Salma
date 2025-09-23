"""
Contract Test: POST /api/chat/messages/ (T016)
Tests the chat messages API endpoint according to the API schema
"""

import pytest
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestChatMessagesContract(TestCase):
    """Contract tests for POST /api/chat/messages/ endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock session
        self.session_id = 'sess_123456789'
        self.dataset_id = 1
    
    def test_send_chat_message_success(self):
        """Test successful chat message sending"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'message_id': 'msg_123456789',
                'user_message': 'What does the age distribution look like?',
                'assistant_response': 'Based on the analysis, the age distribution shows a normal distribution with a mean of 30 years and standard deviation of 5 years.',
                'tokens_used': 45,
                'cost': 0.000225,
                'created_at': '2025-09-23T15:00:00Z',
                'context_used': True
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'What does the age distribution look like?',
                'include_context': True
            }, format='json')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('message_id', response.data)
            self.assertIn('user_message', response.data)
            self.assertIn('assistant_response', response.data)
            self.assertIn('tokens_used', response.data)
            self.assertIn('cost', response.data)
            self.assertIn('created_at', response.data)
            self.assertIn('context_used', response.data)
            
            # Verify data types
            self.assertIsInstance(response.data['message_id'], str)
            self.assertIsInstance(response.data['user_message'], str)
            self.assertIsInstance(response.data['assistant_response'], str)
            self.assertIsInstance(response.data['tokens_used'], int)
            self.assertIsInstance(response.data['cost'], float)
            self.assertIsInstance(response.data['created_at'], str)
            self.assertIsInstance(response.data['context_used'], bool)
    
    def test_send_chat_message_with_analysis_context(self):
        """Test chat message with analysis results context"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'message_id': 'msg_with_context',
                'user_message': 'Can you explain these results?',
                'assistant_response': 'The correlation analysis shows a strong positive relationship between age and salary (r=0.75). This suggests that older employees tend to have higher salaries.',
                'tokens_used': 67,
                'cost': 0.000335,
                'created_at': '2025-09-23T15:00:00Z',
                'context_used': True,
                'analysis_context': {
                    'analysis_id': 1,
                    'tool_name': 'correlation_matrix',
                    'results_summary': 'Strong positive correlation found'
                }
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'Can you explain these results?',
                'include_context': True,
                'analysis_context': {
                    'analysis_id': 1,
                    'tool_name': 'correlation_matrix'
                }
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('analysis_context', response.data)
            self.assertIn('analysis_id', response.data['analysis_context'])
            self.assertIn('tool_name', response.data['analysis_context'])
    
    def test_send_chat_message_with_images(self):
        """Test chat message with image context"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'message_id': 'msg_with_images',
                'user_message': 'What do you see in this chart?',
                'assistant_response': 'The histogram shows a normal distribution of ages with most employees between 25-35 years old.',
                'tokens_used': 52,
                'cost': 0.000260,
                'created_at': '2025-09-23T15:00:00Z',
                'context_used': True,
                'image_context': [
                    {
                        'image_url': '/media/charts/age_histogram.png',
                        'image_data': 'base64_encoded_image_data',
                        'description': 'Age distribution histogram'
                    }
                ]
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'What do you see in this chart?',
                'include_context': True,
                'image_context': [
                    {
                        'image_url': '/media/charts/age_histogram.png',
                        'image_data': 'base64_encoded_image_data'
                    }
                ]
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('image_context', response.data)
            self.assertIsInstance(response.data['image_context'], list)
            self.assertEqual(len(response.data['image_context']), 1)
    
    def test_send_chat_message_missing_session_id(self):
        """Test chat message without session_id"""
        response = self.client.post('/api/chat/messages/', {
            'message': 'Hello, can you help me?'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('session_id is required', response.data['error'])
    
    def test_send_chat_message_missing_message(self):
        """Test chat message without message content"""
        response = self.client.post('/api/chat/messages/', {
            'session_id': self.session_id
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('message is required', response.data['error'])
    
    def test_send_chat_message_empty_message(self):
        """Test chat message with empty message content"""
        response = self.client.post('/api/chat/messages/', {
            'session_id': self.session_id,
            'message': ''
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Message cannot be empty', response.data['error'])
    
    def test_send_chat_message_invalid_session(self):
        """Test chat message with invalid session_id"""
        response = self.client.post('/api/chat/messages/', {
            'session_id': 'invalid_session',
            'message': 'Hello, can you help me?'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('Session not found', response.data['error'])
    
    def test_send_chat_message_unauthenticated(self):
        """Test chat message without authentication"""
        client = APIClient()  # No authentication
        
        response = client.post('/api/chat/messages/', {
            'session_id': self.session_id,
            'message': 'Hello, can you help me?'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_send_chat_message_unauthorized_session(self):
        """Test chat message with session user doesn't own"""
        with patch('analytics.services.llm_processor.LLMProcessor.check_session_access') as mock_check:
            mock_check.return_value = False
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'Hello, can you help me?'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn('error', response.data)
            self.assertIn('Access denied', response.data['error'])
    
    def test_send_chat_message_token_limit_exceeded(self):
        """Test chat message when user token limit is exceeded"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': False,
                'error': 'Token limit exceeded',
                'tokens_used': 0,
                'cost': 0.0
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'Hello, can you help me?'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertIn('error', response.data)
            self.assertIn('Token limit exceeded', response.data['error'])
    
    def test_send_chat_message_llm_error(self):
        """Test chat message when LLM processing fails"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': False,
                'error': 'LLM processing failed',
                'tokens_used': 0,
                'cost': 0.0
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'Hello, can you help me?'
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
            self.assertIn('LLM processing failed', response.data['error'])
    
    def test_send_chat_message_with_context_caching(self):
        """Test chat message with context caching"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'message_id': 'msg_cached_context',
                'user_message': 'What does this mean?',
                'assistant_response': 'Based on the previous analysis, this indicates a strong correlation.',
                'tokens_used': 23,
                'cost': 0.000115,
                'created_at': '2025-09-23T15:00:00Z',
                'context_used': True,
                'context_cached': True,
                'context_size': 10  # Last 10 messages
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'What does this mean?',
                'include_context': True
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('context_cached', response.data)
            self.assertTrue(response.data['context_cached'])
            self.assertIn('context_size', response.data)
            self.assertEqual(response.data['context_size'], 10)
    
    def test_send_chat_message_response_schema(self):
        """Test that response matches the expected schema"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'message_id': 'msg_schema_test',
                'user_message': 'Test message',
                'assistant_response': 'Test response',
                'tokens_used': 15,
                'cost': 0.000075,
                'created_at': '2025-09-23T15:00:00Z',
                'context_used': False,
                'user_id': self.user.id,
                'session_id': self.session_id
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'Test message'
            }, format='json')
            
            # Verify all required fields are present
            required_fields = [
                'message_id', 'user_message', 'assistant_response', 
                'tokens_used', 'cost', 'created_at', 'context_used',
                'user_id', 'session_id'
            ]
            
            for field in required_fields:
                self.assertIn(field, response.data, f"Missing required field: {field}")
            
            # Verify field types
            self.assertIsInstance(response.data['message_id'], str)
            self.assertIsInstance(response.data['user_message'], str)
            self.assertIsInstance(response.data['assistant_response'], str)
            self.assertIsInstance(response.data['tokens_used'], int)
            self.assertIsInstance(response.data['cost'], float)
            self.assertIsInstance(response.data['created_at'], str)
            self.assertIsInstance(response.data['context_used'], bool)
            self.assertIsInstance(response.data['user_id'], int)
            self.assertIsInstance(response.data['session_id'], str)
    
    def test_send_chat_message_audit_logging(self):
        """Test that chat message is properly logged for audit"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'message_id': 'msg_audit_test',
                'user_message': 'Audit test message',
                'assistant_response': 'Audit test response',
                'tokens_used': 20,
                'cost': 0.000100,
                'created_at': '2025-09-23T15:00:00Z',
                'context_used': False
            }
            
            with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
                response = self.client.post('/api/chat/messages/', {
                    'session_id': self.session_id,
                    'message': 'Audit test message'
                }, format='json')
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                self.assertEqual(call_args[1]['action'], 'chat_message')
                self.assertEqual(call_args[1]['resource'], 'chat_message')
                self.assertEqual(call_args[1]['success'], True)
    
    def test_send_chat_message_with_batch_processing(self):
        """Test chat message with batch LLM processing"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'message_id': 'msg_batch_test',
                'user_message': 'Batch test message',
                'assistant_response': 'Batch processed response',
                'tokens_used': 25,
                'cost': 0.000125,
                'created_at': '2025-09-23T15:00:00Z',
                'context_used': True,
                'batch_processed': True,
                'batch_size': 3
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'Batch test message',
                'include_context': True,
                'batch_process': True
            }, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('batch_processed', response.data)
            self.assertTrue(response.data['batch_processed'])
            self.assertIn('batch_size', response.data)
            self.assertEqual(response.data['batch_size'], 3)
