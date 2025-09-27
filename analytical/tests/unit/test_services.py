"""
Unit Tests for Analytics Services

This module contains comprehensive unit tests for all services in the analytics app.
Tests cover functionality, error handling, edge cases, and integration points.
"""

import os
import tempfile
import json
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta

from analytics.models import (
    Dataset, DatasetColumn, AnalysisTool, AnalysisSession, 
    AnalysisResult, ChatMessage, AuditTrail, User
)
from analytics.services import (
    FileProcessingService, ColumnTypeManager, AnalysisExecutor,
    AuditTrailManager, SessionManager, LLMProcessor, AgenticAIController,
    RAGService, ImageManager, SandboxExecutor, ReportGenerator,
    StructuredLogger, VectorNoteManager, GoogleAIService
)

User = get_user_model()


class FileProcessingServiceTest(TestCase):
    """Test FileProcessingService functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = FileProcessingService()
        
    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertIsNotNone(self.service)
        self.assertIsNotNone(self.service.audit_logger)
        
    def test_validate_file_type_valid(self):
        """Test file type validation with valid files"""
        valid_files = [
            'test.csv',
            'data.xlsx',
            'dataset.parquet',
            'analysis.json'
        ]
        
        for filename in valid_files:
            with self.subTest(filename=filename):
                result = self.service.validate_file_type(filename)
                self.assertTrue(result['valid'])
                
    def test_validate_file_type_invalid(self):
        """Test file type validation with invalid files"""
        invalid_files = [
            'malware.exe',
            'script.py',
            'virus.bat',
            'suspicious.scr'
        ]
        
        for filename in invalid_files:
            with self.subTest(filename=filename):
                result = self.service.validate_file_type(filename)
                self.assertFalse(result['valid'])
                
    def test_sanitize_excel_file(self):
        """Test Excel file sanitization"""
        # Create a mock Excel file
        excel_data = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['x', 'y', 'z']
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            excel_data.to_excel(tmp.name, index=False)
            
            with patch('analytics.services.file_processing.pd.read_excel') as mock_read:
                mock_read.return_value = excel_data
                result = self.service.sanitize_excel_file(tmp.name)
                
                self.assertTrue(result['success'])
                self.assertIsNotNone(result['data'])
                
            os.unlink(tmp.name)
            
    def test_convert_to_parquet(self):
        """Test CSV to Parquet conversion"""
        # Create test CSV data
        csv_data = "name,age,city\nJohn,25,NYC\nJane,30,LA"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp.write(csv_data)
            tmp.flush()
            
            result = self.service.convert_to_parquet(tmp.name, 'test_dataset')
            
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['parquet_path'])
            self.assertTrue(os.path.exists(result['parquet_path']))
            
            # Cleanup
            os.unlink(tmp.name)
            if os.path.exists(result['parquet_path']):
                os.unlink(result['parquet_path'])


class ColumnTypeManagerTest(TestCase):
    """Test ColumnTypeManager functionality"""
    
    def setUp(self):
        self.manager = ColumnTypeManager()
        
    def test_detect_numeric_column(self):
        """Test detection of numeric columns"""
        data = pd.Series([1, 2, 3, 4, 5])
        result = self.manager.detect_column_type(data)
        
        self.assertEqual(result['type'], 'numeric')
        self.assertGreater(result['confidence'], 0.8)
        
    def test_detect_categorical_column(self):
        """Test detection of categorical columns"""
        data = pd.Series(['A', 'B', 'A', 'C', 'B'])
        result = self.manager.detect_column_type(data)
        
        self.assertEqual(result['type'], 'categorical')
        self.assertGreater(result['confidence'], 0.7)
        
    def test_detect_datetime_column(self):
        """Test detection of datetime columns"""
        data = pd.Series([
            '2023-01-01',
            '2023-01-02',
            '2023-01-03'
        ])
        result = self.manager.detect_column_type(data)
        
        self.assertEqual(result['type'], 'datetime')
        self.assertGreater(result['confidence'], 0.8)
        
    def test_detect_text_column(self):
        """Test detection of text columns"""
        data = pd.Series(['This is a long text', 'Another text', 'More text'])
        result = self.manager.detect_column_type(data)
        
        self.assertEqual(result['type'], 'text')
        self.assertGreater(result['confidence'], 0.6)


class AnalysisExecutorTest(TestCase):
    """Test AnalysisExecutor functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.dataset = Dataset.objects.create(
            name='test_dataset',
            user=self.user,
            file_size_bytes=1000,
            parquet_size_bytes=500
        )
        self.tool = AnalysisTool.objects.create(
            name='test_tool',
            display_name='Test Tool',
            description='A test analysis tool',
            tool_type='statistical',
            parameters_schema={'param1': 'string'}
        )
        self.session = AnalysisSession.objects.create(
            name='test_session',
            user=self.user,
            primary_dataset=self.dataset,
            is_active=True
        )
        self.executor = AnalysisExecutor()
        
    def test_execute_analysis_success(self):
        """Test successful analysis execution"""
        with patch('analytics.services.analysis_executor.tool_registry') as mock_registry:
            mock_tool = Mock()
            mock_tool.execute.return_value = {'result': 'success'}
            mock_registry.get_tool.return_value = mock_tool
            
            result = self.executor.execute_analysis(
                tool_name='test_tool',
                dataset=self.dataset,
                session=self.session,
                parameters={'param1': 'value1'},
                user=self.user
            )
            
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['result_id'])
            
    def test_execute_analysis_tool_not_found(self):
        """Test analysis execution with non-existent tool"""
        result = self.executor.execute_analysis(
            tool_name='non_existent_tool',
            dataset=self.dataset,
            session=self.session,
            parameters={},
            user=self.user
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
    def test_execute_analysis_validation_error(self):
        """Test analysis execution with invalid parameters"""
        result = self.executor.execute_analysis(
            tool_name='test_tool',
            dataset=self.dataset,
            session=self.session,
            parameters={'invalid_param': 'value'},
            user=self.user
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class AuditTrailManagerTest(TestCase):
    """Test AuditTrailManager functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.manager = AuditTrailManager()
        
    def test_log_action_success(self):
        """Test successful action logging"""
        result = self.manager.log_action(
            user=self.user,
            action_type='CREATE',
            resource_type='Dataset',
            resource_id=1,
            details={'name': 'test_dataset'}
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['audit_id'])
        
    def test_log_action_without_user(self):
        """Test action logging without user"""
        result = self.manager.log_action(
            user=None,
            action_type='VIEW',
            resource_type='Dashboard',
            resource_id=None,
            details={}
        )
        
        self.assertTrue(result['success'])
        
    def test_get_audit_trail(self):
        """Test retrieving audit trail"""
        # Create some audit entries
        self.manager.log_action(
            user=self.user,
            action_type='CREATE',
            resource_type='Dataset',
            resource_id=1,
            details={'name': 'test_dataset'}
        )
        
        trail = self.manager.get_audit_trail(
            user_id=self.user.id,
            limit=10
        )
        
        self.assertIsInstance(trail, list)
        self.assertGreater(len(trail), 0)


class SessionManagerTest(TestCase):
    """Test SessionManager functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.dataset = Dataset.objects.create(
            name='test_dataset',
            user=self.user,
            file_size_bytes=1000,
            parquet_size_bytes=500
        )
        self.manager = SessionManager()
        
    def test_create_session_success(self):
        """Test successful session creation"""
        result = self.manager.create_session(
            name='test_session',
            user=self.user,
            primary_dataset=self.dataset,
            description='Test session'
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['session_id'])
        
    def test_create_session_duplicate_name(self):
        """Test session creation with duplicate name"""
        # Create first session
        self.manager.create_session(
            name='test_session',
            user=self.user,
            primary_dataset=self.dataset
        )
        
        # Try to create another with same name
        result = self.manager.create_session(
            name='test_session',
            user=self.user,
            primary_dataset=self.dataset
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
    def test_get_user_sessions(self):
        """Test retrieving user sessions"""
        # Create some sessions
        self.manager.create_session(
            name='session1',
            user=self.user,
            primary_dataset=self.dataset
        )
        self.manager.create_session(
            name='session2',
            user=self.user,
            primary_dataset=self.dataset
        )
        
        sessions = self.manager.get_user_sessions(self.user.id)
        
        self.assertIsInstance(sessions, list)
        self.assertEqual(len(sessions), 2)


class LLMProcessorTest(TestCase):
    """Test LLMProcessor functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.processor = LLMProcessor()
        
    @patch('analytics.services.llm_processor.GoogleGenerativeAI')
    def test_process_message_success(self, mock_ai):
        """Test successful message processing"""
        mock_model = Mock()
        mock_model.generate_content.return_value.text = "Test response"
        mock_ai.return_value = mock_model
        
        result = self.processor.process_message(
            message="Test message",
            user=self.user,
            context=[]
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['response'], "Test response")
        
    def test_process_message_empty_input(self):
        """Test message processing with empty input"""
        result = self.processor.process_message(
            message="",
            user=self.user,
            context=[]
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class RAGServiceTest(TestCase):
    """Test RAGService functionality"""
    
    def setUp(self):
        self.service = RAGService()
        
    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertIsNotNone(self.service)
        
    @patch('analytics.services.rag_service.redis_client')
    def test_upsert_document_success(self, mock_redis):
        """Test successful document upsert"""
        mock_redis.ft.return_value.add_document.return_value = True
        
        result = self.service.upsert_document(
            doc_id="test_doc",
            content="Test content",
            metadata={"type": "test"}
        )
        
        self.assertTrue(result['success'])
        
    @patch('analytics.services.rag_service.redis_client')
    def test_search_documents_success(self, mock_redis):
        """Test successful document search"""
        mock_redis.ft.return_value.search.return_value = Mock(docs=[])
        
        result = self.service.search_documents(
            query="test query",
            limit=10
        )
        
        self.assertTrue(result['success'])
        self.assertIsInstance(result['results'], list)


class ImageManagerTest(TestCase):
    """Test ImageManager functionality"""
    
    def setUp(self):
        self.manager = ImageManager()
        
    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertIsNotNone(self.manager)
        
    def test_validate_image_format_valid(self):
        """Test image format validation with valid formats"""
        valid_formats = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
        
        for fmt in valid_formats:
            with self.subTest(format=fmt):
                result = self.manager.validate_image_format(fmt)
                self.assertTrue(result['valid'])
                
    def test_validate_image_format_invalid(self):
        """Test image format validation with invalid formats"""
        invalid_formats = ['exe', 'pdf', 'txt', 'doc']
        
        for fmt in invalid_formats:
            with self.subTest(format=fmt):
                result = self.manager.validate_image_format(fmt)
                self.assertFalse(result['valid'])


class SandboxExecutorTest(TestCase):
    """Test SandboxExecutor functionality"""
    
    def setUp(self):
        self.executor = SandboxExecutor()
        
    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertIsNotNone(self.executor)
        
    def test_validate_code_safe(self):
        """Test code validation with safe code"""
        safe_code = "print('Hello, World!')"
        result = self.executor.validate_code(safe_code)
        
        self.assertTrue(result['safe'])
        
    def test_validate_code_unsafe(self):
        """Test code validation with unsafe code"""
        unsafe_code = "import os; os.system('rm -rf /')"
        result = self.executor.validate_code(unsafe_code)
        
        self.assertFalse(result['safe'])
        self.assertIn('error', result)


class ReportGeneratorTest(TestCase):
    """Test ReportGenerator functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.generator = ReportGenerator()
        
    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertIsNotNone(self.generator)
        
    def test_generate_report_success(self):
        """Test successful report generation"""
        with patch('analytics.services.report_generator.tempfile') as mock_tempfile:
            mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value.name = '/tmp/test.pdf'
            
            result = self.generator.generate_report(
                title="Test Report",
                content="Test content",
                format="pdf",
                user=self.user
            )
            
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['file_path'])


class StructuredLoggerTest(TestCase):
    """Test StructuredLogger functionality"""
    
    def setUp(self):
        self.logger = StructuredLogger()
        
    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertIsNotNone(self.logger)
        
    def test_log_info_message(self):
        """Test logging info message"""
        result = self.logger.log_info("Test info message")
        self.assertTrue(result['success'])
        
    def test_log_error_message(self):
        """Test logging error message"""
        result = self.logger.log_error("Test error message", {"error": "test"})
        self.assertTrue(result['success'])


class VectorNoteManagerTest(TestCase):
    """Test VectorNoteManager functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.manager = VectorNoteManager()
        
    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertIsNotNone(self.manager)
        
    def test_create_note_success(self):
        """Test successful note creation"""
        result = self.manager.create_note(
            title="Test Note",
            text="Test content",
            user=self.user,
            scope="global"
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['note_id'])


class GoogleAIServiceTest(TestCase):
    """Test GoogleAIService functionality"""
    
    def setUp(self):
        self.service = GoogleAIService()
        
    def test_service_initialization(self):
        """Test service initializes correctly"""
        self.assertIsNotNone(self.service)
        
    @patch('analytics.services.google_ai_service.genai')
    def test_generate_content_success(self, mock_genai):
        """Test successful content generation"""
        mock_model = Mock()
        mock_model.generate_content.return_value.text = "Generated content"
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = self.service.generate_content("Test prompt")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['content'], "Generated content")
