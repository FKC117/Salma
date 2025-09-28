"""
Contract Test: GET /api/tools/ (T017)
Tests the tools listing API endpoint according to the API schema
"""

import pytest
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

class TestToolsGetContract(TestCase):
    """Contract tests for GET /api/tools/ endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_tools_success(self):
        """Test successful tools listing"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_all_tools') as mock_get_tools:
            mock_get_tools.return_value = [
                {
                    'tool_id': 'descriptive_stats',
                    'name': 'Descriptive Statistics',
                    'description': 'Calculate basic descriptive statistics for numeric columns',
                    'category': 'statistical',
                    'parameters': [
                        {
                            'name': 'columns',
                            'type': 'array',
                            'required': True,
                            'description': 'List of numeric columns to analyze'
                        },
                        {
                            'name': 'include_charts',
                            'type': 'boolean',
                            'required': False,
                            'default': True,
                            'description': 'Include visualization charts'
                        }
                    ],
                    'output_types': ['table', 'chart'],
                    'estimated_time': 2.5,
                    'complexity': 'low'
                },
                {
                    'tool_id': 'correlation_matrix',
                    'name': 'Correlation Matrix',
                    'description': 'Calculate correlation matrix between numeric variables',
                    'category': 'statistical',
                    'parameters': [
                        {
                            'name': 'columns',
                            'type': 'array',
                            'required': True,
                            'description': 'List of numeric columns for correlation'
                        },
                        {
                            'name': 'method',
                            'type': 'string',
                            'required': False,
                            'default': 'pearson',
                            'options': ['pearson', 'spearman', 'kendall'],
                            'description': 'Correlation method to use'
                        }
                    ],
                    'output_types': ['table', 'heatmap'],
                    'estimated_time': 3.0,
                    'complexity': 'medium'
                },
                {
                    'tool_id': 'survival_analysis',
                    'name': 'Survival Analysis',
                    'description': 'Perform survival analysis using Kaplan-Meier estimator',
                    'category': 'advanced',
                    'parameters': [
                        {
                            'name': 'time_column',
                            'type': 'string',
                            'required': True,
                            'description': 'Column containing time-to-event data'
                        },
                        {
                            'name': 'event_column',
                            'type': 'string',
                            'required': True,
                            'description': 'Column containing event indicators'
                        },
                        {
                            'name': 'group_column',
                            'type': 'string',
                            'required': False,
                            'description': 'Column for group comparison'
                        }
                    ],
                    'output_types': ['table', 'chart', 'statistics'],
                    'estimated_time': 5.0,
                    'complexity': 'high'
                }
            ]
            
            response = self.client.get('/api/tools/')
            
            # Contract assertions
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('tools', response.data)
            self.assertIn('total_count', response.data)
            self.assertIn('categories', response.data)
            
            # Verify data types
            self.assertIsInstance(response.data['tools'], list)
            self.assertIsInstance(response.data['total_count'], int)
            self.assertIsInstance(response.data['categories'], list)
            
            # Verify tool structure
            tool = response.data['tools'][0]
            required_tool_fields = [
                'tool_id', 'name', 'description', 'category', 
                'parameters', 'output_types', 'estimated_time', 'complexity'
            ]
            
            for field in required_tool_fields:
                self.assertIn(field, tool, f"Missing required tool field: {field}")
            
            # Verify parameter structure
            parameter = tool['parameters'][0]
            required_param_fields = ['name', 'type', 'required', 'description']
            
            for field in required_param_fields:
                self.assertIn(field, parameter, f"Missing required parameter field: {field}")
    
    def test_get_tools_by_category(self):
        """Test tools listing filtered by category"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_tools_by_category') as mock_get_tools:
            mock_get_tools.return_value = [
                {
                    'tool_id': 'descriptive_stats',
                    'name': 'Descriptive Statistics',
                    'description': 'Calculate basic descriptive statistics',
                    'category': 'statistical',
                    'parameters': [],
                    'output_types': ['table'],
                    'estimated_time': 2.5,
                    'complexity': 'low'
                }
            ]
            
            response = self.client.get('/api/tools/?category=statistical')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('tools', response.data)
            self.assertEqual(len(response.data['tools']), 1)
            self.assertEqual(response.data['tools'][0]['category'], 'statistical')
    
    def test_get_tools_by_complexity(self):
        """Test tools listing filtered by complexity"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_tools_by_complexity') as mock_get_tools:
            mock_get_tools.return_value = [
                {
                    'tool_id': 'descriptive_stats',
                    'name': 'Descriptive Statistics',
                    'description': 'Calculate basic descriptive statistics',
                    'category': 'statistical',
                    'parameters': [],
                    'output_types': ['table'],
                    'estimated_time': 2.5,
                    'complexity': 'low'
                }
            ]
            
            response = self.client.get('/api/tools/?complexity=low')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('tools', response.data)
            self.assertEqual(len(response.data['tools']), 1)
            self.assertEqual(response.data['tools'][0]['complexity'], 'low')
    
    def test_get_tools_search(self):
        """Test tools listing with search query"""
        with patch('analytics.services.tool_registry.ToolRegistry.search_tools') as mock_search:
            mock_search.return_value = [
                {
                    'tool_id': 'correlation_matrix',
                    'name': 'Correlation Matrix',
                    'description': 'Calculate correlation matrix between variables',
                    'category': 'statistical',
                    'parameters': [],
                    'output_types': ['table', 'heatmap'],
                    'estimated_time': 3.0,
                    'complexity': 'medium'
                }
            ]
            
            response = self.client.get('/api/tools/?search=correlation')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('tools', response.data)
            self.assertEqual(len(response.data['tools']), 1)
            self.assertIn('correlation', response.data['tools'][0]['name'].lower())
    
    def test_get_tools_pagination(self):
        """Test tools listing with pagination"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_tools_paginated') as mock_get_tools:
            mock_get_tools.return_value = {
                'tools': [
                    {
                        'tool_id': 'descriptive_stats',
                        'name': 'Descriptive Statistics',
                        'description': 'Calculate basic descriptive statistics',
                        'category': 'statistical',
                        'parameters': [],
                        'output_types': ['table'],
                        'estimated_time': 2.5,
                        'complexity': 'low'
                    }
                ],
                'total_count': 25,
                'page': 1,
                'page_size': 10,
                'total_pages': 3
            }
            
            response = self.client.get('/api/tools/?page=1&page_size=10')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('tools', response.data)
            self.assertIn('total_count', response.data)
            self.assertIn('page', response.data)
            self.assertIn('page_size', response.data)
            self.assertIn('total_pages', response.data)
            
            self.assertEqual(response.data['page'], 1)
            self.assertEqual(response.data['page_size'], 10)
            self.assertEqual(response.data['total_pages'], 3)
    
    def test_get_tools_unauthenticated(self):
        """Test tools listing without authentication"""
        client = APIClient()  # No authentication
        
        response = client.get('/api/tools/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_tools_empty_result(self):
        """Test tools listing with no tools available"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_all_tools') as mock_get_tools:
            mock_get_tools.return_value = []
            
            response = self.client.get('/api/tools/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('tools', response.data)
            self.assertEqual(len(response.data['tools']), 0)
            self.assertEqual(response.data['total_count'], 0)
    
    def test_get_tools_with_categories(self):
        """Test tools listing with category information"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_all_tools') as mock_get_tools:
            mock_get_tools.return_value = [
                {
                    'tool_id': 'descriptive_stats',
                    'name': 'Descriptive Statistics',
                    'description': 'Calculate basic descriptive statistics',
                    'category': 'statistical',
                    'parameters': [],
                    'output_types': ['table'],
                    'estimated_time': 2.5,
                    'complexity': 'low'
                }
            ]
        
        with patch('analytics.services.tool_registry.ToolRegistry.get_categories') as mock_get_categories:
            mock_get_categories.return_value = [
                {
                    'name': 'statistical',
                    'display_name': 'Statistical Analysis',
                    'description': 'Basic statistical analysis tools',
                    'tool_count': 5
                },
                {
                    'name': 'advanced',
                    'display_name': 'Advanced Analysis',
                    'description': 'Advanced analytical tools',
                    'tool_count': 3
                }
            ]
            
            response = self.client.get('/api/tools/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('categories', response.data)
            self.assertIsInstance(response.data['categories'], list)
            self.assertEqual(len(response.data['categories']), 2)
            
            category = response.data['categories'][0]
            required_category_fields = ['name', 'display_name', 'description', 'tool_count']
            
            for field in required_category_fields:
                self.assertIn(field, category, f"Missing required category field: {field}")
    
    def test_get_tools_response_schema(self):
        """Test that response matches the expected schema"""
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
                    'tags': ['statistics', 'descriptive', 'numeric'],
                    'version': '1.0',
                    'author': 'Analytics Team'
                }
            ]
        
        with patch('analytics.services.tool_registry.ToolRegistry.get_categories') as mock_get_categories:
            mock_get_categories.return_value = [
                {
                    'name': 'statistical',
                    'display_name': 'Statistical Analysis',
                    'description': 'Basic statistical analysis tools',
                    'tool_count': 1
                }
            ]
            
            response = self.client.get('/api/tools/')
            
            # Verify all required fields are present
            required_fields = ['tools', 'total_count', 'categories']
            
            for field in required_fields:
                self.assertIn(field, response.data, f"Missing required field: {field}")
            
            # Verify field types
            self.assertIsInstance(response.data['tools'], list)
            self.assertIsInstance(response.data['total_count'], int)
            self.assertIsInstance(response.data['categories'], list)
            
            # Verify tool has all required fields
            tool = response.data['tools'][0]
            self.assertIsInstance(tool['tool_id'], str)
            self.assertIsInstance(tool['name'], str)
            self.assertIsInstance(tool['description'], str)
            self.assertIsInstance(tool['category'], str)
            self.assertIsInstance(tool['parameters'], list)
            self.assertIsInstance(tool['output_types'], list)
            self.assertIsInstance(tool['estimated_time'], float)
            self.assertIsInstance(tool['complexity'], str)
    
    def test_get_tools_audit_logging(self):
        """Test that tools listing is properly logged for audit"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_all_tools') as mock_get_tools:
            mock_get_tools.return_value = []
        
        with patch('analytics.services.tool_registry.ToolRegistry.get_categories') as mock_get_categories:
            mock_get_categories.return_value = []
        
        with patch('analytics.services.audit_trail_manager.AuditTrailManager.log_user_action') as mock_audit:
            response = self.client.get('/api/tools/')
            
            # Verify audit logging was called
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            self.assertEqual(call_args[1]['action'], 'tools_list')
            self.assertEqual(call_args[1]['resource'], 'analysis_tools')
            self.assertEqual(call_args[1]['success'], True)
    
    def test_get_tools_with_langchain_integration(self):
        """Test tools listing with LangChain integration info"""
        with patch('analytics.services.tool_registry.ToolRegistry.get_all_tools') as mock_get_tools:
            mock_get_tools.return_value = [
                {
                    'tool_id': 'descriptive_stats',
                    'name': 'Descriptive Statistics',
                    'description': 'Calculate basic descriptive statistics',
                    'category': 'statistical',
                    'parameters': [],
                    'output_types': ['table'],
                    'estimated_time': 2.5,
                    'complexity': 'low',
                    'langchain_registered': True,
                    'langchain_tool_name': 'descriptive_statistics_tool',
                    'available_for_llm': True
                }
            ]
        
        with patch('analytics.services.tool_registry.ToolRegistry.get_categories') as mock_get_categories:
            mock_get_categories.return_value = []
            
            response = self.client.get('/api/tools/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            tool = response.data['tools'][0]
            self.assertIn('langchain_registered', tool)
            self.assertIn('langchain_tool_name', tool)
            self.assertIn('available_for_llm', tool)
            self.assertTrue(tool['langchain_registered'])
            self.assertTrue(tool['available_for_llm'])
