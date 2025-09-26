"""
Statistical Analysis Tools

This module provides comprehensive statistical analysis tools for the analytical system.
All tools are designed to work with pandas DataFrames and return standardized results.
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import chi2_contingency, fisher_exact
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StatisticalTools:
    """
    Collection of statistical analysis tools for data analysis
    """
    
    @staticmethod
    def descriptive_statistics(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive descriptive statistics for numeric columns
        
        Args:
            df: Input DataFrame
            columns: Specific columns to analyze (if None, all numeric columns)
            
        Returns:
            Dict containing descriptive statistics
        """
        try:
            if columns is None:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            else:
                numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in ['int64', 'float64']]
            
            if not numeric_cols:
                return {"error": "No numeric columns found for analysis"}
            
            results = {}
            
            for col in numeric_cols:
                series = df[col].dropna()
                if len(series) == 0:
                    continue
                    
                results[col] = {
                    'count': len(series),
                    'mean': float(series.mean()),
                    'median': float(series.median()),
                    'mode': float(series.mode().iloc[0]) if not series.mode().empty else None,
                    'std': float(series.std()),
                    'var': float(series.var()),
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'range': float(series.max() - series.min()),
                    'q1': float(series.quantile(0.25)),
                    'q3': float(series.quantile(0.75)),
                    'iqr': float(series.quantile(0.75) - series.quantile(0.25)),
                    'skewness': float(series.skew()),
                    'kurtosis': float(series.kurtosis()),
                    'missing_count': int(df[col].isna().sum()),
                    'missing_percentage': float(df[col].isna().sum() / len(df) * 100)
                }
            
            return {
                'type': 'descriptive_statistics',
                'summary': {
                    'total_columns_analyzed': len(results),
                    'total_rows': len(df),
                    'analysis_timestamp': datetime.now().isoformat()
                },
                'statistics': results
            }
            
        except Exception as e:
            logger.error(f"Error in descriptive_statistics: {str(e)}")
            return {"error": f"Descriptive statistics calculation failed: {str(e)}"}
    
    @staticmethod
    def correlation_analysis(df: pd.DataFrame, method: str = 'pearson', 
                           columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calculate correlation matrix and analysis
        
        Args:
            df: Input DataFrame
            method: Correlation method ('pearson', 'spearman', 'kendall')
            columns: Specific columns to analyze
            
        Returns:
            Dict containing correlation analysis
        """
        try:
            if columns is None:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            else:
                numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in ['int64', 'float64']]
            
            if len(numeric_cols) < 2:
                return {"error": "At least 2 numeric columns required for correlation analysis"}
            
            # Calculate correlation matrix
            corr_matrix = df[numeric_cols].corr(method=method)
            
            # Find strong correlations (|r| > 0.7)
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:
                        strong_correlations.append({
                            'variable1': corr_matrix.columns[i],
                            'variable2': corr_matrix.columns[j],
                            'correlation': float(corr_value),
                            'strength': 'strong' if abs(corr_value) > 0.8 else 'moderate'
                        })
            
            return {
                'type': 'correlation_analysis',
                'method': method,
                'correlation_matrix': corr_matrix.to_dict(),
                'strong_correlations': strong_correlations,
                'summary': {
                    'total_variables': len(numeric_cols),
                    'strong_correlations_count': len(strong_correlations),
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in correlation_analysis: {str(e)}")
            return {"error": f"Correlation analysis failed: {str(e)}"}
    
    @staticmethod
    def t_test(df: pd.DataFrame, column: str, group_column: str, 
               alternative: str = 'two-sided') -> Dict[str, Any]:
        """
        Perform t-test for comparing means between groups
        
        Args:
            df: Input DataFrame
            column: Numeric column to test
            group_column: Categorical column defining groups
            alternative: Test alternative ('two-sided', 'less', 'greater')
            
        Returns:
            Dict containing t-test results
        """
        try:
            if column not in df.columns or group_column not in df.columns:
                return {"error": "Specified columns not found in DataFrame"}
            
            # Get groups
            groups = df[group_column].unique()
            if len(groups) != 2:
                return {"error": "Group column must have exactly 2 unique values"}
            
            group1_data = df[df[group_column] == groups[0]][column].dropna()
            group2_data = df[df[group_column] == groups[1]][column].dropna()
            
            if len(group1_data) < 2 or len(group2_data) < 2:
                return {"error": "Each group must have at least 2 observations"}
            
            # Perform t-test
            t_stat, p_value = stats.ttest_ind(group1_data, group2_data, alternative=alternative)
            
            # Calculate effect size (Cohen's d)
            pooled_std = np.sqrt(((len(group1_data) - 1) * group1_data.var() + 
                                (len(group2_data) - 1) * group2_data.var()) / 
                               (len(group1_data) + len(group2_data) - 2))
            cohens_d = (group1_data.mean() - group2_data.mean()) / pooled_std
            
            return {
                'type': 't_test',
                'test_statistic': float(t_stat),
                'p_value': float(p_value),
                'alternative': alternative,
                'groups': {
                    'group1': {
                        'name': str(groups[0]),
                        'n': len(group1_data),
                        'mean': float(group1_data.mean()),
                        'std': float(group1_data.std())
                    },
                    'group2': {
                        'name': str(groups[1]),
                        'n': len(group2_data),
                        'mean': float(group2_data.mean()),
                        'std': float(group2_data.std())
                    }
                },
                'effect_size': {
                    'cohens_d': float(cohens_d),
                    'interpretation': 'large' if abs(cohens_d) > 0.8 else 'medium' if abs(cohens_d) > 0.5 else 'small'
                },
                'significance': p_value < 0.05,
                'summary': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'tested_column': column,
                    'group_column': group_column
                }
            }
            
        except Exception as e:
            logger.error(f"Error in t_test: {str(e)}")
            return {"error": f"T-test failed: {str(e)}"}
    
    @staticmethod
    def chi_square_test(df: pd.DataFrame, column1: str, column2: str) -> Dict[str, Any]:
        """
        Perform chi-square test of independence
        
        Args:
            df: Input DataFrame
            column1: First categorical column
            column2: Second categorical column
            
        Returns:
            Dict containing chi-square test results
        """
        try:
            if column1 not in df.columns or column2 not in df.columns:
                return {"error": "Specified columns not found in DataFrame"}
            
            # Create contingency table
            contingency_table = pd.crosstab(df[column1], df[column2])
            
            # Perform chi-square test
            chi2, p_value, dof, expected = chi2_contingency(contingency_table)
            
            # Calculate Cramér's V (effect size)
            n = contingency_table.sum().sum()
            cramers_v = np.sqrt(chi2 / (n * (min(contingency_table.shape) - 1)))
            
            return {
                'type': 'chi_square_test',
                'chi2_statistic': float(chi2),
                'p_value': float(p_value),
                'degrees_of_freedom': int(dof),
                'contingency_table': contingency_table.to_dict(),
                'expected_frequencies': expected.tolist(),
                'effect_size': {
                    'cramers_v': float(cramers_v),
                    'interpretation': 'strong' if cramers_v > 0.3 else 'moderate' if cramers_v > 0.1 else 'weak'
                },
                'significance': p_value < 0.05,
                'summary': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'tested_columns': [column1, column2],
                    'table_dimensions': contingency_table.shape
                }
            }
            
        except Exception as e:
            logger.error(f"Error in chi_square_test: {str(e)}")
            return {"error": f"Chi-square test failed: {str(e)}"}
    
    @staticmethod
    def anova_test(df: pd.DataFrame, column: str, group_column: str) -> Dict[str, Any]:
        """
        Perform one-way ANOVA test
        
        Args:
            df: Input DataFrame
            column: Numeric column to test
            group_column: Categorical column defining groups
            
        Returns:
            Dict containing ANOVA results
        """
        try:
            if column not in df.columns or group_column not in df.columns:
                return {"error": "Specified columns not found in DataFrame"}
            
            # Get groups
            groups = df[group_column].unique()
            if len(groups) < 2:
                return {"error": "At least 2 groups required for ANOVA"}
            
            # Prepare data for ANOVA
            group_data = []
            group_names = []
            for group in groups:
                group_values = df[df[group_column] == group][column].dropna()
                if len(group_values) > 0:
                    group_data.append(group_values)
                    group_names.append(str(group))
            
            if len(group_data) < 2:
                return {"error": "At least 2 groups with data required for ANOVA"}
            
            # Perform ANOVA
            f_stat, p_value = stats.f_oneway(*group_data)
            
            # Calculate eta-squared (effect size)
            ss_between = sum(len(group) * (group.mean() - np.concatenate(group_data).mean())**2 for group in group_data)
            ss_total = sum((np.concatenate(group_data) - np.concatenate(group_data).mean())**2)
            eta_squared = ss_between / ss_total if ss_total > 0 else 0
            
            # Group statistics
            group_stats = []
            for i, group in enumerate(group_data):
                group_stats.append({
                    'group_name': group_names[i],
                    'n': len(group),
                    'mean': float(group.mean()),
                    'std': float(group.std()),
                    'min': float(group.min()),
                    'max': float(group.max())
                })
            
            return {
                'type': 'anova_test',
                'f_statistic': float(f_stat),
                'p_value': float(p_value),
                'groups': group_stats,
                'effect_size': {
                    'eta_squared': float(eta_squared),
                    'interpretation': 'large' if eta_squared > 0.14 else 'medium' if eta_squared > 0.06 else 'small'
                },
                'significance': p_value < 0.05,
                'summary': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'tested_column': column,
                    'group_column': group_column,
                    'total_groups': len(group_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in anova_test: {str(e)}")
            return {"error": f"ANOVA test failed: {str(e)}"}
    
    @staticmethod
    def normality_test(df: pd.DataFrame, columns: Optional[List[str]] = None, 
                      method: str = 'shapiro') -> Dict[str, Any]:
        """
        Test normality of numeric columns
        
        Args:
            df: Input DataFrame
            columns: Specific columns to test (if None, all numeric columns)
            method: Test method ('shapiro', 'kstest', 'normaltest')
            
        Returns:
            Dict containing normality test results
        """
        try:
            if columns is None:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            else:
                numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in ['int64', 'float64']]
            
            if not numeric_cols:
                return {"error": "No numeric columns found for normality testing"}
            
            results = {}
            
            for col in numeric_cols:
                series = df[col].dropna()
                if len(series) < 3:
                    results[col] = {"error": "Insufficient data for normality test"}
                    continue
                
                try:
                    if method == 'shapiro':
                        if len(series) > 5000:  # Shapiro-Wilk has sample size limit
                            series_sample = series.sample(5000, random_state=42)
                        else:
                            series_sample = series
                        statistic, p_value = stats.shapiro(series_sample)
                    elif method == 'kstest':
                        statistic, p_value = stats.kstest(series, 'norm', args=(series.mean(), series.std()))
                    elif method == 'normaltest':
                        statistic, p_value = stats.normaltest(series)
                    else:
                        return {"error": f"Unknown normality test method: {method}"}
                    
                    results[col] = {
                        'test_method': method,
                        'statistic': float(statistic),
                        'p_value': float(p_value),
                        'is_normal': p_value > 0.05,
                        'sample_size': len(series),
                        'interpretation': 'normal' if p_value > 0.05 else 'not normal'
                    }
                    
                except Exception as e:
                    results[col] = {"error": f"Normality test failed: {str(e)}"}
            
            return {
                'type': 'normality_test',
                'method': method,
                'results': results,
                'summary': {
                    'total_columns_tested': len(numeric_cols),
                    'normal_columns': sum(1 for r in results.values() if isinstance(r, dict) and r.get('is_normal', False)),
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in normality_test: {str(e)}")
            return {"error": f"Normality test failed: {str(e)}"}
    
    @staticmethod
    def outlier_detection(df: pd.DataFrame, columns: Optional[List[str]] = None, 
                         method: str = 'iqr', threshold: float = 1.5) -> Dict[str, Any]:
        """
        Detect outliers in numeric columns
        
        Args:
            df: Input DataFrame
            columns: Specific columns to analyze
            method: Detection method ('iqr', 'zscore', 'modified_zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            Dict containing outlier detection results
        """
        try:
            if columns is None:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            else:
                numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in ['int64', 'float64']]
            
            if not numeric_cols:
                return {"error": "No numeric columns found for outlier detection"}
            
            results = {}
            
            for col in numeric_cols:
                series = df[col].dropna()
                if len(series) < 4:
                    results[col] = {"error": "Insufficient data for outlier detection"}
                    continue
                
                outliers = []
                
                if method == 'iqr':
                    Q1 = series.quantile(0.25)
                    Q3 = series.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - threshold * IQR
                    upper_bound = Q3 + threshold * IQR
                    outliers = series[(series < lower_bound) | (series > upper_bound)].tolist()
                    
                elif method == 'zscore':
                    z_scores = np.abs(stats.zscore(series))
                    outliers = series[z_scores > threshold].tolist()
                    
                elif method == 'modified_zscore':
                    median = series.median()
                    mad = np.median(np.abs(series - median))
                    modified_z_scores = 0.6745 * (series - median) / mad
                    outliers = series[np.abs(modified_z_scores) > threshold].tolist()
                
                else:
                    return {"error": f"Unknown outlier detection method: {method}"}
                
                results[col] = {
                    'method': method,
                    'threshold': threshold,
                    'outlier_count': len(outliers),
                    'outlier_percentage': len(outliers) / len(series) * 100,
                    'outliers': outliers,
                    'outlier_indices': series[series.isin(outliers)].index.tolist() if outliers else []
                }
            
            return {
                'type': 'outlier_detection',
                'method': method,
                'threshold': threshold,
                'results': results,
                'summary': {
                    'total_columns_analyzed': len(numeric_cols),
                    'columns_with_outliers': sum(1 for r in results.values() if isinstance(r, dict) and r.get('outlier_count', 0) > 0),
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in outlier_detection: {str(e)}")
            return {"error": f"Outlier detection failed: {str(e)}"}
    
    @staticmethod
    def confidence_interval(df: pd.DataFrame, column: str, confidence_level: float = 0.95) -> Dict[str, Any]:
        """
        Calculate confidence interval for a numeric column
        
        Args:
            df: Input DataFrame
            column: Numeric column to analyze
            confidence_level: Confidence level (0.95 for 95%, 0.99 for 99%)
            
        Returns:
            Dict containing confidence interval results
        """
        try:
            if column not in df.columns:
                return {"error": f"Column '{column}' not found in DataFrame"}
            
            series = df[column].dropna()
            if len(series) < 2:
                return {"error": "Insufficient data for confidence interval calculation"}
            
            n = len(series)
            mean = series.mean()
            std = series.std()
            se = std / np.sqrt(n)
            
            # Calculate critical value
            alpha = 1 - confidence_level
            critical_value = stats.t.ppf(1 - alpha/2, n - 1)
            
            # Calculate margin of error
            margin_of_error = critical_value * se
            
            # Calculate confidence interval
            ci_lower = mean - margin_of_error
            ci_upper = mean + margin_of_error
            
            return {
                'type': 'confidence_interval',
                'column': column,
                'confidence_level': confidence_level,
                'sample_size': n,
                'mean': float(mean),
                'standard_error': float(se),
                'margin_of_error': float(margin_of_error),
                'confidence_interval': {
                    'lower_bound': float(ci_lower),
                    'upper_bound': float(ci_upper)
                },
                'summary': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'interpretation': f"We are {confidence_level*100}% confident that the true population mean lies between {ci_lower:.4f} and {ci_upper:.4f}"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in confidence_interval: {str(e)}")
            return {"error": f"Confidence interval calculation failed: {str(e)}"}
