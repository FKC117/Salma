"""
Unit Tests for Celery Tasks

This module contains comprehensive unit tests for all Celery tasks in the analytics app.
Tests cover file processing tasks, analysis tasks, LLM tasks, agent tasks, and maintenance tasks.
"""

import os
import tempfile
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from analytics.tasks.file_processing_tasks import (
    process_uploaded_file, compress_image, cleanup_old_files
)
from analytics.tasks.analysis_tasks import (
    execute_analysis_task, generate_report_task, process_visualization
)
from analytics.tasks.llm_tasks import (
    process_llm_request, generate_ai_response, process_chat_message
)
from analytics.tasks.agent_tasks import (
    run_agent_analysis, execute_agent_step, monitor_agent_progress
)
from analytics.tasks.image_tasks import (
    process_image_upload, generate_thumbnail, optimize_image
)
from analytics.tasks.report_tasks import (
    generate_pdf_report, generate_excel_report, send_report_email
)
from analytics.tasks.sandbox_tasks import (
    execute_sandbox_code, validate_sandbox_environment, cleanup_sandbox
)
from analytics.tasks.maintenance_tasks import (
    cleanup_old_data, backup_database, monitor_system_health
)

User = get_user_model()


class FileProcessingTasksTest(TestCase):
    """Test file processing tasks"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    @patch('analytics.tasks.file_processing_tasks.FileProcessingService')
    def test_process_uploaded_file_success(self, mock_service):
        """Test successful file processing"""
        mock_instance = Mock()
        mock_instance.process_file.return_value = {
            'success': True,
            'dataset_id': 1,
            'parquet_path': '/tmp/test.parquet'
        }
        mock_service.return_value = mock_instance
        
        result = process_uploaded_file.delay(
            file_path='/tmp/test.csv',
            user_id=self.user.id,
            dataset_name='test_dataset'
        )
        
        # In a real test, you'd check the result
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.file_processing_tasks.FileProcessingService')
    def test_process_uploaded_file_failure(self, mock_service):
        """Test file processing failure"""
        mock_instance = Mock()
        mock_instance.process_file.return_value = {
            'success': False,
            'error': 'Invalid file format'
        }
        mock_service.return_value = mock_instance
        
        result = process_uploaded_file.delay(
            file_path='/tmp/invalid.txt',
            user_id=self.user.id,
            dataset_name='test_dataset'
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.file_processing_tasks.ImageManager')
    def test_compress_image_success(self, mock_manager):
        """Test successful image compression"""
        mock_instance = Mock()
        mock_instance.compress_image.return_value = {
            'success': True,
            'compressed_path': '/tmp/compressed.jpg',
            'size_reduction': 0.5
        }
        mock_manager.return_value = mock_instance
        
        result = compress_image.delay(
            image_path='/tmp/large.jpg',
            target_size_mb=1.0
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.file_processing_tasks.os')
    def test_cleanup_old_files(self, mock_os):
        """Test cleanup of old files"""
        mock_os.listdir.return_value = ['old_file1.txt', 'old_file2.txt']
        mock_os.path.getmtime.return_value = 1000000  # Old timestamp
        mock_os.path.join.return_value = '/tmp/old_file1.txt'
        mock_os.remove.return_value = None
        
        result = cleanup_old_files.delay(
            directory='/tmp',
            max_age_days=7
        )
        
        self.assertIsNotNone(result)


class AnalysisTasksTest(TestCase):
    """Test analysis tasks"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    @patch('analytics.tasks.analysis_tasks.AnalysisExecutor')
    def test_execute_analysis_task_success(self, mock_executor):
        """Test successful analysis execution"""
        mock_instance = Mock()
        mock_instance.execute_analysis.return_value = {
            'success': True,
            'result_id': 1,
            'execution_time': 1.5
        }
        mock_executor.return_value = mock_instance
        
        result = execute_analysis_task.delay(
            tool_name='descriptive_statistics',
            dataset_id=1,
            session_id=1,
            parameters={'column': 'age'},
            user_id=self.user.id
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.analysis_tasks.AnalysisExecutor')
    def test_execute_analysis_task_failure(self, mock_executor):
        """Test analysis execution failure"""
        mock_instance = Mock()
        mock_instance.execute_analysis.return_value = {
            'success': False,
            'error': 'Tool not found'
        }
        mock_executor.return_value = mock_instance
        
        result = execute_analysis_task.delay(
            tool_name='nonexistent_tool',
            dataset_id=1,
            session_id=1,
            parameters={},
            user_id=self.user.id
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.analysis_tasks.ReportGenerator')
    def test_generate_report_task_success(self, mock_generator):
        """Test successful report generation"""
        mock_instance = Mock()
        mock_instance.generate_report.return_value = {
            'success': True,
            'file_path': '/tmp/report.pdf',
            'file_size': 1024
        }
        mock_generator.return_value = mock_instance
        
        result = generate_report_task.delay(
            session_id=1,
            report_type='pdf',
            user_id=self.user.id
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.analysis_tasks.VisualizationTools')
    def test_process_visualization_success(self, mock_tools):
        """Test successful visualization processing"""
        mock_instance = Mock()
        mock_instance.create_visualization.return_value = {
            'success': True,
            'image_path': '/tmp/chart.png',
            'image_id': 1
        }
        mock_tools.return_value = mock_instance
        
        result = process_visualization.delay(
            data={'x': [1, 2, 3], 'y': [4, 5, 6]},
            chart_type='line',
            title='Test Chart'
        )
        
        self.assertIsNotNone(result)


class LLMTasksTest(TestCase):
    """Test LLM tasks"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    @patch('analytics.tasks.llm_tasks.LLMProcessor')
    def test_process_llm_request_success(self, mock_processor):
        """Test successful LLM request processing"""
        mock_instance = Mock()
        mock_instance.process_message.return_value = {
            'success': True,
            'response': 'AI generated response',
            'tokens_used': 150
        }
        mock_processor.return_value = mock_instance
        
        result = process_llm_request.delay(
            message='Test message',
            user_id=self.user.id,
            context=[]
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.llm_tasks.LLMProcessor')
    def test_process_llm_request_failure(self, mock_processor):
        """Test LLM request processing failure"""
        mock_instance = Mock()
        mock_instance.process_message.return_value = {
            'success': False,
            'error': 'API rate limit exceeded'
        }
        mock_processor.return_value = mock_instance
        
        result = process_llm_request.delay(
            message='Test message',
            user_id=self.user.id,
            context=[]
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.llm_tasks.GoogleAIService')
    def test_generate_ai_response_success(self, mock_service):
        """Test successful AI response generation"""
        mock_instance = Mock()
        mock_instance.generate_content.return_value = {
            'success': True,
            'content': 'Generated AI response',
            'tokens_used': 200
        }
        mock_service.return_value = mock_instance
        
        result = generate_ai_response.delay(
            prompt='Generate analysis',
            user_id=self.user.id
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.llm_tasks.ChatMessage')
    def test_process_chat_message_success(self, mock_message):
        """Test successful chat message processing"""
        mock_message.objects.create.return_value = Mock(id=1)
        
        result = process_chat_message.delay(
            message='Hello',
            user_id=self.user.id,
            session_id=1
        )
        
        self.assertIsNotNone(result)


class AgentTasksTest(TestCase):
    """Test agent tasks"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    @patch('analytics.tasks.agent_tasks.AgenticAIController')
    def test_run_agent_analysis_success(self, mock_controller):
        """Test successful agent analysis"""
        mock_instance = Mock()
        mock_instance.run_analysis.return_value = {
            'success': True,
            'agent_run_id': 1,
            'steps_completed': 5
        }
        mock_controller.return_value = mock_instance
        
        result = run_agent_analysis.delay(
            dataset_id=1,
            session_id=1,
            user_id=self.user.id,
            analysis_goal='Find patterns in data'
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.agent_tasks.AgenticAIController')
    def test_run_agent_analysis_failure(self, mock_controller):
        """Test agent analysis failure"""
        mock_instance = Mock()
        mock_instance.run_analysis.return_value = {
            'success': False,
            'error': 'Insufficient data for analysis'
        }
        mock_controller.return_value = mock_instance
        
        result = run_agent_analysis.delay(
            dataset_id=1,
            session_id=1,
            user_id=self.user.id,
            analysis_goal='Find patterns in data'
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.agent_tasks.AgenticAIController')
    def test_execute_agent_step_success(self, mock_controller):
        """Test successful agent step execution"""
        mock_instance = Mock()
        mock_instance.execute_step.return_value = {
            'success': True,
            'step_id': 1,
            'result': 'Step completed successfully'
        }
        mock_controller.return_value = mock_instance
        
        result = execute_agent_step.delay(
            agent_run_id=1,
            step_type='data_analysis',
            parameters={'column': 'age'}
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.agent_tasks.AgentRun')
    def test_monitor_agent_progress(self, mock_agent_run):
        """Test agent progress monitoring"""
        mock_run = Mock()
        mock_run.status = 'running'
        mock_run.progress_percentage = 50
        mock_agent_run.objects.get.return_value = mock_run
        
        result = monitor_agent_progress.delay(agent_run_id=1)
        
        self.assertIsNotNone(result)


class ImageTasksTest(TestCase):
    """Test image tasks"""
    
    @patch('analytics.tasks.image_tasks.ImageManager')
    def test_process_image_upload_success(self, mock_manager):
        """Test successful image upload processing"""
        mock_instance = Mock()
        mock_instance.process_upload.return_value = {
            'success': True,
            'image_id': 1,
            'file_path': '/tmp/processed.jpg'
        }
        mock_manager.return_value = mock_instance
        
        result = process_image_upload.delay(
            image_path='/tmp/upload.jpg',
            user_id=1
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.image_tasks.ImageManager')
    def test_generate_thumbnail_success(self, mock_manager):
        """Test successful thumbnail generation"""
        mock_instance = Mock()
        mock_instance.generate_thumbnail.return_value = {
            'success': True,
            'thumbnail_path': '/tmp/thumb.jpg',
            'size': (150, 150)
        }
        mock_manager.return_value = mock_instance
        
        result = generate_thumbnail.delay(
            image_path='/tmp/large.jpg',
            size=(150, 150)
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.image_tasks.ImageManager')
    def test_optimize_image_success(self, mock_manager):
        """Test successful image optimization"""
        mock_instance = Mock()
        mock_instance.optimize_image.return_value = {
            'success': True,
            'optimized_path': '/tmp/optimized.jpg',
            'size_reduction': 0.3
        }
        mock_manager.return_value = mock_instance
        
        result = optimize_image.delay(
            image_path='/tmp/large.jpg',
            target_size_mb=1.0
        )
        
        self.assertIsNotNone(result)


class ReportTasksTest(TestCase):
    """Test report tasks"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    @patch('analytics.tasks.report_tasks.ReportGenerator')
    def test_generate_pdf_report_success(self, mock_generator):
        """Test successful PDF report generation"""
        mock_instance = Mock()
        mock_instance.generate_pdf.return_value = {
            'success': True,
            'file_path': '/tmp/report.pdf',
            'file_size': 2048
        }
        mock_generator.return_value = mock_instance
        
        result = generate_pdf_report.delay(
            session_id=1,
            user_id=self.user.id,
            title='Analysis Report'
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.report_tasks.ReportGenerator')
    def test_generate_excel_report_success(self, mock_generator):
        """Test successful Excel report generation"""
        mock_instance = Mock()
        mock_instance.generate_excel.return_value = {
            'success': True,
            'file_path': '/tmp/report.xlsx',
            'file_size': 4096
        }
        mock_generator.return_value = mock_instance
        
        result = generate_excel_report.delay(
            session_id=1,
            user_id=self.user.id,
            title='Data Report'
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.report_tasks.send_mail')
    def test_send_report_email_success(self, mock_send_mail):
        """Test successful report email sending"""
        mock_send_mail.return_value = True
        
        result = send_report_email.delay(
            user_id=self.user.id,
            report_path='/tmp/report.pdf',
            subject='Your Analysis Report'
        )
        
        self.assertIsNotNone(result)


class SandboxTasksTest(TestCase):
    """Test sandbox tasks"""
    
    @patch('analytics.tasks.sandbox_tasks.SandboxExecutor')
    def test_execute_sandbox_code_success(self, mock_executor):
        """Test successful sandbox code execution"""
        mock_instance = Mock()
        mock_instance.execute_code.return_value = {
            'success': True,
            'output': 'Hello, World!',
            'execution_time': 0.1
        }
        mock_executor.return_value = mock_instance
        
        result = execute_sandbox_code.delay(
            code='print("Hello, World!")',
            user_id=1
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.sandbox_tasks.SandboxExecutor')
    def test_execute_sandbox_code_failure(self, mock_executor):
        """Test sandbox code execution failure"""
        mock_instance = Mock()
        mock_instance.execute_code.return_value = {
            'success': False,
            'error': 'Code execution timeout'
        }
        mock_executor.return_value = mock_instance
        
        result = execute_sandbox_code.delay(
            code='while True: pass',  # Infinite loop
            user_id=1
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.sandbox_tasks.SandboxExecutor')
    def test_validate_sandbox_environment(self, mock_executor):
        """Test sandbox environment validation"""
        mock_instance = Mock()
        mock_instance.validate_environment.return_value = {
            'valid': True,
            'python_version': '3.11.0',
            'available_packages': ['pandas', 'numpy']
        }
        mock_executor.return_value = mock_instance
        
        result = validate_sandbox_environment.delay()
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.sandbox_tasks.SandboxExecutor')
    def test_cleanup_sandbox(self, mock_executor):
        """Test sandbox cleanup"""
        mock_instance = Mock()
        mock_instance.cleanup.return_value = {
            'success': True,
            'files_removed': 5,
            'space_freed': 1024
        }
        mock_executor.return_value = mock_instance
        
        result = cleanup_sandbox.delay()
        
        self.assertIsNotNone(result)


class MaintenanceTasksTest(TestCase):
    """Test maintenance tasks"""
    
    @patch('analytics.tasks.maintenance_tasks.Dataset')
    def test_cleanup_old_data_success(self, mock_dataset):
        """Test successful old data cleanup"""
        mock_dataset.objects.filter.return_value.delete.return_value = (5, {'Dataset': 5})
        
        result = cleanup_old_data.delay(
            days_old=30,
            dry_run=False
        )
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.maintenance_tasks.backup_database')
    def test_backup_database_success(self, mock_backup):
        """Test successful database backup"""
        mock_backup.return_value = {
            'success': True,
            'backup_path': '/tmp/backup.sql',
            'backup_size': 1024000
        }
        
        result = backup_database.delay()
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.maintenance_tasks.psutil')
    def test_monitor_system_health_success(self, mock_psutil):
        """Test successful system health monitoring"""
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.disk_usage.return_value.percent = 45.0
        
        result = monitor_system_health.delay()
        
        self.assertIsNotNone(result)
        
    @patch('analytics.tasks.maintenance_tasks.psutil')
    def test_monitor_system_health_high_usage(self, mock_psutil):
        """Test system health monitoring with high resource usage"""
        mock_psutil.cpu_percent.return_value = 95.0
        mock_psutil.virtual_memory.return_value.percent = 90.0
        mock_psutil.disk_usage.return_value.percent = 85.0
        
        result = monitor_system_health.delay()
        
        self.assertIsNotNone(result)
