"""
Integration Test: Agentic AI Execution Workflow (T023)
Tests the complete agentic AI execution workflow
"""

import pytest
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestAgenticAIWorkflow(TestCase):
    """Integration tests for agentic AI execution workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock dataset and session
        self.dataset_id = 1
        self.session_id = 'sess_123456789'
        self.goal = 'Analyze the relationship between age and salary in the dataset'
    
    def test_agentic_ai_planning_workflow(self):
        """Test agentic AI planning workflow"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': True,
                'agent_run_id': 1,
                'status': 'planning',
                'correlation_id': 'agent_123456789',
                'estimated_completion_time': 300,
                'progress_url': '/api/agent/run/1/status/',
                'goal': self.goal,
                'planning_results': {
                    'analysis_plan': [
                        {
                            'step': 1,
                            'action': 'descriptive_stats',
                            'description': 'Calculate basic descriptive statistics for age and salary',
                            'estimated_time': 30,
                            'dependencies': []
                        },
                        {
                            'step': 2,
                            'action': 'correlation_matrix',
                            'description': 'Calculate correlation between age and salary',
                            'estimated_time': 45,
                            'dependencies': [1]
                        },
                        {
                            'step': 3,
                            'action': 'regression_analysis',
                            'description': 'Perform linear regression analysis',
                            'estimated_time': 60,
                            'dependencies': [1, 2]
                        },
                        {
                            'step': 4,
                            'action': 'interpretation',
                            'description': 'Generate comprehensive interpretation',
                            'estimated_time': 90,
                            'dependencies': [1, 2, 3]
                        }
                    ],
                    'total_estimated_time': 225,
                    'complexity_score': 0.7,
                    'confidence_score': 0.85
                }
            }
            
            response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal,
                'constraints': {
                    'max_steps': 10,
                    'max_cost': 5000,
                    'max_time': 1800
                }
            }, format='json')
            
            # Verify planning workflow
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('planning_results', response.data)
            self.assertIn('analysis_plan', response.data['planning_results'])
            self.assertEqual(len(response.data['planning_results']['analysis_plan']), 4)
            self.assertIn('confidence_score', response.data['planning_results'])
    
    def test_agentic_ai_execution_workflow(self):
        """Test agentic AI execution workflow"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.execute_agent_step') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'step_id': 1,
                'agent_run_id': 1,
                'step_number': 1,
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
                            'image_url': '/media/charts/age_histogram.png'
                        }
                    ]
                },
                'execution_time': 2.5,
                'token_usage': 150,
                'confidence_score': 0.9,
                'next_action': 'correlation_matrix'
            }
            
            response = self.client.post('/api/agent/run/1/execute/', {
                'step_number': 1,
                'parameters': {
                    'columns': ['age', 'salary'],
                    'include_charts': True
                }
            }, format='json')
            
            # Verify execution workflow
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('results', response.data)
            self.assertIn('next_action', response.data)
            self.assertIn('confidence_score', response.data)
            self.assertEqual(response.data['tool_name'], 'descriptive_stats')
    
    def test_agentic_ai_progress_tracking_workflow(self):
        """Test agentic AI progress tracking workflow"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.get_agent_progress') as mock_get_progress:
            mock_get_progress.return_value = {
                'agent_run_id': 1,
                'status': 'running',
                'current_step': 2,
                'total_steps': 4,
                'progress_percentage': 50,
                'elapsed_time': 120,
                'estimated_remaining_time': 180,
                'current_action': 'correlation_matrix',
                'completed_steps': [
                    {
                        'step': 1,
                        'action': 'descriptive_stats',
                        'status': 'completed',
                        'execution_time': 30,
                        'confidence_score': 0.9
                    }
                ],
                'next_steps': [
                    {
                        'step': 2,
                        'action': 'correlation_matrix',
                        'status': 'running',
                        'estimated_time': 45
                    },
                    {
                        'step': 3,
                        'action': 'regression_analysis',
                        'status': 'pending',
                        'estimated_time': 60
                    }
                ],
                'resource_usage': {
                    'tokens_used': 300,
                    'tokens_remaining': 4700,
                    'memory_usage_mb': 45,
                    'cpu_usage_percent': 25
                }
            }
            
            response = self.client.get('/api/agent/run/1/status/')
            
            # Verify progress tracking
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('progress_percentage', response.data)
            self.assertIn('current_action', response.data)
            self.assertIn('completed_steps', response.data)
            self.assertIn('next_steps', response.data)
            self.assertIn('resource_usage', response.data)
            self.assertEqual(response.data['progress_percentage'], 50)
    
    def test_agentic_ai_adaptive_planning_workflow(self):
        """Test agentic AI adaptive planning workflow"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.adapt_plan') as mock_adapt:
            mock_adapt.return_value = {
                'success': True,
                'plan_adapted': True,
                'adaptation_reason': 'Strong correlation detected, adding advanced analysis',
                'original_plan': [
                    {'step': 1, 'action': 'descriptive_stats'},
                    {'step': 2, 'action': 'correlation_matrix'},
                    {'step': 3, 'action': 'interpretation'}
                ],
                'adapted_plan': [
                    {'step': 1, 'action': 'descriptive_stats'},
                    {'step': 2, 'action': 'correlation_matrix'},
                    {'step': 3, 'action': 'regression_analysis', 'added': True},
                    {'step': 4, 'action': 'outlier_detection', 'added': True},
                    {'step': 5, 'action': 'interpretation'}
                ],
                'adaptation_confidence': 0.8,
                'estimated_time_adjustment': 120
            }
            
            response = self.client.post('/api/agent/run/1/adapt/', {
                'adaptation_trigger': 'strong_correlation_detected',
                'current_results': {
                    'correlation': 0.85,
                    'significance': 0.001
                }
            }, format='json')
            
            # Verify adaptive planning
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('plan_adapted', response.data)
            self.assertIn('adaptation_reason', response.data)
            self.assertIn('adapted_plan', response.data)
            self.assertTrue(response.data['plan_adapted'])
    
    def test_agentic_ai_error_recovery_workflow(self):
        """Test agentic AI error recovery workflow"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.handle_error') as mock_handle_error:
            mock_handle_error.return_value = {
                'success': True,
                'error_recovered': True,
                'error_details': {
                    'error_type': 'tool_execution_failed',
                    'error_message': 'Insufficient data for regression analysis',
                    'step_number': 3,
                    'tool_name': 'regression_analysis'
                },
                'recovery_action': 'skip_regression_analysis',
                'recovery_plan': [
                    {
                        'step': 3,
                        'action': 'regression_analysis',
                        'status': 'skipped',
                        'reason': 'Insufficient data'
                    },
                    {
                        'step': 4,
                        'action': 'interpretation',
                        'status': 'modified',
                        'modification': 'Focus on correlation analysis only'
                    }
                ],
                'recovery_confidence': 0.7,
                'estimated_time_saved': 60
            }
            
            response = self.client.post('/api/agent/run/1/recover/', {
                'error_type': 'tool_execution_failed',
                'error_message': 'Insufficient data for regression analysis',
                'step_number': 3
            }, format='json')
            
            # Verify error recovery
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('error_recovered', response.data)
            self.assertIn('recovery_action', response.data)
            self.assertIn('recovery_plan', response.data)
            self.assertTrue(response.data['error_recovered'])
    
    def test_agentic_ai_human_feedback_workflow(self):
        """Test agentic AI human feedback workflow"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.process_human_feedback') as mock_process_feedback:
            mock_process_feedback.return_value = {
                'success': True,
                'feedback_processed': True,
                'feedback_type': 'guidance',
                'feedback_content': 'Focus more on salary distribution analysis',
                'agent_response': 'I will adjust the analysis plan to include more detailed salary distribution analysis.',
                'plan_adjustments': [
                    {
                        'step': 2,
                        'action': 'salary_distribution',
                        'added': True,
                        'reason': 'Human feedback requested'
                    }
                ],
                'feedback_confidence': 0.9,
                'next_actions': [
                    'Continue with salary distribution analysis',
                    'Provide detailed salary insights'
                ]
            }
            
            response = self.client.post('/api/agent/run/1/feedback/', {
                'feedback_type': 'guidance',
                'feedback_content': 'Focus more on salary distribution analysis',
                'step_number': 2
            }, format='json')
            
            # Verify human feedback processing
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('feedback_processed', response.data)
            self.assertIn('agent_response', response.data)
            self.assertIn('plan_adjustments', response.data)
            self.assertTrue(response.data['feedback_processed'])
    
    def test_agentic_ai_constraint_monitoring_workflow(self):
        """Test agentic AI constraint monitoring workflow"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.check_constraints') as mock_check_constraints:
            mock_check_constraints.return_value = {
                'constraints_satisfied': True,
                'constraint_status': {
                    'max_steps': {
                        'limit': 10,
                        'used': 3,
                        'remaining': 7,
                        'status': 'ok'
                    },
                    'max_cost': {
                        'limit': 5000,
                        'used': 1200,
                        'remaining': 3800,
                        'status': 'ok'
                    },
                    'max_time': {
                        'limit': 1800,
                        'used': 300,
                        'remaining': 1500,
                        'status': 'ok'
                    }
                },
                'warnings': [],
                'recommendations': [
                    'Continue with current plan',
                    'Consider optimizing token usage for remaining steps'
                ]
            }
            
            response = self.client.get('/api/agent/run/1/constraints/')
            
            # Verify constraint monitoring
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('constraints_satisfied', response.data)
            self.assertIn('constraint_status', response.data)
            self.assertIn('recommendations', response.data)
            self.assertTrue(response.data['constraints_satisfied'])
    
    def test_agentic_ai_completion_workflow(self):
        """Test agentic AI completion workflow"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.complete_agent_run') as mock_complete:
            mock_complete.return_value = {
                'success': True,
                'agent_run_id': 1,
                'status': 'completed',
                'completion_summary': {
                    'total_steps': 4,
                    'completed_steps': 4,
                    'failed_steps': 0,
                    'total_execution_time': 225,
                    'total_token_usage': 1200,
                    'final_confidence_score': 0.85
                },
                'final_results': {
                    'summary': 'Analysis completed successfully. Strong positive correlation (r=0.75) found between age and salary.',
                    'key_findings': [
                        'Age and salary show strong positive correlation (r=0.75)',
                        'Salary increases by approximately $2,000 per year of age',
                        'The relationship is statistically significant (p<0.001)'
                    ],
                    'recommendations': [
                        'Consider age-based salary bands for fair compensation',
                        'Investigate factors beyond age that influence salary',
                        'Monitor for potential age discrimination in salary practices'
                    ],
                    'generated_artifacts': [
                        {
                            'type': 'table',
                            'title': 'Correlation Analysis Results',
                            'url': '/media/results/correlation_results.csv'
                        },
                        {
                            'type': 'chart',
                            'title': 'Age vs Salary Scatter Plot',
                            'url': '/media/charts/age_salary_scatter.png'
                        },
                        {
                            'type': 'report',
                            'title': 'Comprehensive Analysis Report',
                            'url': '/media/reports/analysis_report.pdf'
                        }
                    ]
                },
                'user_feedback_request': {
                    'question': 'Was this analysis helpful?',
                    'options': ['Very helpful', 'Somewhat helpful', 'Not helpful'],
                    'feedback_url': '/api/agent/run/1/feedback/'
                }
            }
            
            response = self.client.post('/api/agent/run/1/complete/', {
                'final_interpretation': 'Strong positive correlation between age and salary'
            }, format='json')
            
            # Verify completion workflow
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('completion_summary', response.data)
            self.assertIn('final_results', response.data)
            self.assertIn('generated_artifacts', response.data['final_results'])
            self.assertEqual(response.data['status'], 'completed')
    
    def test_agentic_ai_pause_resume_workflow(self):
        """Test agentic AI pause and resume workflow"""
        # Test pause
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.pause_agent_run') as mock_pause:
            mock_pause.return_value = {
                'success': True,
                'agent_run_id': 1,
                'status': 'paused',
                'pause_reason': 'User requested pause',
                'pause_time': '2025-09-23T15:30:00Z',
                'resume_info': {
                    'can_resume': True,
                    'resume_url': '/api/agent/run/1/resume/',
                    'estimated_resume_time': '2025-09-23T15:35:00Z'
                }
            }
            
            pause_response = self.client.post('/api/agent/run/1/pause/', {
                'reason': 'User requested pause'
            }, format='json')
            
            self.assertEqual(pause_response.status_code, status.HTTP_200_OK)
            self.assertEqual(pause_response.data['status'], 'paused')
            
            # Test resume
            with patch('analytics.services.agentic_ai_controller.AgenticAIController.resume_agent_run') as mock_resume:
                mock_resume.return_value = {
                    'success': True,
                    'agent_run_id': 1,
                    'status': 'running',
                    'resume_time': '2025-09-23T15:35:00Z',
                    'current_step': 2,
                    'resume_plan': [
                        {'step': 2, 'action': 'correlation_matrix', 'status': 'running'},
                        {'step': 3, 'action': 'regression_analysis', 'status': 'pending'}
                    ]
                }
                
                resume_response = self.client.post('/api/agent/run/1/resume/')
                
                self.assertEqual(resume_response.status_code, status.HTTP_200_OK)
                self.assertEqual(resume_response.data['status'], 'running')
    
    def test_agentic_ai_cancellation_workflow(self):
        """Test agentic AI cancellation workflow"""
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.cancel_agent_run') as mock_cancel:
            mock_cancel.return_value = {
                'success': True,
                'agent_run_id': 1,
                'status': 'cancelled',
                'cancellation_reason': 'User requested cancellation',
                'cancellation_time': '2025-09-23T15:40:00Z',
                'cancellation_summary': {
                    'steps_completed': 2,
                    'steps_cancelled': 2,
                    'partial_results': [
                        {
                            'step': 1,
                            'action': 'descriptive_stats',
                            'status': 'completed',
                            'results_available': True
                        },
                        {
                            'step': 2,
                            'action': 'correlation_matrix',
                            'status': 'completed',
                            'results_available': True
                        }
                    ],
                    'cleanup_performed': True,
                    'resources_released': True
                }
            }
            
            response = self.client.post('/api/agent/run/1/cancel/', {
                'reason': 'User requested cancellation'
            }, format='json')
            
            # Verify cancellation workflow
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'cancelled')
            self.assertIn('cancellation_summary', response.data)
            self.assertIn('partial_results', response.data['cancellation_summary'])
            self.assertTrue(response.data['cancellation_summary']['cleanup_performed'])
    
    def test_agentic_ai_workflow_integration(self):
        """Test complete agentic AI workflow integration"""
        # Start agent run
        with patch('analytics.services.agentic_ai_controller.AgenticAIController.start_agent_run') as mock_start:
            mock_start.return_value = {
                'success': True,
                'agent_run_id': 1,
                'status': 'planning',
                'correlation_id': 'agent_integration_test',
                'estimated_completion_time': 300,
                'progress_url': '/api/agent/run/1/status/',
                'goal': self.goal
            }
            
            start_response = self.client.post('/api/agent/run/', {
                'dataset_id': self.dataset_id,
                'goal': self.goal
            }, format='json')
            
            self.assertEqual(start_response.status_code, status.HTTP_200_OK)
            
            # Execute steps
            with patch('analytics.services.agentic_ai_controller.AgenticAIController.execute_agent_step') as mock_execute:
                mock_execute.return_value = {
                    'success': True,
                    'step_id': 1,
                    'agent_run_id': 1,
                    'step_number': 1,
                    'tool_name': 'descriptive_stats',
                    'status': 'completed',
                    'results': {'summary': 'Step completed'},
                    'execution_time': 30,
                    'next_action': 'correlation_matrix'
                }
                
                execute_response = self.client.post('/api/agent/run/1/execute/', {
                    'step_number': 1,
                    'parameters': {'columns': ['age', 'salary']}
                }, format='json')
                
                self.assertEqual(execute_response.status_code, status.HTTP_200_OK)
                
                # Complete agent run
                with patch('analytics.services.agentic_ai_controller.AgenticAIController.complete_agent_run') as mock_complete:
                    mock_complete.return_value = {
                        'success': True,
                        'agent_run_id': 1,
                        'status': 'completed',
                        'completion_summary': {
                            'total_steps': 4,
                            'completed_steps': 4,
                            'total_execution_time': 225
                        },
                        'final_results': {
                            'summary': 'Analysis completed successfully',
                            'key_findings': ['Strong correlation found'],
                            'recommendations': ['Consider further analysis']
                        }
                    }
                    
                    complete_response = self.client.post('/api/agent/run/1/complete/', {
                        'final_interpretation': 'Analysis completed'
                    }, format='json')
                    
                    self.assertEqual(complete_response.status_code, status.HTTP_200_OK)
                    self.assertEqual(complete_response.data['status'], 'completed')
