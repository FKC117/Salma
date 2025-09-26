"""
Unit Tests for Analytics Models

This module contains comprehensive unit tests for all models in the analytics app,
testing model creation, validation, relationships, methods, and edge cases.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal
import json
from datetime import datetime, timedelta

from analytics.models import (
    User, Dataset, DatasetColumn, AnalysisSession, AnalysisResult,
    ChatMessage, AgentRun, AgentStep, GeneratedImage, AuditTrail, VectorNote
)


class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_creation(self):
        """Test basic user creation"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertFalse(user.is_premium)
        self.assertFalse(user.account_suspended)
        self.assertEqual(user.token_usage_current_month, 0)
        self.assertEqual(user.max_tokens_per_month, 1000000)
        self.assertEqual(user.storage_used_bytes, 0)
        self.assertEqual(user.max_storage_bytes, 262144000)
        self.assertEqual(user.preferred_theme, 'dark')
        self.assertTrue(user.auto_save_analysis)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
        self.assertIsNotNone(user.last_activity)
    
    def test_user_str_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.username} ({user.email})"
        self.assertEqual(str(user), expected)
    
    def test_user_storage_properties(self):
        """Test user storage-related properties"""
        user = User.objects.create_user(**self.user_data)
        
        # Test storage_used_mb property
        user.storage_used_bytes = 1048576  # 1MB
        self.assertEqual(user.storage_used_mb, 1.0)
        
        # Test max_storage_mb property
        self.assertEqual(user.max_storage_mb, 250.0)
        
        # Test storage_usage_percentage
        self.assertEqual(user.storage_usage_percentage, 0.4)  # 1MB / 250MB
    
    def test_user_token_properties(self):
        """Test user token-related properties"""
        user = User.objects.create_user(**self.user_data)
        
        # Test token_usage_percentage
        user.token_usage_current_month = 500000  # 500K tokens
        self.assertEqual(user.token_usage_percentage, 50.0)  # 500K / 1M
    
    def test_user_can_use_tokens(self):
        """Test token usage validation"""
        user = User.objects.create_user(**self.user_data)
        
        # Should be able to use tokens within limit
        self.assertTrue(user.can_use_tokens(100000))
        
        # Should not be able to exceed limit
        user.token_usage_current_month = 900000
        self.assertFalse(user.can_use_tokens(200000))
    
    def test_user_can_upload_file(self):
        """Test file upload validation"""
        user = User.objects.create_user(**self.user_data)
        
        # Should be able to upload file within limit
        self.assertTrue(user.can_upload_file(1000000))  # 1MB
        
        # Should not be able to exceed limit
        user.storage_used_bytes = 262144000  # At the limit (250MB)
        self.assertFalse(user.can_upload_file(1000000))  # Adding 1MB would exceed limit
    
    def test_user_add_token_usage(self):
        """Test adding token usage"""
        user = User.objects.create_user(**self.user_data)
        initial_usage = user.token_usage_current_month
        
        user.add_token_usage(50000)
        self.assertEqual(user.token_usage_current_month, initial_usage + 50000)
    
    def test_user_add_storage_usage(self):
        """Test adding storage usage"""
        user = User.objects.create_user(**self.user_data)
        initial_storage = user.storage_used_bytes
        
        user.add_storage_usage(1000000)
        self.assertEqual(user.storage_used_bytes, initial_storage + 1000000)
    
    def test_user_remove_storage_usage(self):
        """Test removing storage usage"""
        user = User.objects.create_user(**self.user_data)
        user.storage_used_bytes = 1000000
        
        user.remove_storage_usage(500000)
        self.assertEqual(user.storage_used_bytes, 500000)
        
        # Should not go below 0
        user.remove_storage_usage(1000000)
        self.assertEqual(user.storage_used_bytes, 0)
    
    def test_user_reset_monthly_token_usage(self):
        """Test resetting monthly token usage"""
        user = User.objects.create_user(**self.user_data)
        user.token_usage_current_month = 500000
        old_reset_time = user.token_usage_last_reset
        
        user.reset_monthly_token_usage()
        
        self.assertEqual(user.token_usage_current_month, 0)
        self.assertGreater(user.token_usage_last_reset, old_reset_time)
    
    def test_user_update_last_activity(self):
        """Test updating last activity"""
        user = User.objects.create_user(**self.user_data)
        old_activity = user.last_activity
        
        user.update_last_activity()
        
        self.assertGreater(user.last_activity, old_activity)
    
    def test_user_storage_warning_threshold(self):
        """Test storage warning threshold calculation"""
        user = User.objects.create_user(**self.user_data)
        expected_threshold = int(user.max_storage_bytes * 0.8)
        
        self.assertEqual(user.get_storage_warning_threshold(), expected_threshold)
    
    def test_user_should_send_storage_warning(self):
        """Test storage warning logic"""
        user = User.objects.create_user(**self.user_data)
        
        # Should not send warning initially
        self.assertFalse(user.should_send_storage_warning())
        
        # Should send warning when over threshold
        user.storage_used_bytes = user.get_storage_warning_threshold()
        self.assertTrue(user.should_send_storage_warning())
        
        # Should not send warning if already sent
        user.storage_warning_sent = True
        self.assertFalse(user.should_send_storage_warning())
    
    def test_user_get_usage_summary(self):
        """Test usage summary generation"""
        user = User.objects.create_user(**self.user_data)
        user.token_usage_current_month = 500000
        user.storage_used_bytes = 1048576
        
        summary = user.get_usage_summary()
        
        self.assertIn('tokens', summary)
        self.assertIn('storage', summary)
        self.assertIn('account', summary)
        
        self.assertEqual(summary['tokens']['used'], 500000)
        self.assertEqual(summary['tokens']['max'], 1000000)
        self.assertEqual(summary['tokens']['percentage'], 50.0)
        
        self.assertEqual(summary['storage']['used_mb'], 1.0)
        self.assertEqual(summary['storage']['max_mb'], 250.0)


class DatasetModelTest(TestCase):
    """Test cases for Dataset model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.dataset_data = {
            'name': 'Test Dataset',
            'description': 'A test dataset',
            'original_filename': 'test.csv',
            'file_size_bytes': 1048576,
            'file_hash': 'abc123def456',
            'original_format': 'csv',
            'parquet_path': '/media/datasets/test.parquet',
            'parquet_size_bytes': 524288,
            'row_count': 1000,
            'column_count': 10,
            'data_types': {'col1': 'numeric', 'col2': 'categorical'},
            'processing_status': 'completed',
            'data_quality_score': 0.95,
            'completeness_score': 0.90,
            'consistency_score': 0.85,
            'security_scan_passed': True,
            'sanitized': True,
            'user': self.user
        }
    
    def test_dataset_creation(self):
        """Test basic dataset creation"""
        dataset = Dataset.objects.create(**self.dataset_data)
        
        self.assertEqual(dataset.name, 'Test Dataset')
        self.assertEqual(dataset.description, 'A test dataset')
        self.assertEqual(dataset.original_filename, 'test.csv')
        self.assertEqual(dataset.file_size_bytes, 1048576)
        self.assertEqual(dataset.file_hash, 'abc123def456')
        self.assertEqual(dataset.original_format, 'csv')
        self.assertEqual(dataset.parquet_path, '/media/datasets/test.parquet')
        self.assertEqual(dataset.parquet_size_bytes, 524288)
        self.assertEqual(dataset.row_count, 1000)
        self.assertEqual(dataset.column_count, 10)
        self.assertEqual(dataset.data_types, {'col1': 'numeric', 'col2': 'categorical'})
        self.assertEqual(dataset.processing_status, 'completed')
        self.assertEqual(dataset.data_quality_score, 0.95)
        self.assertEqual(dataset.completeness_score, 0.90)
        self.assertEqual(dataset.consistency_score, 0.85)
        self.assertTrue(dataset.security_scan_passed)
        self.assertTrue(dataset.sanitized)
        self.assertEqual(dataset.user, self.user)
        self.assertIsNotNone(dataset.created_at)
        self.assertIsNotNone(dataset.updated_at)
    
    def test_dataset_str_representation(self):
        """Test dataset string representation"""
        dataset = Dataset.objects.create(**self.dataset_data)
        expected = f"{dataset.name} ({dataset.original_filename})"
        self.assertEqual(str(dataset), expected)
    
    def test_dataset_file_size_properties(self):
        """Test dataset file size properties"""
        dataset = Dataset.objects.create(**self.dataset_data)
        
        # Test file_size_mb property
        self.assertEqual(dataset.file_size_mb, 1.0)
        
        # Test parquet_size_mb property
        self.assertEqual(dataset.parquet_size_mb, 0.5)
        
        # Test compression_ratio property
        expected_ratio = dataset.file_size_bytes / dataset.parquet_size_bytes
        self.assertEqual(dataset.compression_ratio, expected_ratio)
    
    def test_dataset_get_column_types_summary(self):
        """Test column types summary generation"""
        dataset = Dataset.objects.create(**self.dataset_data)
        
        summary = dataset.get_column_types_summary()
        
        self.assertIn('numeric', summary)
        self.assertIn('categorical', summary)
        self.assertEqual(summary['numeric'], 1)
        self.assertEqual(summary['categorical'], 1)
    
    def test_dataset_get_processing_summary(self):
        """Test processing summary generation"""
        dataset = Dataset.objects.create(**self.dataset_data)
        
        summary = dataset.get_processing_summary()
        
        self.assertIn('file_info', summary)
        self.assertIn('data_quality', summary)
        self.assertIn('column_types', summary)
        self.assertIn('security', summary)
        
        self.assertEqual(summary['file_info']['original_size_mb'], 1.0)
        self.assertEqual(summary['data_quality']['overall_score'], 0.95)
        self.assertEqual(summary['security']['scan_passed'], True)


class DatasetColumnModelTest(TestCase):
    """Test cases for DatasetColumn model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.dataset = Dataset.objects.create(
            name='Test Dataset',
            original_filename='test.csv',
            file_size_bytes=1048576,
            file_hash='abc123def456',
            original_format='csv',
            parquet_path='/media/datasets/test.parquet',
            row_count=1000,
            column_count=10,
            user=self.user
        )
        
        self.column_data = {
            'name': 'test_column',
            'display_name': 'Test Column',
            'description': 'A test column',
            'detected_type': 'numeric',
            'confirmed_type': 'numeric',
            'confidence_score': 0.95,
            'null_count': 50,
            'null_percentage': 5.0,
            'unique_count': 950,
            'unique_percentage': 95.0,
            'min_value': 0.0,
            'max_value': 100.0,
            'mean_value': 50.0,
            'median_value': 50.0,
            'std_deviation': 25.0,
            'dataset': self.dataset
        }
    
    def test_column_creation(self):
        """Test basic column creation"""
        column = DatasetColumn.objects.create(**self.column_data)
        
        self.assertEqual(column.name, 'test_column')
        self.assertEqual(column.display_name, 'Test Column')
        self.assertEqual(column.description, 'A test column')
        self.assertEqual(column.detected_type, 'numeric')
        self.assertEqual(column.confirmed_type, 'numeric')
        self.assertEqual(column.confidence_score, 0.95)
        self.assertEqual(column.null_count, 50)
        self.assertEqual(column.null_percentage, 5.0)
        self.assertEqual(column.unique_count, 950)
        self.assertEqual(column.unique_percentage, 95.0)
        self.assertEqual(column.min_value, 0.0)
        self.assertEqual(column.max_value, 100.0)
        self.assertEqual(column.mean_value, 50.0)
        self.assertEqual(column.median_value, 50.0)
        self.assertEqual(column.std_deviation, 25.0)
        self.assertEqual(column.dataset, self.dataset)
        self.assertIsNotNone(column.created_at)
        self.assertIsNotNone(column.updated_at)
    
    def test_column_str_representation(self):
        """Test column string representation"""
        column = DatasetColumn.objects.create(**self.column_data)
        expected = f"{column.dataset.name}.{column.name} ({column.get_effective_type()})"
        self.assertEqual(str(column), expected)
    
    def test_column_get_effective_type(self):
        """Test effective type calculation"""
        column = DatasetColumn.objects.create(**self.column_data)
        
        # Should return confirmed_type if available
        self.assertEqual(column.get_effective_type(), 'numeric')
        
        # Should return detected_type if confirmed_type is None
        column.confirmed_type = None
        self.assertEqual(column.get_effective_type(), 'numeric')
    
    def test_column_type_properties(self):
        """Test column type properties"""
        column = DatasetColumn.objects.create(**self.column_data)
        
        # Test type properties
        self.assertTrue(column.is_numeric)
        self.assertFalse(column.is_categorical)
        self.assertFalse(column.is_datetime)
        self.assertFalse(column.is_text)
        self.assertFalse(column.is_boolean)
        
        # Test effective type
        self.assertEqual(column.get_effective_type(), 'numeric')


class AnalysisSessionModelTest(TestCase):
    """Test cases for AnalysisSession model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.dataset = Dataset.objects.create(
            name='Test Dataset',
            original_filename='test.csv',
            file_size_bytes=1048576,
            file_hash='abc123def456',
            original_format='csv',
            parquet_path='/media/datasets/test.parquet',
            row_count=1000,
            column_count=10,
            user=self.user
        )
        
        self.session_data = {
            'name': 'Test Session',
            'description': 'A test analysis session',
            'is_active': True,
            'user': self.user,
            'primary_dataset': self.dataset
        }
    
    def test_session_creation(self):
        """Test basic session creation"""
        session = AnalysisSession.objects.create(**self.session_data)
        
        self.assertEqual(session.name, 'Test Session')
        self.assertEqual(session.description, 'A test analysis session')
        self.assertTrue(session.is_active)
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.primary_dataset, self.dataset)
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.updated_at)
        self.assertIsNotNone(session.last_accessed)
    
    def test_session_str_representation(self):
        """Test session string representation"""
        session = AnalysisSession.objects.create(**self.session_data)
        expected = f"{session.name} ({session.primary_dataset.name})"
        self.assertEqual(str(session), expected)
    
    def test_session_update_last_accessed(self):
        """Test updating last accessed"""
        session = AnalysisSession.objects.create(**self.session_data)
        old_accessed = session.last_accessed
        
        # Add a small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        session.update_last_accessed()
        
        self.assertGreater(session.last_accessed, old_accessed)


class AnalysisResultModelTest(TestCase):
    """Test cases for AnalysisResult model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.dataset = Dataset.objects.create(
            name='Test Dataset',
            original_filename='test.csv',
            file_size_bytes=1048576,
            file_hash='abc123def456',
            original_format='csv',
            parquet_path='/media/datasets/test.parquet',
            row_count=1000,
            column_count=10,
            user=self.user
        )
        
        self.session = AnalysisSession.objects.create(
            name='Test Session',
            user=self.user,
            primary_dataset=self.dataset
        )
        
        # Create a mock AnalysisTool first
        from analytics.models import AnalysisTool
        self.tool = AnalysisTool.objects.create(
            name='test_tool',
            display_name='Test Tool',
            category='statistical',
            description='Test tool',
            langchain_tool_name='test_tool',
            tool_class='test.Tool',
            tool_function='execute'
        )
        
        self.result_data = {
            'name': 'Test Result',
            'description': 'A test analysis result',
            'tool_used': self.tool,
            'session': self.session,
            'dataset': self.dataset,
            'result_data': {'result': 'test_result'},
            'parameters_used': {'param1': 'value1'},
            'execution_time_ms': 1500,
            'output_type': 'table',
            'cache_key': 'test_cache_key_123',
            'user': self.user
        }
    
    def test_result_creation(self):
        """Test basic result creation"""
        result = AnalysisResult.objects.create(**self.result_data)
        
        self.assertEqual(result.name, 'Test Result')
        self.assertEqual(result.description, 'A test analysis result')
        self.assertEqual(result.tool_used, self.tool)
        self.assertEqual(result.parameters_used, {'param1': 'value1'})
        self.assertEqual(result.result_data, {'result': 'test_result'})
        self.assertEqual(result.output_type, 'table')
        self.assertEqual(result.execution_time_ms, 1500)
        self.assertEqual(result.session, self.session)
        self.assertEqual(result.dataset, self.dataset)
        self.assertEqual(result.user, self.user)
        self.assertIsNotNone(result.created_at)
    
    def test_result_str_representation(self):
        """Test result string representation"""
        result = AnalysisResult.objects.create(**self.result_data)
        expected = f"{result.name} ({result.tool_used.display_name})"
        self.assertEqual(str(result), expected)


class ChatMessageModelTest(TestCase):
    """Test cases for ChatMessage model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.dataset = Dataset.objects.create(
            name='Test Dataset',
            original_filename='test.csv',
            file_size_bytes=1048576,
            file_hash='abc123def456',
            original_format='csv',
            parquet_path='/media/datasets/test.parquet',
            row_count=1000,
            column_count=10,
            user=self.user
        )
        
        self.session = AnalysisSession.objects.create(
            name='Test Session',
            user=self.user,
            primary_dataset=self.dataset
        )
        
        self.message_data = {
            'content': 'Hello, this is a test message',
            'message_type': 'user',
            'session': self.session,
            'user': self.user
        }
    
    def test_message_creation(self):
        """Test basic message creation"""
        message = ChatMessage.objects.create(**self.message_data)
        
        self.assertEqual(message.content, 'Hello, this is a test message')
        self.assertEqual(message.message_type, 'user')
        self.assertEqual(message.session, self.session)
        self.assertEqual(message.user, self.user)
        self.assertIsNotNone(message.created_at)
    
    def test_message_str_representation(self):
        """Test message string representation"""
        message = ChatMessage.objects.create(**self.message_data)
        expected = f"{message.message_type}: {message.content[:50]}..."
        self.assertEqual(str(message), expected)


class GeneratedImageModelTest(TestCase):
    """Test cases for GeneratedImage model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.dataset = Dataset.objects.create(
            name='Test Dataset',
            original_filename='test.csv',
            file_size_bytes=1048576,
            file_hash='abc123def456',
            original_format='csv',
            parquet_path='/media/datasets/test.parquet',
            row_count=1000,
            column_count=10,
            user=self.user
        )
        
        self.session = AnalysisSession.objects.create(
            name='Test Session',
            user=self.user,
            primary_dataset=self.dataset
        )
        
        # Create a mock AnalysisTool first
        from analytics.models import AnalysisTool
        self.tool = AnalysisTool.objects.create(
            name='test_tool',
            display_name='Test Tool',
            category='visualization',
            description='Test visualization tool',
            langchain_tool_name='test_tool',
            tool_class='test.Tool',
            tool_function='execute'
        )
        
        self.result = AnalysisResult.objects.create(
            name='Test Result',
            description='A test visualization result',
            tool_used=self.tool,
            session=self.session,
            dataset=self.dataset,
            result_data={},
            parameters_used={},
            execution_time_ms=1000,
            output_type='chart',
            cache_key='test_cache_key_456',
            user=self.user
        )
        
        self.image_data = {
            'name': 'Test Chart',
            'description': 'A test chart',
            'file_path': '/media/images/test.png',
            'file_size_bytes': 50000,
            'image_format': 'png',
            'width': 800,
            'height': 600,
            'dpi': 300,
            'tool_used': 'matplotlib',
            'parameters_used': {'style': 'dark'},
            'user': self.user,
            'analysis_result': self.result
        }
    
    def test_image_creation(self):
        """Test basic image creation"""
        image = GeneratedImage.objects.create(**self.image_data)
        
        self.assertEqual(image.name, 'Test Chart')
        self.assertEqual(image.description, 'A test chart')
        self.assertEqual(image.file_path, '/media/images/test.png')
        self.assertEqual(image.file_size_bytes, 50000)
        self.assertEqual(image.image_format, 'png')
        self.assertEqual(image.width, 800)
        self.assertEqual(image.height, 600)
        self.assertEqual(image.dpi, 300)
        self.assertEqual(image.tool_used, 'matplotlib')
        self.assertEqual(image.parameters_used, {'style': 'dark'})
        self.assertEqual(image.user, self.user)
        self.assertEqual(image.analysis_result, self.result)
        self.assertIsNotNone(image.created_at)
    
    def test_image_str_representation(self):
        """Test image string representation"""
        image = GeneratedImage.objects.create(**self.image_data)
        expected = f"{image.name} ({image.image_format})"
        self.assertEqual(str(image), expected)


class AuditTrailModelTest(TestCase):
    """Test cases for AuditTrail model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.audit_data = {
            'action_type': 'create',
            'resource_type': 'dataset',
            'resource_id': 123,
            'resource_name': 'Test Dataset',
            'action_description': 'Created new dataset',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0',
            'success': True,
            'user': self.user
        }
    
    def test_audit_creation(self):
        """Test basic audit trail creation"""
        audit = AuditTrail.objects.create(**self.audit_data)
        
        self.assertEqual(audit.action_type, 'create')
        self.assertEqual(audit.resource_type, 'dataset')
        self.assertEqual(audit.resource_id, 123)
        self.assertEqual(audit.resource_name, 'Test Dataset')
        self.assertEqual(audit.action_description, 'Created new dataset')
        self.assertEqual(audit.ip_address, '192.168.1.1')
        self.assertEqual(audit.user_agent, 'Mozilla/5.0')
        self.assertTrue(audit.success)
        self.assertEqual(audit.user, self.user)
        self.assertIsNotNone(audit.created_at)
    
    def test_audit_str_representation(self):
        """Test audit trail string representation"""
        audit = AuditTrail.objects.create(**self.audit_data)
        expected = f"{audit.action_type} - {audit.resource_name} ({audit.created_at})"
        self.assertEqual(str(audit), expected)


class VectorNoteModelTest(TestCase):
    """Test cases for VectorNote model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.note_data = {
            'title': 'Test Note',
            'text': 'This is a test note',
            'scope': 'global',
            'content_type': 'user_insight',
            'metadata_json': {'source': 'test'},
            'user': self.user
        }
    
    def test_note_creation(self):
        """Test basic vector note creation"""
        note = VectorNote.objects.create(**self.note_data)
        
        self.assertEqual(note.title, 'Test Note')
        self.assertEqual(note.text, 'This is a test note')
        self.assertEqual(note.scope, 'global')
        self.assertEqual(note.content_type, 'user_insight')
        self.assertEqual(note.metadata_json, {'source': 'test'})
        self.assertEqual(note.user, self.user)
        self.assertIsNotNone(note.created_at)
        self.assertIsNotNone(note.updated_at)
    
    def test_note_str_representation(self):
        """Test vector note string representation"""
        note = VectorNote.objects.create(**self.note_data)
        expected = f"{note.title} ({note.scope})"
        self.assertEqual(str(note), expected)


class ModelRelationshipTest(TestCase):
    """Test cases for model relationships"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.dataset = Dataset.objects.create(
            name='Test Dataset',
            original_filename='test.csv',
            file_size_bytes=1048576,
            file_hash='abc123def456',
            original_format='csv',
            parquet_path='/media/datasets/test.parquet',
            row_count=1000,
            column_count=10,
            user=self.user
        )
        
        self.column = DatasetColumn.objects.create(
            name='test_column',
            detected_type='numeric',
            dataset=self.dataset
        )
        
        self.session = AnalysisSession.objects.create(
            name='Test Session',
            user=self.user,
            primary_dataset=self.dataset
        )
        
        # Create a mock AnalysisTool first
        from analytics.models import AnalysisTool
        self.tool = AnalysisTool.objects.create(
            name='test_tool',
            display_name='Test Tool',
            category='statistical',
            description='Test tool',
            langchain_tool_name='test_tool',
            tool_class='test.Tool',
            tool_function='execute'
        )
        
        self.result = AnalysisResult.objects.create(
            name='Test Result',
            description='A test analysis result',
            tool_used=self.tool,
            session=self.session,
            dataset=self.dataset,
            result_data={},
            parameters_used={},
            execution_time_ms=1000,
            output_type='table',
            cache_key='test_cache_key_789',
            user=self.user
        )
    
    def test_user_dataset_relationship(self):
        """Test user-dataset relationship"""
        self.assertEqual(self.dataset.user, self.user)
        self.assertIn(self.dataset, self.user.datasets.all())
    
    def test_dataset_column_relationship(self):
        """Test dataset-column relationship"""
        self.assertEqual(self.column.dataset, self.dataset)
        self.assertIn(self.column, self.dataset.columns.all())
    
    def test_user_session_relationship(self):
        """Test user-session relationship"""
        self.assertEqual(self.session.user, self.user)
        self.assertIn(self.session, self.user.analysis_sessions.all())
    
    def test_dataset_session_relationship(self):
        """Test dataset-session relationship"""
        self.assertEqual(self.session.primary_dataset, self.dataset)
        self.assertIn(self.session, self.dataset.primary_sessions.all())
    
    def test_session_result_relationship(self):
        """Test session-result relationship"""
        self.assertEqual(self.result.session, self.session)
        self.assertIn(self.result, self.session.results.all())


class ModelValidationTest(TestCase):
    """Test cases for model validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_email_validation(self):
        """Test user email validation"""
        with self.assertRaises(ValidationError):
            user = User(
                username='testuser2',
                email='invalid-email',
                password='testpass123'
            )
            user.full_clean()
    
    def test_dataset_data_quality_score_validation(self):
        """Test dataset data quality score validation"""
        with self.assertRaises(ValidationError):
            dataset = Dataset(
                name='Test Dataset',
                original_filename='test.csv',
                file_size_bytes=1048576,
                file_hash='abc123def456',
                original_format='csv',
                parquet_path='/media/datasets/test.parquet',
                row_count=1000,
                column_count=10,
                data_quality_score=1.5,  # Invalid: should be between 0 and 1
                user=self.user
            )
            dataset.full_clean()
    
    def test_column_confidence_score_validation(self):
        """Test column confidence score validation"""
        dataset = Dataset.objects.create(
            name='Test Dataset',
            original_filename='test.csv',
            file_size_bytes=1048576,
            file_hash='abc123def456',
            original_format='csv',
            parquet_path='/media/datasets/test.parquet',
            row_count=1000,
            column_count=10,
            user=self.user
        )
        
        with self.assertRaises(ValidationError):
            column = DatasetColumn(
                name='test_column',
                detected_type='numeric',
                confidence_score=1.5,  # Invalid: should be between 0 and 1
                dataset=dataset
            )
            column.full_clean()


class ModelIndexesTest(TestCase):
    """Test cases for model database indexes"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_indexes(self):
        """Test user model indexes"""
        # Test that queries use indexes efficiently
        users = User.objects.filter(token_usage_current_month__gt=0)
        self.assertIsNotNone(users.query)
        
        users = User.objects.filter(storage_used_bytes__gt=0)
        self.assertIsNotNone(users.query)
        
        users = User.objects.filter(last_activity__lt=timezone.now())
        self.assertIsNotNone(users.query)
    
    def test_dataset_indexes(self):
        """Test dataset model indexes"""
        dataset = Dataset.objects.create(
            name='Test Dataset',
            original_filename='test.csv',
            file_size_bytes=1048576,
            file_hash='abc123def456',
            original_format='csv',
            parquet_path='/media/datasets/test.parquet',
            row_count=1000,
            column_count=10,
            user=self.user
        )
        
        # Test that queries use indexes efficiently
        datasets = Dataset.objects.filter(user=self.user, created_at__lt=timezone.now())
        self.assertIsNotNone(datasets.query)
        
        datasets = Dataset.objects.filter(processing_status='completed')
        self.assertIsNotNone(datasets.query)
        
        datasets = Dataset.objects.filter(file_hash='abc123def456')
        self.assertIsNotNone(datasets.query)
