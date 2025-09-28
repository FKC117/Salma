"""
Integration Test: End-to-End User Journey (T025)
Tests the complete end-to-end user journey workflow
"""

import pytest
import json
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestEndToEndJourney(TransactionTestCase):
    """Integration tests for complete end-to-end user journey"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Test data
        self.csv_content = """name,age,city,salary,department
John,25,New York,50000,Engineering
Jane,30,Los Angeles,60000,Marketing
Bob,35,Chicago,55000,Engineering
Alice,28,San Francisco,70000,Product
Charlie,32,Boston,65000,Sales
Diana,29,Seattle,58000,Engineering
Eve,31,Austin,62000,Marketing
Frank,27,Denver,52000,Sales"""
        
        self.dataset_id = 1
        self.session_id = 'sess_e2e_test'
        self.agent_run_id = 1
        self.report_id = 'report_e2e_test'
    
    def test_complete_user_journey_workflow(self):
        """Test complete user journey from login to report download"""
        
        # Step 1: File Upload
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': self.dataset_id,
                'filename': 'employee_data.csv',
                'columns': ['name', 'age', 'city', 'salary', 'department'],
                'row_count': 8,
                'file_size': 1024,
                'parquet_path': '/media/datasets/employee_data.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'column_types': {
                    'name': 'categorical',
                    'age': 'numeric',
                    'city': 'categorical',
                    'salary': 'numeric',
                    'department': 'categorical'
                }
            }
            
            csv_file = SimpleUploadedFile(
                "employee_data.csv",
                self.csv_content.encode('utf-8'),
                content_type="text/csv"
            )
            
            upload_response = self.client.post('/api/upload/', {
                'file': csv_file,
                'description': 'Employee dataset for end-to-end testing'
            }, format='multipart')
            
            self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
            self.assertIn('dataset_id', upload_response.data)
            
            # Step 2: Session Creation
            with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create_session:
                mock_create_session.return_value = {
                    'success': True,
                    'session_id': self.session_id,
                    'dataset_id': self.dataset_id,
                    'dataset_name': 'employee_data.csv',
                    'created_at': '2025-09-23T15:01:00Z',
                    'status': 'active',
                    'session_info': {
                        'user_id': self.user.id,
                        'session_name': 'Employee Analysis Session',
                        'dataset_columns': ['name', 'age', 'city', 'salary', 'department'],
                        'available_tools': ['descriptive_stats', 'correlation_matrix', 'regression_analysis']
                    }
                }
                
                session_response = self.client.post('/api/sessions/', {
                    'dataset_id': self.dataset_id,
                    'session_name': 'Employee Analysis Session'
                }, format='json')
                
                self.assertEqual(session_response.status_code, status.HTTP_201_CREATED)
                self.assertIn('session_id', session_response.data)
                
                # Step 3: Tool Selection and Analysis
                with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
                    mock_execute.return_value = {
                        'success': True,
                        'analysis_id': 1,
                        'tool_name': 'descriptive_stats',
                        'status': 'completed',
                        'results': {
                            'summary': 'Descriptive statistics calculated for employee data',
                            'tables': [
                                {
                                    'title': 'Summary Statistics',
                                    'data': [
                                        {'column': 'age', 'mean': 29.75, 'std': 3.2, 'min': 25, 'max': 35},
                                        {'column': 'salary', 'mean': 59000.0, 'std': 6500.0, 'min': 50000, 'max': 70000}
                                    ]
                                }
                            ],
                            'charts': [
                                {
                                    'title': 'Age Distribution',
                                    'type': 'histogram',
                                    'image_url': '/media/charts/age_histogram.png'
                                }
                            ]
                        },
                        'execution_time': 2.5,
                        'created_at': '2025-09-23T15:02:00Z'
                    }
                    
                    analysis_response = self.client.post('/api/analysis/execute/', {
                        'session_id': self.session_id,
                        'tool_name': 'descriptive_stats',
                        'parameters': {
                            'columns': ['age', 'salary'],
                            'include_charts': True
                        }
                    }, format='json')
                    
                    self.assertEqual(analysis_response.status_code, status.HTTP_200_OK)
                    self.assertIn('results', analysis_response.data)
                    
                    # Step 4: AI Chat Interaction
                    with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process_message:
                        mock_process_message.return_value = {
                            'success': True,
                            'message_id': 'msg_e2e_test',
                            'user_message': 'What insights can you provide about the employee data?',
                            'assistant_response': 'Based on the analysis, I can see that the employee age ranges from 25-35 with an average of 29.75 years. The salary distribution shows a mean of $59,000 with a standard deviation of $6,500. The data suggests a relatively young workforce with moderate salary variation.',
                            'tokens_used': 85,
                            'cost': 0.000425,
                            'created_at': '2025-09-23T15:03:00Z',
                            'context_used': True
                        }
                        
                        chat_response = self.client.post('/api/chat/messages/', {
                            'session_id': self.session_id,
                            'message': 'What insights can you provide about the employee data?',
                            'include_context': True
                        }, format='json')
                        
                        self.assertEqual(chat_response.status_code, status.HTTP_200_OK)
                        self.assertIn('assistant_response', chat_response.data)
                        
                        # Step 5: Agentic AI Analysis
                        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start_agent:
                            mock_start_agent.return_value = {
                                'success': True,
                                'agent_run_id': self.agent_run_id,
                                'status': 'planning',
                                'correlation_id': 'agent_e2e_test',
                                'estimated_completion_time': 300,
                                'progress_url': '/api/agent/run/1/status/',
                                'goal': 'Analyze salary patterns by department and age'
                            }
                            
                            agent_response = self.client.post('/api/agent/run/', {
                                'dataset_id': self.dataset_id,
                                'goal': 'Analyze salary patterns by department and age'
                            }, format='json')
                            
                            self.assertEqual(agent_response.status_code, status.HTTP_200_OK)
                            self.assertIn('agent_run_id', agent_response.data)
                            
                            # Step 6: Report Generation
                            with patch('analytics.services.report_generator.ReportGenerator.initiate_report') as mock_initiate_report:
                                mock_initiate_report.return_value = {
                                    'success': True,
                                    'report_id': self.report_id,
                                    'status': 'initiated',
                                    'report_config': {
                                        'title': 'Employee Data Analysis Report',
                                        'sections': ['executive_summary', 'analysis_results', 'recommendations'],
                                        'format': 'docx'
                                    },
                                    'estimated_completion_time': 120
                                }
                                
                                report_response = self.client.post('/api/reports/generate/', {
                                    'session_id': self.session_id,
                                    'report_config': {
                                        'title': 'Employee Data Analysis Report',
                                        'sections': ['executive_summary', 'analysis_results', 'recommendations'],
                                        'format': 'docx'
                                    }
                                }, format='json')
                                
                                self.assertEqual(report_response.status_code, status.HTTP_201_CREATED)
                                self.assertIn('report_id', report_response.data)
                                
                                # Step 7: Report Download
                                with patch('analytics.services.report_generator.ReportGenerator.generate_download') as mock_download:
                                    mock_download.return_value = {
                                        'success': True,
                                        'report_id': self.report_id,
                                        'download_info': {
                                            'filename': 'employee_data_analysis_report.docx',
                                            'file_size_mb': 2.5,
                                            'download_url': '/api/reports/report_e2e_test/download/',
                                            'expires_at': '2025-09-30T15:00:00Z'
                                        }
                                    }
                                    
                                    download_response = self.client.get(f'/api/reports/{self.report_id}/download/')
                                    
                                    self.assertEqual(download_response.status_code, status.HTTP_200_OK)
                                    self.assertIn('download_info', download_response.data)
                                    self.assertIn('download_url', download_response.data['download_info'])
    
    def test_user_journey_with_error_recovery(self):
        """Test user journey with error recovery scenarios"""
        
        # Step 1: File Upload with Error
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': False,
                'error': 'File format not supported',
                'error_code': 'UNSUPPORTED_FORMAT',
                'suggestions': ['Use CSV, XLS, or JSON format']
            }
            
            invalid_file = SimpleUploadedFile(
                "invalid_file.txt",
                b"plain text content",
                content_type="text/plain"
            )
            
            upload_response = self.client.post('/api/upload/', {
                'file': invalid_file,
                'description': 'Invalid file format'
            }, format='multipart')
            
            self.assertEqual(upload_response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', upload_response.data)
            
            # Step 2: Retry with Valid File
            with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process_retry:
                mock_process_retry.return_value = {
                    'success': True,
                    'dataset_id': self.dataset_id,
                    'filename': 'employee_data.csv',
                    'columns': ['name', 'age', 'city', 'salary'],
                    'row_count': 5,
                    'file_size': 512,
                    'parquet_path': '/media/datasets/employee_data.parquet',
                    'uploaded_at': '2025-09-23T15:00:00Z'
                }
                
                csv_file = SimpleUploadedFile(
                    "employee_data.csv",
                    self.csv_content.encode('utf-8'),
                    content_type="text/csv"
                )
                
                retry_response = self.client.post('/api/upload/', {
                    'file': csv_file,
                    'description': 'Retry with valid file'
                }, format='multipart')
                
                self.assertEqual(retry_response.status_code, status.HTTP_201_CREATED)
                
                # Step 3: Analysis with Error Recovery
                with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
                    mock_execute.return_value = {
                        'success': False,
                        'error': 'Insufficient data for analysis',
                        'error_code': 'INSUFFICIENT_DATA',
                        'suggestions': ['Ensure dataset has at least 10 rows', 'Check data quality']
                    }
                    
                    analysis_response = self.client.post('/api/analysis/execute/', {
                        'session_id': self.session_id,
                        'tool_name': 'descriptive_stats',
                        'parameters': {
                            'columns': ['age', 'salary']
                        }
                    }, format='json')
                    
                    self.assertEqual(analysis_response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
                    self.assertIn('error', analysis_response.data)
    
    def test_user_journey_with_performance_optimization(self):
        """Test user journey with performance optimization"""
        
        # Step 1: Optimized File Upload
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': self.dataset_id,
                'filename': 'large_dataset.csv',
                'columns': ['col1', 'col2', 'col3', 'col4', 'col5'],
                'row_count': 10000,
                'file_size': 5000,
                'parquet_path': '/media/datasets/large_dataset.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'processing_info': {
                    'compression_ratio': 0.8,
                    'processing_time_ms': 1500,
                    'memory_usage_mb': 128,
                    'optimization_applied': True
                }
            }
            
            large_csv_content = "col1,col2,col3,col4,col5\n" + "\n".join([
                f"value{i},value{i+1},value{i+2},value{i+3},value{i+4}" 
                for i in range(10000)
            ])
            
            large_file = SimpleUploadedFile(
                "large_dataset.csv",
                large_csv_content.encode('utf-8'),
                content_type="text/csv"
            )
            
            upload_response = self.client.post('/api/upload/', {
                'file': large_file,
                'description': 'Large dataset for performance testing'
            }, format='multipart')
            
            self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
            self.assertIn('processing_info', upload_response.data)
            self.assertTrue(upload_response.data['processing_info']['optimization_applied'])
            
            # Step 2: Optimized Analysis Execution
            with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
                mock_execute.return_value = {
                    'success': True,
                    'analysis_id': 1,
                    'tool_name': 'descriptive_stats',
                    'status': 'completed',
                    'results': {
                        'summary': 'Optimized analysis completed',
                        'tables': [
                            {
                                'title': 'Summary Statistics',
                                'data': [
                                    {'column': 'col1', 'mean': 5000.0, 'std': 2886.0, 'min': 0, 'max': 10000}
                                ]
                            }
                        ]
                    },
                    'execution_time': 5.2,
                    'performance_info': {
                        'memory_optimized': True,
                        'parallel_processing': True,
                        'cache_used': True,
                        'optimization_level': 'aggressive'
                    }
                }
                
                analysis_response = self.client.post('/api/analysis/execute/', {
                    'session_id': self.session_id,
                    'tool_name': 'descriptive_stats',
                    'parameters': {
                        'columns': ['col1', 'col2'],
                        'optimization_level': 'aggressive'
                    }
                }, format='json')
                
                self.assertEqual(analysis_response.status_code, status.HTTP_200_OK)
                self.assertIn('performance_info', analysis_response.data)
                self.assertTrue(analysis_response.data['performance_info']['memory_optimized'])
    
    def test_user_journey_with_security_validation(self):
        """Test user journey with security validation"""
        
        # Step 1: File Upload with Security Scan
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': self.dataset_id,
                'filename': 'secure_dataset.csv',
                'columns': ['name', 'age', 'salary'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/secure_dataset.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'security_scan': {
                    'malware_scan': 'passed',
                    'content_validation': 'passed',
                    'data_sanitization': 'completed',
                    'threats_detected': [],
                    'security_score': 0.95
                }
            }
            
            csv_file = SimpleUploadedFile(
                "secure_dataset.csv",
                self.csv_content.encode('utf-8'),
                content_type="text/csv"
            )
            
            upload_response = self.client.post('/api/upload/', {
                'file': csv_file,
                'description': 'Secure dataset upload'
            }, format='multipart')
            
            self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
            self.assertIn('security_scan', upload_response.data)
            self.assertEqual(upload_response.data['security_scan']['security_score'], 0.95)
            
            # Step 2: Secure Analysis Execution
            with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
                mock_execute.return_value = {
                    'success': True,
                    'analysis_id': 1,
                    'tool_name': 'descriptive_stats',
                    'status': 'completed',
                    'results': {
                        'summary': 'Secure analysis completed',
                        'tables': [
                            {
                                'title': 'Summary Statistics',
                                'data': [
                                    {'column': 'age', 'mean': 30.0, 'std': 3.0, 'min': 25, 'max': 35}
                                ]
                            }
                        ]
                    },
                    'execution_time': 2.0,
                    'security_info': {
                        'data_masking': 'applied',
                        'access_control': 'enforced',
                        'audit_logged': True,
                        'compliance_verified': True
                    }
                }
                
                analysis_response = self.client.post('/api/analysis/execute/', {
                    'session_id': self.session_id,
                    'tool_name': 'descriptive_stats',
                    'parameters': {
                        'columns': ['age', 'salary']
                    }
                }, format='json')
                
                self.assertEqual(analysis_response.status_code, status.HTTP_200_OK)
                self.assertIn('security_info', analysis_response.data)
                self.assertTrue(analysis_response.data['security_info']['audit_logged'])
    
    def test_user_journey_with_audit_trail(self):
        """Test user journey with comprehensive audit trail"""
        
        # Mock audit logging for all steps
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
            mock_audit.return_value = {'success': True}
            
            # Step 1: File Upload with Audit
            with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
                mock_process.return_value = {
                    'success': True,
                    'dataset_id': self.dataset_id,
                    'filename': 'audit_dataset.csv',
                    'columns': ['name', 'age', 'salary'],
                    'row_count': 5,
                    'file_size': 1024,
                    'parquet_path': '/media/datasets/audit_dataset.parquet',
                    'uploaded_at': '2025-09-23T15:00:00Z'
                }
                
                csv_file = SimpleUploadedFile(
                    "audit_dataset.csv",
                    self.csv_content.encode('utf-8'),
                    content_type="text/csv"
                )
                
                upload_response = self.client.post('/api/upload/', {
                    'file': csv_file,
                    'description': 'Dataset for audit testing'
                }, format='multipart')
                
                self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
                
                # Verify audit logging was called
                self.assertTrue(mock_audit.called)
                
                # Step 2: Session Creation with Audit
                with patch('analytics.services.session_manager.SessionManager.create_session') as mock_create_session:
                    mock_create_session.return_value = {
                        'success': True,
                        'session_id': self.session_id,
                        'dataset_id': self.dataset_id,
                        'created_at': '2025-09-23T15:01:00Z',
                        'status': 'active'
                    }
                    
                    session_response = self.client.post('/api/sessions/', {
                        'dataset_id': self.dataset_id,
                        'session_name': 'Audit Test Session'
                    }, format='json')
                    
                    self.assertEqual(session_response.status_code, status.HTTP_201_CREATED)
                    
                    # Verify audit logging was called again
                    self.assertTrue(mock_audit.call_count >= 2)
    
    def test_user_journey_with_concurrent_operations(self):
        """Test user journey with concurrent operations"""
        
        # Simulate concurrent file uploads
        with patch('analytics.services.file_processing.FileProcessingService.process_file') as mock_process:
            mock_process.return_value = {
                'success': True,
                'dataset_id': self.dataset_id,
                'filename': 'concurrent_dataset.csv',
                'columns': ['name', 'age', 'salary'],
                'row_count': 5,
                'file_size': 1024,
                'parquet_path': '/media/datasets/concurrent_dataset.parquet',
                'uploaded_at': '2025-09-23T15:00:00Z',
                'concurrent_info': {
                    'queue_position': 1,
                    'estimated_wait_time': 30,
                    'processing_priority': 'normal'
                }
            }
            
            csv_file = SimpleUploadedFile(
                "concurrent_dataset.csv",
                self.csv_content.encode('utf-8'),
                content_type="text/csv"
            )
            
            upload_response = self.client.post('/api/upload/', {
                'file': csv_file,
                'description': 'Concurrent upload test'
            }, format='multipart')
            
            self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
            self.assertIn('concurrent_info', upload_response.data)
            self.assertIn('queue_position', upload_response.data['concurrent_info'])
            
            # Simulate concurrent analysis execution
            with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
                mock_execute.return_value = {
                    'success': True,
                    'analysis_id': 1,
                    'tool_name': 'descriptive_stats',
                    'status': 'completed',
                    'results': {
                        'summary': 'Concurrent analysis completed',
                        'tables': []
                    },
                    'execution_time': 2.0,
                    'concurrent_info': {
                        'resource_allocation': {
                            'memory_limit_mb': 256,
                            'cpu_limit_percent': 50
                        },
                        'load_balancing': 'enabled'
                    }
                }
                
                analysis_response = self.client.post('/api/analysis/execute/', {
                    'session_id': self.session_id,
                    'tool_name': 'descriptive_stats',
                    'parameters': {
                        'columns': ['age', 'salary']
                    }
                }, format='json')
                
                self.assertEqual(analysis_response.status_code, status.HTTP_200_OK)
                self.assertIn('concurrent_info', analysis_response.data)
                self.assertIn('resource_allocation', analysis_response.data['concurrent_info'])
