"""
Integration Test: Three-Panel UI Interaction (T022)
Tests the complete three-panel UI interaction workflow
"""

import pytest
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestThreePanelUIWorkflow(TestCase):
    """Integration tests for three-panel UI interaction workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock session and dataset
        self.session_id = 'sess_123456789'
        self.dataset_id = 1
        self.dataset_name = "Test Dataset"
    
    def test_tools_panel_tool_selection_workflow(self):
        """Test tools panel tool selection workflow"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_all_tools') as mock_get_tools:
            mock_get_tools.return_value = [
                {
                    'tool_id': 'descriptive_stats',
                    'name': 'Descriptive Statistics',
                    'description': 'Calculate basic descriptive statistics',
                    'category': 'statistical',
                    'parameters': [
                        {
                            'name': 'columns',
                            'type': 'array',
                            'required': True,
                            'description': 'List of numeric columns to analyze'
                        }
                    ],
                    'output_types': ['table', 'chart'],
                    'estimated_time': 2.5,
                    'complexity': 'low',
                    'compatible_with_dataset': True
                },
                {
                    'tool_id': 'correlation_matrix',
                    'name': 'Correlation Matrix',
                    'description': 'Calculate correlation matrix',
                    'category': 'statistical',
                    'parameters': [
                        {
                            'name': 'columns',
                            'type': 'array',
                            'required': True,
                            'description': 'List of numeric columns for correlation'
                        }
                    ],
                    'output_types': ['table', 'heatmap'],
                    'estimated_time': 3.0,
                    'complexity': 'medium',
                    'compatible_with_dataset': True
                }
            ]
            
            response = self.client.get('/api/tools/')
            
            # Verify tools panel data
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('tools', response.data)
            self.assertEqual(len(response.data['tools']), 2)
            
            # Verify tool compatibility
            for tool in response.data['tools']:
                self.assertTrue(tool['compatible_with_dataset'])
                self.assertIn('tool_id', tool)
                self.assertIn('parameters', tool)
                self.assertIn('output_types', tool)
    
    def test_tools_panel_parameter_configuration_workflow(self):
        """Test tools panel parameter configuration workflow"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_tool_parameters') as mock_get_params:
            mock_get_params.return_value = {
                'tool_id': 'descriptive_stats',
                'parameters': [
                    {
                        'name': 'columns',
                        'type': 'array',
                        'required': True,
                        'description': 'List of numeric columns to analyze',
                        'options': ['age', 'salary'],
                        'default': ['age', 'salary']
                    },
                    {
                        'name': 'include_charts',
                        'type': 'boolean',
                        'required': False,
                        'description': 'Include visualization charts',
                        'default': True
                    },
                    {
                        'name': 'statistics',
                        'type': 'array',
                        'required': False,
                        'description': 'Statistics to calculate',
                        'options': ['mean', 'median', 'std', 'min', 'max'],
                        'default': ['mean', 'std']
                    }
                ],
                'parameter_validation': {
                    'columns': {
                        'min_selections': 1,
                        'max_selections': 10,
                        'data_type_requirements': ['numeric']
                    }
                }
            }
            
            response = self.client.get(f'/api/tools/descriptive_stats/parameters/')
            
            # Verify parameter configuration
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('parameters', response.data)
            self.assertIn('parameter_validation', response.data)
            self.assertEqual(len(response.data['parameters']), 3)
            
            # Verify parameter options
            columns_param = next(p for p in response.data['parameters'] if p['name'] == 'columns')
            self.assertIn('options', columns_param)
            self.assertIn('age', columns_param['options'])
            self.assertIn('salary', columns_param['options'])
    
    def test_dashboard_panel_analysis_execution_workflow(self):
        """Test dashboard panel analysis execution workflow"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'analysis_id': 1,
                'tool_name': 'descriptive_stats',
                'status': 'completed',
                'results': {
                    'summary': 'Descriptive statistics calculated successfully',
                    'tables': [
                        {
                            'title': 'Summary Statistics',
                            'data': [
                                {'column': 'age', 'mean': 30.0, 'std': 5.0, 'min': 25, 'max': 35},
                                {'column': 'salary', 'mean': 60000.0, 'std': 10000.0, 'min': 50000, 'max': 70000}
                            ]
                        }
                    ],
                    'charts': [
                        {
                            'title': 'Age Distribution',
                            'type': 'histogram',
                            'image_url': '/media/charts/age_histogram.png',
                            'image_data': 'base64_encoded_image_data'
                        }
                    ]
                },
                'execution_time': 2.5,
                'created_at': '2025-09-23T15:00:00Z'
            }
            
            response = self.client.post('/api/analysis/execute/', {
                'session_id': self.session_id,
                'tool_name': 'descriptive_stats',
                'parameters': {
                    'columns': ['age', 'salary'],
                    'include_charts': True
                }
            }, format='json')
            
            # Verify analysis execution
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('results', response.data)
            self.assertIn('tables', response.data['results'])
            self.assertIn('charts', response.data['results'])
            self.assertEqual(len(response.data['results']['tables']), 1)
            self.assertEqual(len(response.data['results']['charts']), 1)
    
    def test_dashboard_panel_results_display_workflow(self):
        """Test dashboard panel results display workflow"""
        with patch('analytics.services.analysis_executor.AnalysisExecutor.get_analysis_results') as mock_get_results:
            mock_get_results.return_value = {
                'analysis_id': 1,
                'tool_name': 'descriptive_stats',
                'status': 'completed',
                'results': {
                    'summary': 'Descriptive statistics calculated',
                    'tables': [
                        {
                            'title': 'Summary Statistics',
                            'data': [
                                {'column': 'age', 'mean': 30.0, 'std': 5.0, 'min': 25, 'max': 35},
                                {'column': 'salary', 'mean': 60000.0, 'std': 10000.0, 'min': 50000, 'max': 70000}
                            ],
                            'format': 'table',
                            'interactive': True
                        }
                    ],
                    'charts': [
                        {
                            'title': 'Age Distribution',
                            'type': 'histogram',
                            'image_url': '/media/charts/age_histogram.png',
                            'image_data': 'base64_encoded_image_data',
                            'interactive': False
                        }
                    ]
                },
                'display_options': {
                    'table_format': 'responsive',
                    'chart_interaction': 'hover',
                    'export_formats': ['png', 'svg', 'pdf']
                }
            }
            
            response = self.client.get(f'/api/analysis/results/1/')
            
            # Verify results display
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('results', response.data)
            self.assertIn('display_options', response.data)
            self.assertIn('tables', response.data['results'])
            self.assertIn('charts', response.data['results'])
            
            # Verify display options
            self.assertIn('table_format', response.data['display_options'])
            self.assertIn('export_formats', response.data['display_options'])
    
    def test_chat_panel_ai_interaction_workflow(self):
        """Test chat panel AI interaction workflow"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'message_id': 'msg_123456789',
                'user_message': 'What does the age distribution tell us?',
                'assistant_response': 'The age distribution shows a normal distribution with a mean of 30 years and standard deviation of 5 years. This indicates that most employees are in their late 20s to early 30s, with relatively few outliers.',
                'tokens_used': 45,
                'cost': 0.000225,
                'created_at': '2025-09-23T15:00:00Z',
                'context_used': True,
                'analysis_context': {
                    'analysis_id': 1,
                    'tool_name': 'descriptive_stats',
                    'results_summary': 'Age statistics calculated'
                }
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'What does the age distribution tell us?',
                'include_context': True,
                'analysis_context': {
                    'analysis_id': 1,
                    'tool_name': 'descriptive_stats'
                }
            }, format='json')
            
            # Verify AI interaction
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('assistant_response', response.data)
            self.assertIn('analysis_context', response.data)
            self.assertIn('tokens_used', response.data)
            self.assertTrue(response.data['context_used'])
    
    def test_chat_panel_context_management_workflow(self):
        """Test chat panel context management workflow"""
        with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
            mock_process.return_value = {
                'success': True,
                'message_id': 'msg_context_test',
                'user_message': 'Can you explain this correlation?',
                'assistant_response': 'Based on the correlation analysis, there is a strong positive correlation (r=0.75) between age and salary. This suggests that older employees tend to have higher salaries, which is typical in most organizations.',
                'tokens_used': 67,
                'cost': 0.000335,
                'created_at': '2025-09-23T15:00:00Z',
                'context_used': True,
                'context_info': {
                    'previous_messages': 3,
                    'analysis_results_included': 2,
                    'context_size': 10,
                    'context_cached': True
                }
            }
            
            response = self.client.post('/api/chat/messages/', {
                'session_id': self.session_id,
                'message': 'Can you explain this correlation?',
                'include_context': True
            }, format='json')
            
            # Verify context management
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('context_info', response.data)
            self.assertIn('previous_messages', response.data['context_info'])
            self.assertIn('analysis_results_included', response.data['context_info'])
            self.assertTrue(response.data['context_info']['context_cached'])
    
    def test_three_panel_synchronization_workflow(self):
        """Test three-panel synchronization workflow"""
        # Simulate tool selection in tools panel
        with patch('analytics.services.tool_registry.ToolRegistry.get_tool_parameters') as mock_get_params:
            mock_get_params.return_value = {
                'tool_id': 'correlation_matrix',
                'parameters': [
                    {
                        'name': 'columns',
                        'type': 'array',
                        'required': True,
                        'options': ['age', 'salary'],
                        'default': ['age', 'salary']
                    }
                ]
            }
            
            # Tool selection
            tool_response = self.client.get(f'/api/tools/correlation_matrix/parameters/')
            self.assertEqual(tool_response.status_code, status.HTTP_200_OK)
            
            # Analysis execution in dashboard panel
            with patch('analytics.services.analysis_executor.AnalysisExecutor.execute_analysis') as mock_execute:
                mock_execute.return_value = {
                    'success': True,
                    'analysis_id': 2,
                    'tool_name': 'correlation_matrix',
                    'status': 'completed',
                    'results': {
                        'summary': 'Correlation matrix calculated',
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
                        ]
                    }
                }
                
                # Analysis execution
                analysis_response = self.client.post('/api/analysis/execute/', {
                    'session_id': self.session_id,
                    'tool_name': 'correlation_matrix',
                    'parameters': {
                        'columns': ['age', 'salary']
                    }
                }, format='json')
                
                self.assertEqual(analysis_response.status_code, status.HTTP_200_OK)
                
                # AI interpretation in chat panel
                with patch('analytics.services.llm_processor.LLMProcessor.process_message') as mock_process:
                    mock_process.return_value = {
                        'success': True,
                        'message_id': 'msg_sync_test',
                        'user_message': 'What does this correlation mean?',
                        'assistant_response': 'The correlation of 0.75 between age and salary indicates a strong positive relationship. This means that as employees get older, their salaries tend to increase.',
                        'tokens_used': 52,
                        'cost': 0.000260,
                        'created_at': '2025-09-23T15:00:00Z',
                        'context_used': True,
                        'analysis_context': {
                            'analysis_id': 2,
                            'tool_name': 'correlation_matrix',
                            'results_summary': 'Correlation matrix calculated'
                        }
                    }
                    
                    # AI interpretation
                    chat_response = self.client.post('/api/chat/messages/', {
                        'session_id': self.session_id,
                        'message': 'What does this correlation mean?',
                        'include_context': True,
                        'analysis_context': {
                            'analysis_id': 2,
                            'tool_name': 'correlation_matrix'
                        }
                    }, format='json')
                    
                    self.assertEqual(chat_response.status_code, status.HTTP_200_OK)
                    self.assertIn('analysis_context', chat_response.data)
    
    def test_panel_resizing_and_layout_workflow(self):
        """Test panel resizing and layout workflow"""
        with patch('analytics.services.ui_manager.UIManager.update_panel_layout') as mock_update_layout:
            mock_update_layout.return_value = {
                'success': True,
                'layout_updated': True,
                'new_layout': {
                    'tools_panel_width': 300,
                    'dashboard_panel_width': 800,
                    'chat_panel_width': 350,
                    'layout_saved': True
                },
                'user_preferences': {
                    'default_layout': 'balanced',
                    'auto_save_layout': True,
                    'responsive_mode': True
                }
            }
            
            response = self.client.post('/api/ui/layout/', {
                'tools_panel_width': 300,
                'dashboard_panel_width': 800,
                'chat_panel_width': 350,
                'save_preferences': True
            }, format='json')
            
            # Verify layout update
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('new_layout', response.data)
            self.assertIn('user_preferences', response.data)
            self.assertTrue(response.data['layout_updated'])
    
    def test_panel_state_persistence_workflow(self):
        """Test panel state persistence workflow"""
        with patch('analytics.services.ui_manager.UIManager.save_panel_state') as mock_save_state:
            mock_save_state.return_value = {
                'success': True,
                'state_saved': True,
                'panel_states': {
                    'tools_panel': {
                        'selected_tool': 'descriptive_stats',
                        'expanded_sections': ['statistical', 'advanced'],
                        'filter_applied': 'compatible_only'
                    },
                    'dashboard_panel': {
                        'active_analysis': 1,
                        'view_mode': 'split',
                        'chart_preferences': {
                            'default_type': 'bar',
                            'interactive': True
                        }
                    },
                    'chat_panel': {
                        'message_history': 10,
                        'context_enabled': True,
                        'auto_scroll': True
                    }
                }
            }
            
            response = self.client.post('/api/ui/state/', {
                'session_id': self.session_id,
                'panel_states': {
                    'tools_panel': {
                        'selected_tool': 'descriptive_stats',
                        'expanded_sections': ['statistical', 'advanced']
                    },
                    'dashboard_panel': {
                        'active_analysis': 1,
                        'view_mode': 'split'
                    },
                    'chat_panel': {
                        'message_history': 10,
                        'context_enabled': True
                    }
                }
            }, format='json')
            
            # Verify state persistence
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('panel_states', response.data)
            self.assertTrue(response.data['state_saved'])
            self.assertIn('tools_panel', response.data['panel_states'])
            self.assertIn('dashboard_panel', response.data['panel_states'])
            self.assertIn('chat_panel', response.data['panel_states'])
    
    def test_three_panel_error_handling_workflow(self):
        """Test three-panel error handling workflow"""
        # Simulate error in tools panel
        with patch('analytics.services.tool_registry.ToolRegistry.get_all_tools') as mock_get_tools:
            mock_get_tools.return_value = {
                'success': False,
                'error': 'Tool registry unavailable',
                'error_code': 'TOOL_REGISTRY_ERROR',
                'fallback_tools': [
                    {
                        'tool_id': 'basic_stats',
                        'name': 'Basic Statistics',
                        'description': 'Fallback tool for basic statistics',
                        'category': 'statistical',
                        'parameters': [],
                        'output_types': ['table'],
                        'estimated_time': 1.0,
                        'complexity': 'low'
                    }
                ]
            }
            
            response = self.client.get('/api/tools/')
            
            # Verify error handling
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertIn('error', response.data)
            self.assertIn('fallback_tools', response.data)
            self.assertEqual(len(response.data['fallback_tools']), 1)
    
    def test_three_panel_performance_optimization_workflow(self):
        """Test three-panel performance optimization workflow"""
        with patch('analytics.services.ui_manager.UIManager.optimize_panel_performance') as mock_optimize:
            mock_optimize.return_value = {
                'success': True,
                'performance_optimized': True,
                'optimization_results': {
                    'tools_panel': {
                        'lazy_loading_enabled': True,
                        'cached_tools': 15,
                        'load_time_reduction': '40%'
                    },
                    'dashboard_panel': {
                        'virtual_scrolling_enabled': True,
                        'chart_lazy_loading': True,
                        'memory_usage_reduction': '30%'
                    },
                    'chat_panel': {
                        'message_pagination': True,
                        'context_caching': True,
                        'response_time_improvement': '25%'
                    }
                },
                'overall_improvement': {
                    'page_load_time': '2.1s',
                    'memory_usage': '45MB',
                    'cpu_usage': '15%'
                }
            }
            
            response = self.client.post('/api/ui/optimize/', {
                'session_id': self.session_id,
                'optimization_level': 'aggressive'
            }, format='json')
            
            # Verify performance optimization
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('optimization_results', response.data)
            self.assertIn('overall_improvement', response.data)
            self.assertTrue(response.data['performance_optimized'])
