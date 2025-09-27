"""
Unit Tests for Analytics Tools

This module contains comprehensive unit tests for all tools in the analytics app.
Tests cover statistical tools, visualization tools, ML tools, survival analysis tools, and the tool registry.
"""

import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from analytics.tools.statistical_tools import StatisticalTools
from analytics.tools.visualization_tools import VisualizationTools
from analytics.tools.ml_tools import MachineLearningTools
from analytics.tools.survival_tools import SurvivalAnalysisTools
from analytics.tools.tool_registry import ToolRegistry

User = get_user_model()


class StatisticalToolsTest(TestCase):
    """Test StatisticalTools functionality"""
    
    def setUp(self):
        self.tools = StatisticalTools()
        # Create sample data
        self.sample_data = pd.DataFrame({
            'numeric_col': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'categorical_col': ['A', 'B', 'A', 'C', 'B', 'A', 'C', 'B', 'A', 'C'],
            'text_col': ['text1', 'text2', 'text3', 'text4', 'text5', 'text6', 'text7', 'text8', 'text9', 'text10']
        })
        
    def test_descriptive_statistics(self):
        """Test descriptive statistics calculation"""
        result = self.tools.descriptive_statistics(self.sample_data, 'numeric_col')
        
        self.assertTrue(result['success'])
        self.assertIn('mean', result['statistics'])
        self.assertIn('std', result['statistics'])
        self.assertIn('min', result['statistics'])
        self.assertIn('max', result['statistics'])
        
    def test_descriptive_statistics_invalid_column(self):
        """Test descriptive statistics with invalid column"""
        result = self.tools.descriptive_statistics(self.sample_data, 'nonexistent_col')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
    def test_correlation_analysis(self):
        """Test correlation analysis"""
        # Create data with known correlation
        data = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10]
        })
        
        result = self.tools.correlation_analysis(data, ['x', 'y'])
        
        self.assertTrue(result['success'])
        self.assertIn('correlation_matrix', result)
        
    def test_hypothesis_testing(self):
        """Test hypothesis testing"""
        result = self.tools.hypothesis_testing(
            self.sample_data, 
            'numeric_col', 
            test_type='t_test',
            null_hypothesis='mean = 5'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('p_value', result)
        self.assertIn('test_statistic', result)
        
    def test_frequency_analysis(self):
        """Test frequency analysis"""
        result = self.tools.frequency_analysis(self.sample_data, 'categorical_col')
        
        self.assertTrue(result['success'])
        self.assertIn('frequencies', result)
        self.assertIn('percentages', result)
        
    def test_outlier_detection(self):
        """Test outlier detection"""
        # Create data with outliers
        data = pd.DataFrame({
            'values': [1, 2, 3, 4, 5, 100, 6, 7, 8, 9, 10]
        })
        
        result = self.tools.outlier_detection(data, 'values')
        
        self.assertTrue(result['success'])
        self.assertIn('outliers', result)
        self.assertIn('outlier_indices', result)


class VisualizationToolsTest(TestCase):
    """Test VisualizationTools functionality"""
    
    def setUp(self):
        self.tools = VisualizationTools()
        self.sample_data = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10],
            'category': ['A', 'B', 'A', 'B', 'A']
        })
        
    @patch('analytics.tools.visualization_tools.plt')
    def test_create_line_plot(self, mock_plt):
        """Test line plot creation"""
        result = self.tools.create_line_plot(
            self.sample_data, 
            x_column='x', 
            y_column='y',
            title='Test Line Plot'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('plot_path', result)
        
    @patch('analytics.tools.visualization_tools.plt')
    def test_create_bar_plot(self, mock_plt):
        """Test bar plot creation"""
        result = self.tools.create_bar_plot(
            self.sample_data, 
            x_column='category', 
            y_column='y',
            title='Test Bar Plot'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('plot_path', result)
        
    @patch('analytics.tools.visualization_tools.plt')
    def test_create_scatter_plot(self, mock_plt):
        """Test scatter plot creation"""
        result = self.tools.create_scatter_plot(
            self.sample_data, 
            x_column='x', 
            y_column='y',
            title='Test Scatter Plot'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('plot_path', result)
        
    @patch('analytics.tools.visualization_tools.plt')
    def test_create_histogram(self, mock_plt):
        """Test histogram creation"""
        result = self.tools.create_histogram(
            self.sample_data, 
            column='y',
            title='Test Histogram'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('plot_path', result)
        
    @patch('analytics.tools.visualization_tools.plt')
    def test_create_box_plot(self, mock_plt):
        """Test box plot creation"""
        result = self.tools.create_box_plot(
            self.sample_data, 
            column='y',
            title='Test Box Plot'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('plot_path', result)
        
    def test_create_plot_invalid_column(self):
        """Test plot creation with invalid column"""
        result = self.tools.create_line_plot(
            self.sample_data, 
            x_column='nonexistent', 
            y_column='y'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class MachineLearningToolsTest(TestCase):
    """Test MachineLearningTools functionality"""
    
    def setUp(self):
        self.tools = MachineLearningTools()
        # Create sample data for ML
        np.random.seed(42)
        self.sample_data = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'target': np.random.randint(0, 2, 100)
        })
        
    def test_train_classification_model(self):
        """Test classification model training"""
        result = self.tools.train_classification_model(
            self.sample_data,
            target_column='target',
            feature_columns=['feature1', 'feature2'],
            model_type='logistic_regression'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('model_id', result)
        self.assertIn('accuracy', result)
        
    def test_train_regression_model(self):
        """Test regression model training"""
        # Create regression data
        np.random.seed(42)
        reg_data = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'target': np.random.randn(100)
        })
        
        result = self.tools.train_regression_model(
            reg_data,
            target_column='target',
            feature_columns=['feature1', 'feature2'],
            model_type='linear_regression'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('model_id', result)
        self.assertIn('r2_score', result)
        
    def test_predict_classification(self):
        """Test classification prediction"""
        # First train a model
        train_result = self.tools.train_classification_model(
            self.sample_data,
            target_column='target',
            feature_columns=['feature1', 'feature2'],
            model_type='logistic_regression'
        )
        
        if train_result['success']:
            # Test prediction
            test_data = pd.DataFrame({
                'feature1': [0.5, -0.3],
                'feature2': [0.8, -0.2]
            })
            
            result = self.tools.predict_classification(
                test_data,
                model_id=train_result['model_id']
            )
            
            self.assertTrue(result['success'])
            self.assertIn('predictions', result)
            
    def test_feature_importance(self):
        """Test feature importance calculation"""
        result = self.tools.calculate_feature_importance(
            self.sample_data,
            target_column='target',
            feature_columns=['feature1', 'feature2']
        )
        
        self.assertTrue(result['success'])
        self.assertIn('importance_scores', result)
        
    def test_cross_validation(self):
        """Test cross-validation"""
        result = self.tools.cross_validate_model(
            self.sample_data,
            target_column='target',
            feature_columns=['feature1', 'feature2'],
            model_type='logistic_regression',
            cv_folds=5
        )
        
        self.assertTrue(result['success'])
        self.assertIn('cv_scores', result)
        self.assertIn('mean_score', result)


class SurvivalAnalysisToolsTest(TestCase):
    """Test SurvivalAnalysisTools functionality"""
    
    def setUp(self):
        self.tools = SurvivalAnalysisTools()
        # Create sample survival data
        self.survival_data = pd.DataFrame({
            'duration': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            'event': [1, 1, 0, 1, 0, 1, 1, 0, 1, 0],
            'group': ['A', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A']
        })
        
    def test_kaplan_meier_analysis(self):
        """Test Kaplan-Meier survival analysis"""
        result = self.tools.kaplan_meier_analysis(
            self.survival_data,
            duration_column='duration',
            event_column='event'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('survival_function', result)
        self.assertIn('median_survival', result)
        
    def test_log_rank_test(self):
        """Test log-rank test for survival comparison"""
        result = self.tools.log_rank_test(
            self.survival_data,
            duration_column='duration',
            event_column='event',
            group_column='group'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('p_value', result)
        self.assertIn('test_statistic', result)
        
    def test_cox_proportional_hazards(self):
        """Test Cox proportional hazards model"""
        result = self.tools.cox_proportional_hazards(
            self.survival_data,
            duration_column='duration',
            event_column='event',
            covariates=['group']
        )
        
        self.assertTrue(result['success'])
        self.assertIn('hazard_ratios', result)
        self.assertIn('p_values', result)
        
    def test_survival_analysis_missing_lifelines(self):
        """Test survival analysis when lifelines is not available"""
        with patch('analytics.tools.survival_tools.lifelines', None):
            result = self.tools.kaplan_meier_analysis(
                self.survival_data,
                duration_column='duration',
                event_column='event'
            )
            
            self.assertFalse(result['success'])
            self.assertIn('error', result)


class ToolRegistryTest(TestCase):
    """Test ToolRegistry functionality"""
    
    def setUp(self):
        self.registry = ToolRegistry()
        
    def test_registry_initialization(self):
        """Test registry initializes correctly"""
        self.assertIsNotNone(self.registry)
        self.assertIsInstance(self.registry.tools, dict)
        
    def test_register_tool(self):
        """Test tool registration"""
        mock_tool = Mock()
        mock_tool.name = 'test_tool'
        mock_tool.tool_type = 'statistical'
        
        result = self.registry.register_tool(mock_tool)
        
        self.assertTrue(result['success'])
        self.assertIn('test_tool', self.registry.tools)
        
    def test_get_tool_existing(self):
        """Test getting existing tool"""
        mock_tool = Mock()
        mock_tool.name = 'test_tool'
        self.registry.tools['test_tool'] = mock_tool
        
        result = self.registry.get_tool('test_tool')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['tool'], mock_tool)
        
    def test_get_tool_nonexistent(self):
        """Test getting non-existent tool"""
        result = self.registry.get_tool('nonexistent_tool')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
    def test_list_tools_by_type(self):
        """Test listing tools by type"""
        # Register tools of different types
        mock_tool1 = Mock()
        mock_tool1.name = 'stat_tool'
        mock_tool1.tool_type = 'statistical'
        
        mock_tool2 = Mock()
        mock_tool2.name = 'viz_tool'
        mock_tool2.tool_type = 'visualization'
        
        self.registry.register_tool(mock_tool1)
        self.registry.register_tool(mock_tool2)
        
        result = self.registry.list_tools_by_type('statistical')
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['tools']), 1)
        self.assertEqual(result['tools'][0].name, 'stat_tool')
        
    def test_validate_tool_parameters(self):
        """Test tool parameter validation"""
        schema = {
            'param1': {'type': 'string', 'required': True},
            'param2': {'type': 'integer', 'required': False}
        }
        
        valid_params = {'param1': 'test', 'param2': 123}
        result = self.registry.validate_tool_parameters(schema, valid_params)
        
        self.assertTrue(result['valid'])
        
    def test_validate_tool_parameters_invalid(self):
        """Test tool parameter validation with invalid parameters"""
        schema = {
            'param1': {'type': 'string', 'required': True},
            'param2': {'type': 'integer', 'required': False}
        }
        
        invalid_params = {'param2': 'not_an_integer'}
        result = self.registry.validate_tool_parameters(schema, invalid_params)
        
        self.assertFalse(result['valid'])
        self.assertIn('errors', result)
        
    def test_get_tool_statistics(self):
        """Test getting tool usage statistics"""
        # Register some tools
        mock_tool1 = Mock()
        mock_tool1.name = 'tool1'
        mock_tool1.usage_count = 10
        
        mock_tool2 = Mock()
        mock_tool2.name = 'tool2'
        mock_tool2.usage_count = 5
        
        self.registry.register_tool(mock_tool1)
        self.registry.register_tool(mock_tool2)
        
        stats = self.registry.get_tool_statistics()
        
        self.assertIn('total_tools', stats)
        self.assertIn('usage_by_type', stats)
        self.assertEqual(stats['total_tools'], 2)
