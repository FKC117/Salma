"""
Integration Test: Report Generation Workflow (T024)
Tests the complete report generation workflow
"""

import pytest
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestReportGenerationWorkflow(TestCase):
    """Integration tests for report generation workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock session and analysis data
        self.session_id = 'sess_123456789'
        self.analysis_id = 1
        self.report_id = 'report_123456789'
    
    def test_report_generation_initiation_workflow(self):
        """Test report generation initiation workflow"""
        with patch('analytics.services.report_generator.ReportGenerator.initiate_report') as mock_initiate:
            mock_initiate.return_value = {
                'success': True,
                'report_id': self.report_id,
                'status': 'initiated',
                'report_config': {
                    'title': 'Data Analysis Report',
                    'subtitle': 'Comprehensive Analysis of Dataset',
                    'author': self.user.username,
                    'date': '2025-09-23',
                    'sections': [
                        {
                            'section_id': 'executive_summary',
                            'title': 'Executive Summary',
                            'include': True,
                            'content_type': 'text'
                        },
                        {
                            'section_id': 'data_overview',
                            'title': 'Data Overview',
                            'include': True,
                            'content_type': 'table'
                        },
                        {
                            'section_id': 'analysis_results',
                            'title': 'Analysis Results',
                            'include': True,
                            'content_type': 'mixed'
                        },
                        {
                            'section_id': 'recommendations',
                            'title': 'Recommendations',
                            'include': True,
                            'content_type': 'text'
                        }
                    ],
                    'format': 'docx',
                    'template': 'professional'
                },
                'estimated_completion_time': 120,
                'progress_url': '/api/reports/123456789/status/'
            }
            
            response = self.client.post('/api/reports/generate/', {
                'session_id': self.session_id,
                'report_config': {
                    'title': 'Data Analysis Report',
                    'sections': ['executive_summary', 'data_overview', 'analysis_results', 'recommendations'],
                    'format': 'docx',
                    'template': 'professional'
                }
            }, format='json')
            
            # Verify report initiation
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('report_id', response.data)
            self.assertIn('report_config', response.data)
            self.assertIn('estimated_completion_time', response.data)
            self.assertEqual(response.data['status'], 'initiated')
    
    def test_report_content_collection_workflow(self):
        """Test report content collection workflow"""
        with patch('analytics.services.report_generator.ReportGenerator.collect_content') as mock_collect:
            mock_collect.return_value = {
                'success': True,
                'report_id': self.report_id,
                'status': 'collecting',
                'content_collection': {
                    'session_data': {
                        'session_id': self.session_id,
                        'dataset_name': 'Test Dataset',
                        'total_analyses': 3,
                        'session_duration': 1800
                    },
                    'analysis_results': [
                        {
                            'analysis_id': 1,
                            'tool_name': 'descriptive_stats',
                            'title': 'Descriptive Statistics',
                            'summary': 'Basic statistics calculated for numeric columns',
                            'tables': [
                                {
                                    'title': 'Summary Statistics',
                                    'data': [
                                        {'column': 'age', 'mean': 30.0, 'std': 5.0},
                                        {'column': 'salary', 'mean': 60000.0, 'std': 10000.0}
                                    ]
                                }
                            ],
                            'charts': [
                                {
                                    'title': 'Age Distribution',
                                    'type': 'histogram',
                                    'image_url': '/media/charts/age_histogram.png'
                                }
                            ],
                            'llm_interpretation': 'The data shows normal distributions for both age and salary variables.'
                        },
                        {
                            'analysis_id': 2,
                            'tool_name': 'correlation_matrix',
                            'title': 'Correlation Analysis',
                            'summary': 'Correlation matrix calculated between numeric variables',
                            'tables': [
                                {
                                    'title': 'Correlation Matrix',
                                    'data': [
                                        {'var1': 'age', 'var2': 'salary', 'correlation': 0.75}
                                    ]
                                }
                            ],
                            'charts': [
                                {
                                    'title': 'Correlation Heatmap',
                                    'type': 'heatmap',
                                    'image_url': '/media/charts/correlation_heatmap.png'
                                }
                            ],
                            'llm_interpretation': 'Strong positive correlation found between age and salary.'
                        }
                    ],
                    'chat_history': [
                        {
                            'message_id': 'msg_1',
                            'user_message': 'What does the age distribution tell us?',
                            'assistant_response': 'The age distribution shows a normal distribution with a mean of 30 years.',
                            'timestamp': '2025-09-23T15:00:00Z'
                        },
                        {
                            'message_id': 'msg_2',
                            'user_message': 'Can you explain the correlation?',
                            'assistant_response': 'The correlation of 0.75 indicates a strong positive relationship.',
                            'timestamp': '2025-09-23T15:05:00Z'
                        }
                    ],
                    'metadata': {
                        'total_pages_estimated': 8,
                        'total_images': 2,
                        'total_tables': 2,
                        'content_size_mb': 2.5
                    }
                }
            }
            
            response = self.client.post(f'/api/reports/{self.report_id}/collect/', {
                'include_analysis_results': True,
                'include_chat_history': True,
                'include_metadata': True
            }, format='json')
            
            # Verify content collection
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('content_collection', response.data)
            self.assertIn('analysis_results', response.data['content_collection'])
            self.assertIn('chat_history', response.data['content_collection'])
            self.assertEqual(len(response.data['content_collection']['analysis_results']), 2)
    
    def test_report_template_processing_workflow(self):
        """Test report template processing workflow"""
        with patch('analytics.services.report_generator.ReportGenerator.process_template') as mock_process:
            mock_process.return_value = {
                'success': True,
                'report_id': self.report_id,
                'status': 'processing',
                'template_processing': {
                    'template_used': 'professional',
                    'template_customization': {
                        'company_logo': '/media/logos/company_logo.png',
                        'color_scheme': 'blue',
                        'font_family': 'Arial',
                        'header_style': 'modern'
                    },
                    'section_processing': [
                        {
                            'section_id': 'executive_summary',
                            'status': 'processed',
                            'content_length': 250,
                            'formatting_applied': True
                        },
                        {
                            'section_id': 'data_overview',
                            'status': 'processed',
                            'tables_included': 1,
                            'formatting_applied': True
                        },
                        {
                            'section_id': 'analysis_results',
                            'status': 'processed',
                            'analyses_included': 2,
                            'charts_included': 2,
                            'formatting_applied': True
                        },
                        {
                            'section_id': 'recommendations',
                            'status': 'processed',
                            'recommendations_count': 3,
                            'formatting_applied': True
                        }
                    ],
                    'processing_stats': {
                        'total_sections': 4,
                        'processed_sections': 4,
                        'processing_time_ms': 1500,
                        'template_size_mb': 0.5
                    }
                }
            }
            
            response = self.client.post(f'/api/reports/{self.report_id}/process/', {
                'template': 'professional',
                'customization': {
                    'color_scheme': 'blue',
                    'font_family': 'Arial',
                    'header_style': 'modern'
                }
            }, format='json')
            
            # Verify template processing
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('template_processing', response.data)
            self.assertIn('section_processing', response.data['template_processing'])
            self.assertIn('processing_stats', response.data['template_processing'])
            self.assertEqual(response.data['template_processing']['processing_stats']['processed_sections'], 4)
    
    def test_report_compilation_workflow(self):
        """Test report compilation workflow"""
        with patch('analytics.services.report_generator.ReportGenerator.compile_report') as mock_compile:
            mock_compile.return_value = {
                'success': True,
                'report_id': self.report_id,
                'status': 'compiling',
                'compilation_results': {
                    'output_format': 'docx',
                    'file_size_mb': 3.2,
                    'total_pages': 8,
                    'compilation_time_ms': 2500,
                    'quality_checks': {
                        'spelling_check': 'passed',
                        'formatting_check': 'passed',
                        'image_quality_check': 'passed',
                        'table_formatting_check': 'passed'
                    },
                    'output_file': {
                        'filename': 'data_analysis_report_20250923.docx',
                        'path': '/media/reports/data_analysis_report_20250923.docx',
                        'url': '/api/reports/123456789/download/',
                        'expires_at': '2025-09-30T15:00:00Z'
                    },
                    'metadata': {
                        'creation_date': '2025-09-23T15:00:00Z',
                        'last_modified': '2025-09-23T15:00:00Z',
                        'author': self.user.username,
                        'version': '1.0'
                    }
                }
            }
            
            response = self.client.post(f'/api/reports/{self.report_id}/compile/', {
                'output_format': 'docx',
                'quality_checks': True,
                'compression': True
            }, format='json')
            
            # Verify report compilation
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('compilation_results', response.data)
            self.assertIn('output_file', response.data['compilation_results'])
            self.assertIn('quality_checks', response.data['compilation_results'])
            self.assertEqual(response.data['compilation_results']['total_pages'], 8)
    
    def test_report_download_workflow(self):
        """Test report download workflow"""
        with patch('analytics.services.report_generator.ReportGenerator.generate_download') as mock_download:
            mock_download.return_value = {
                'success': True,
                'report_id': self.report_id,
                'download_info': {
                    'filename': 'data_analysis_report_20250923.docx',
                    'file_size_mb': 3.2,
                    'download_url': '/api/reports/123456789/download/',
                    'expires_at': '2025-09-30T15:00:00Z',
                    'download_count': 1,
                    'max_downloads': 10
                },
                'download_stats': {
                    'total_downloads': 1,
                    'last_downloaded': '2025-09-23T15:00:00Z',
                    'download_location': 'local_storage'
                }
            }
            
            response = self.client.get(f'/api/reports/{self.report_id}/download/')
            
            # Verify download workflow
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('download_info', response.data)
            self.assertIn('download_url', response.data['download_info'])
            self.assertIn('expires_at', response.data['download_info'])
    
    def test_report_customization_workflow(self):
        """Test report customization workflow"""
        with patch('analytics.services.report_generator.ReportGenerator.customize_report') as mock_customize:
            mock_customize.return_value = {
                'success': True,
                'report_id': self.report_id,
                'status': 'customizing',
                'customization_applied': {
                    'sections': {
                        'executive_summary': {
                            'include': True,
                            'custom_title': 'Executive Summary',
                            'custom_content': 'Custom executive summary content'
                        },
                        'data_overview': {
                            'include': True,
                            'custom_title': 'Data Overview',
                            'include_tables': True,
                            'include_charts': False
                        },
                        'analysis_results': {
                            'include': True,
                            'custom_title': 'Analysis Results',
                            'include_llm_interpretations': True,
                            'include_charts': True
                        },
                        'recommendations': {
                            'include': True,
                            'custom_title': 'Recommendations',
                            'custom_recommendations': [
                                'Custom recommendation 1',
                                'Custom recommendation 2'
                            ]
                        }
                    },
                    'formatting': {
                        'font_size': 12,
                        'line_spacing': 1.5,
                        'margins': 'normal',
                        'header_footer': True
                    },
                    'branding': {
                        'company_logo': '/media/logos/company_logo.png',
                        'color_scheme': 'corporate_blue',
                        'footer_text': 'Confidential - Internal Use Only'
                    }
                }
            }
            
            response = self.client.post(f'/api/reports/{self.report_id}/customize/', {
                'sections': {
                    'executive_summary': {
                        'include': True,
                        'custom_title': 'Executive Summary'
                    },
                    'data_overview': {
                        'include': True,
                        'include_charts': False
                    }
                },
                'formatting': {
                    'font_size': 12,
                    'line_spacing': 1.5
                },
                'branding': {
                    'company_logo': '/media/logos/company_logo.png',
                    'color_scheme': 'corporate_blue'
                }
            }, format='json')
            
            # Verify customization
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('customization_applied', response.data)
            self.assertIn('sections', response.data['customization_applied'])
            self.assertIn('formatting', response.data['customization_applied'])
            self.assertIn('branding', response.data['customization_applied'])
    
    def test_report_status_tracking_workflow(self):
        """Test report status tracking workflow"""
        with patch('analytics.services.report_generator.ReportGenerator.get_report_status') as mock_status:
            mock_status.return_value = {
                'report_id': self.report_id,
                'status': 'compiling',
                'progress_percentage': 75,
                'current_step': 'compilation',
                'steps_completed': [
                    {
                        'step': 'initiation',
                        'status': 'completed',
                        'completion_time': '2025-09-23T15:00:00Z'
                    },
                    {
                        'step': 'content_collection',
                        'status': 'completed',
                        'completion_time': '2025-09-23T15:02:00Z'
                    },
                    {
                        'step': 'template_processing',
                        'status': 'completed',
                        'completion_time': '2025-09-23T15:05:00Z'
                    }
                ],
                'current_step_details': {
                    'step': 'compilation',
                    'progress': 75,
                    'estimated_completion': '2025-09-23T15:08:00Z',
                    'details': 'Compiling report sections and applying formatting'
                },
                'remaining_steps': [
                    {
                        'step': 'quality_checks',
                        'estimated_time': 30
                    },
                    {
                        'step': 'finalization',
                        'estimated_time': 15
                    }
                ],
                'estimated_total_time': 480,
                'elapsed_time': 360
            }
            
            response = self.client.get(f'/api/reports/{self.report_id}/status/')
            
            # Verify status tracking
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('progress_percentage', response.data)
            self.assertIn('current_step', response.data)
            self.assertIn('steps_completed', response.data)
            self.assertIn('remaining_steps', response.data)
            self.assertEqual(response.data['progress_percentage'], 75)
    
    def test_report_error_handling_workflow(self):
        """Test report error handling workflow"""
        with patch('analytics.services.report_generator.ReportGenerator.handle_error') as mock_handle_error:
            mock_handle_error.return_value = {
                'success': True,
                'report_id': self.report_id,
                'error_handled': True,
                'error_details': {
                    'error_type': 'template_processing_failed',
                    'error_message': 'Template file corrupted',
                    'step': 'template_processing',
                    'timestamp': '2025-09-23T15:05:00Z'
                },
                'recovery_action': 'use_fallback_template',
                'recovery_results': {
                    'fallback_template_used': 'basic',
                    'processing_continued': True,
                    'quality_impact': 'minimal'
                },
                'updated_status': 'processing',
                'estimated_delay': 60
            }
            
            response = self.client.post(f'/api/reports/{self.report_id}/error/', {
                'error_type': 'template_processing_failed',
                'error_message': 'Template file corrupted',
                'step': 'template_processing'
            }, format='json')
            
            # Verify error handling
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('error_handled', response.data)
            self.assertIn('recovery_action', response.data)
            self.assertIn('recovery_results', response.data)
            self.assertTrue(response.data['error_handled'])
    
    def test_report_workflow_integration(self):
        """Test complete report generation workflow integration"""
        # Initiate report
        with patch('analytics.services.report_generator.ReportGenerator.initiate_report') as mock_initiate:
            mock_initiate.return_value = {
                'success': True,
                'report_id': self.report_id,
                'status': 'initiated',
                'report_config': {
                    'title': 'Data Analysis Report',
                    'sections': ['executive_summary', 'analysis_results'],
                    'format': 'docx'
                },
                'estimated_completion_time': 120
            }
            
            initiate_response = self.client.post('/api/reports/generate/', {
                'session_id': self.session_id,
                'report_config': {
                    'title': 'Data Analysis Report',
                    'sections': ['executive_summary', 'analysis_results'],
                    'format': 'docx'
                }
            }, format='json')
            
            self.assertEqual(initiate_response.status_code, status.HTTP_201_CREATED)
            
            # Collect content
            with patch('analytics.services.report_generator.ReportGenerator.collect_content') as mock_collect:
                mock_collect.return_value = {
                    'success': True,
                    'report_id': self.report_id,
                    'status': 'collecting',
                    'content_collection': {
                        'analysis_results': [
                            {
                                'analysis_id': 1,
                                'tool_name': 'descriptive_stats',
                                'summary': 'Statistics calculated'
                            }
                        ]
                    }
                }
                
                collect_response = self.client.post(f'/api/reports/{self.report_id}/collect/', {
                    'include_analysis_results': True
                }, format='json')
                
                self.assertEqual(collect_response.status_code, status.HTTP_200_OK)
                
                # Compile report
                with patch('analytics.services.report_generator.ReportGenerator.compile_report') as mock_compile:
                    mock_compile.return_value = {
                        'success': True,
                        'report_id': self.report_id,
                        'status': 'completed',
                        'compilation_results': {
                            'output_file': {
                                'filename': 'report.docx',
                                'url': '/api/reports/123456789/download/'
                            }
                        }
                    }
                    
                    compile_response = self.client.post(f'/api/reports/{self.report_id}/compile/', {
                        'output_format': 'docx'
                    }, format='json')
                    
                    self.assertEqual(compile_response.status_code, status.HTTP_200_OK)
                    self.assertEqual(compile_response.data['status'], 'completed')
