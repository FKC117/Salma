"""
Survival Analysis Tools

This module provides comprehensive survival analysis tools for the analytical system.
All tools are designed to work with pandas DataFrames and return standardized results.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Try to import lifelines, but handle gracefully if not available
try:
    from lifelines import KaplanMeierFitter, CoxPHFitter, WeibullFitter, LogNormalFitter, LogLogisticFitter
    from lifelines.statistics import logrank_test, multivariate_logrank_test
    from lifelines.utils import concordance_index
    LIFELINES_AVAILABLE = True
except ImportError:
    LIFELINES_AVAILABLE = False
    logger.warning("lifelines package not available. Some survival analysis features will be limited.")


class SurvivalAnalysisTools:
    """
    Collection of survival analysis tools for data analysis
    """
    
    @staticmethod
    def kaplan_meier_analysis(df: pd.DataFrame, duration_column: str, event_column: str,
                             group_column: Optional[str] = None, title: str = "Kaplan-Meier Survival Curve") -> Dict[str, Any]:
        """
        Perform Kaplan-Meier survival analysis
        
        Args:
            df: Input DataFrame
            duration_column: Column containing survival times
            event_column: Column containing event indicators (1=event, 0=censored)
            group_column: Optional column for grouping (stratified analysis)
            title: Title for the analysis
            
        Returns:
            Dict containing Kaplan-Meier results
        """
        try:
            if not LIFELINES_AVAILABLE:
                return {"error": "lifelines package not available. Please install with: pip install lifelines"}
            
            if duration_column not in df.columns or event_column not in df.columns:
                return {"error": "Duration or event column not found in DataFrame"}
            
            # Prepare data
            survival_data = df[[duration_column, event_column]].copy()
            if group_column and group_column in df.columns:
                survival_data[group_column] = df[group_column]
            
            # Remove rows with missing values
            survival_data = survival_data.dropna()
            
            if len(survival_data) == 0:
                return {"error": "No valid data available for survival analysis"}
            
            # Validate event column
            unique_events = survival_data[event_column].unique()
            if not all(event in [0, 1] for event in unique_events):
                return {"error": "Event column must contain only 0 (censored) and 1 (event) values"}
            
            results = {
                'type': 'kaplan_meier',
                'title': title,
                'duration_column': duration_column,
                'event_column': event_column,
                'group_column': group_column,
                'total_subjects': len(survival_data),
                'events': int(survival_data[event_column].sum()),
                'censored': int((survival_data[event_column] == 0).sum()),
                'created_at': datetime.now().isoformat()
            }
            
            if group_column:
                # Stratified analysis
                groups = survival_data[group_column].unique()
                group_results = {}
                
                for group in groups:
                    group_data = survival_data[survival_data[group_column] == group]
                    if len(group_data) < 2:
                        continue
                    
                    kmf = KaplanMeierFitter()
                    kmf.fit(group_data[duration_column], group_data[event_column], label=str(group))
                    
                    group_results[str(group)] = {
                        'survival_function': {
                            'timeline': kmf.survival_function_.index.tolist(),
                            'survival_probability': kmf.survival_function_.iloc[:, 0].tolist()
                        },
                        'median_survival_time': kmf.median_survival_time_,
                        'mean_survival_time': kmf.survival_function_.index[-1] if len(kmf.survival_function_) > 0 else None,
                        'subjects': len(group_data),
                        'events': int(group_data[event_column].sum())
                    }
                
                results['grouped_analysis'] = group_results
                
                # Log-rank test for comparing groups
                if len(groups) > 1:
                    try:
                        logrank_result = multivariate_logrank_test(
                            survival_data[duration_column],
                            survival_data[group_column],
                            survival_data[event_column]
                        )
                        results['logrank_test'] = {
                            'test_statistic': float(logrank_result.test_statistic),
                            'p_value': float(logrank_result.p_value),
                            'significant': logrank_result.p_value < 0.05
                        }
                    except Exception as e:
                        results['logrank_test'] = {'error': str(e)}
            else:
                # Single group analysis
                kmf = KaplanMeierFitter()
                kmf.fit(survival_data[duration_column], survival_data[event_column])
                
                results['survival_analysis'] = {
                    'survival_function': {
                        'timeline': kmf.survival_function_.index.tolist(),
                        'survival_probability': kmf.survival_function_.iloc[:, 0].tolist()
                    },
                    'median_survival_time': kmf.median_survival_time_,
                    'mean_survival_time': kmf.survival_function_.index[-1] if len(kmf.survival_function_) > 0 else None
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in kaplan_meier_analysis: {str(e)}")
            return {"error": f"Kaplan-Meier analysis failed: {str(e)}"}
    
    @staticmethod
    def cox_regression(df: pd.DataFrame, duration_column: str, event_column: str,
                      covariates: List[str], title: str = "Cox Proportional Hazards Model") -> Dict[str, Any]:
        """
        Perform Cox proportional hazards regression
        
        Args:
            df: Input DataFrame
            duration_column: Column containing survival times
            event_column: Column containing event indicators (1=event, 0=censored)
            covariates: List of covariate columns
            title: Title for the analysis
            
        Returns:
            Dict containing Cox regression results
        """
        try:
            if not LIFELINES_AVAILABLE:
                return {"error": "lifelines package not available. Please install with: pip install lifelines"}
            
            if duration_column not in df.columns or event_column not in df.columns:
                return {"error": "Duration or event column not found in DataFrame"}
            
            missing_covariates = [col for col in covariates if col not in df.columns]
            if missing_covariates:
                return {"error": f"Covariate columns not found: {missing_covariates}"}
            
            # Prepare data
            survival_data = df[[duration_column, event_column] + covariates].copy()
            survival_data = survival_data.dropna()
            
            if len(survival_data) == 0:
                return {"error": "No valid data available for Cox regression"}
            
            # Validate event column
            unique_events = survival_data[event_column].unique()
            if not all(event in [0, 1] for event in unique_events):
                return {"error": "Event column must contain only 0 (censored) and 1 (event) values"}
            
            # Fit Cox model
            cph = CoxPHFitter()
            cph.fit(survival_data, duration_column=duration_column, event_col=event_column)
            
            # Get summary statistics
            summary = cph.summary
            
            # Calculate concordance index
            concordance = concordance_index(
                survival_data[duration_column],
                -cph.predict_partial_hazard(survival_data),
                survival_data[event_column]
            )
            
            # Prepare results
            results = {
                'type': 'cox_regression',
                'title': title,
                'duration_column': duration_column,
                'event_column': event_column,
                'covariates': covariates,
                'total_subjects': len(survival_data),
                'events': int(survival_data[event_column].sum()),
                'censored': int((survival_data[event_column] == 0).sum()),
                'concordance_index': float(concordance),
                'coefficients': {},
                'created_at': datetime.now().isoformat()
            }
            
            # Extract coefficient information
            for covariate in covariates:
                if covariate in summary.index:
                    coef_info = summary.loc[covariate]
                    results['coefficients'][covariate] = {
                        'coef': float(coef_info['coef']),
                        'exp_coef': float(coef_info['exp(coef)']),
                        'se_coef': float(coef_info['se(coef)']),
                        'p_value': float(coef_info['p']),
                        'lower_ci': float(coef_info['lower 0.95']),
                        'upper_ci': float(coef_info['upper 0.95']),
                        'significant': coef_info['p'] < 0.05
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in cox_regression: {str(e)}")
            return {"error": f"Cox regression failed: {str(e)}"}
    
    @staticmethod
    def parametric_survival_analysis(df: pd.DataFrame, duration_column: str, event_column: str,
                                   distribution: str = 'weibull', group_column: Optional[str] = None,
                                   title: str = "Parametric Survival Analysis") -> Dict[str, Any]:
        """
        Perform parametric survival analysis
        
        Args:
            df: Input DataFrame
            duration_column: Column containing survival times
            event_column: Column containing event indicators (1=event, 0=censored)
            distribution: Parametric distribution ('weibull', 'lognormal', 'loglogistic')
            group_column: Optional column for grouping
            title: Title for the analysis
            
        Returns:
            Dict containing parametric survival results
        """
        try:
            if not LIFELINES_AVAILABLE:
                return {"error": "lifelines package not available. Please install with: pip install lifelines"}
            
            if duration_column not in df.columns or event_column not in df.columns:
                return {"error": "Duration or event column not found in DataFrame"}
            
            # Prepare data
            survival_data = df[[duration_column, event_column]].copy()
            if group_column and group_column in df.columns:
                survival_data[group_column] = df[group_column]
            
            survival_data = survival_data.dropna()
            
            if len(survival_data) == 0:
                return {"error": "No valid data available for parametric survival analysis"}
            
            # Validate event column
            unique_events = survival_data[event_column].unique()
            if not all(event in [0, 1] for event in unique_events):
                return {"error": "Event column must contain only 0 (censored) and 1 (event) values"}
            
            # Select appropriate fitter
            if distribution == 'weibull':
                fitter = WeibullFitter()
            elif distribution == 'lognormal':
                fitter = LogNormalFitter()
            elif distribution == 'loglogistic':
                fitter = LogLogisticFitter()
            else:
                return {"error": f"Unknown distribution: {distribution}. Choose from 'weibull', 'lognormal', 'loglogistic'"}
            
            results = {
                'type': 'parametric_survival',
                'title': title,
                'distribution': distribution,
                'duration_column': duration_column,
                'event_column': event_column,
                'group_column': group_column,
                'total_subjects': len(survival_data),
                'events': int(survival_data[event_column].sum()),
                'censored': int((survival_data[event_column] == 0).sum()),
                'created_at': datetime.now().isoformat()
            }
            
            if group_column:
                # Grouped analysis
                groups = survival_data[group_column].unique()
                group_results = {}
                
                for group in groups:
                    group_data = survival_data[survival_data[group_column] == group]
                    if len(group_data) < 2:
                        continue
                    
                    try:
                        fitter.fit(group_data[duration_column], group_data[event_column], label=str(group))
                        
                        group_results[str(group)] = {
                            'parameters': fitter.params_.to_dict(),
                            'aic': float(fitter.AIC_),
                            'median_survival_time': fitter.median_survival_time_,
                            'mean_survival_time': fitter.mean_survival_time_,
                            'subjects': len(group_data),
                            'events': int(group_data[event_column].sum())
                        }
                    except Exception as e:
                        group_results[str(group)] = {'error': str(e)}
                
                results['grouped_analysis'] = group_results
            else:
                # Single group analysis
                try:
                    fitter.fit(survival_data[duration_column], survival_data[event_column])
                    
                    results['survival_analysis'] = {
                        'parameters': fitter.params_.to_dict(),
                        'aic': float(fitter.AIC_),
                        'median_survival_time': fitter.median_survival_time_,
                        'mean_survival_time': fitter.mean_survival_time_
                    }
                except Exception as e:
                    results['survival_analysis'] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Error in parametric_survival_analysis: {str(e)}")
            return {"error": f"Parametric survival analysis failed: {str(e)}"}
    
    @staticmethod
    def survival_summary_statistics(df: pd.DataFrame, duration_column: str, event_column: str,
                                  group_column: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate summary statistics for survival data
        
        Args:
            df: Input DataFrame
            duration_column: Column containing survival times
            event_column: Column containing event indicators (1=event, 0=censored)
            group_column: Optional column for grouping
            
        Returns:
            Dict containing summary statistics
        """
        try:
            if duration_column not in df.columns or event_column not in df.columns:
                return {"error": "Duration or event column not found in DataFrame"}
            
            # Prepare data
            survival_data = df[[duration_column, event_column]].copy()
            if group_column and group_column in df.columns:
                survival_data[group_column] = df[group_column]
            
            survival_data = survival_data.dropna()
            
            if len(survival_data) == 0:
                return {"error": "No valid data available for survival summary"}
            
            # Validate event column
            unique_events = survival_data[event_column].unique()
            if not all(event in [0, 1] for event in unique_events):
                return {"error": "Event column must contain only 0 (censored) and 1 (event) values"}
            
            results = {
                'type': 'survival_summary',
                'duration_column': duration_column,
                'event_column': event_column,
                'group_column': group_column,
                'created_at': datetime.now().isoformat()
            }
            
            if group_column:
                # Grouped summary
                groups = survival_data[group_column].unique()
                group_summaries = {}
                
                for group in groups:
                    group_data = survival_data[survival_data[group_column] == group]
                    if len(group_data) == 0:
                        continue
                    
                    durations = group_data[duration_column]
                    events = group_data[event_column]
                    
                    group_summaries[str(group)] = {
                        'n_subjects': len(group_data),
                        'n_events': int(events.sum()),
                        'n_censored': int((events == 0).sum()),
                        'event_rate': float(events.mean()),
                        'median_duration': float(durations.median()),
                        'mean_duration': float(durations.mean()),
                        'min_duration': float(durations.min()),
                        'max_duration': float(durations.max()),
                        'std_duration': float(durations.std())
                    }
                
                results['group_summaries'] = group_summaries
            else:
                # Overall summary
                durations = survival_data[duration_column]
                events = survival_data[event_column]
                
                results['overall_summary'] = {
                    'n_subjects': len(survival_data),
                    'n_events': int(events.sum()),
                    'n_censored': int((events == 0).sum()),
                    'event_rate': float(events.mean()),
                    'median_duration': float(durations.median()),
                    'mean_duration': float(durations.mean()),
                    'min_duration': float(durations.min()),
                    'max_duration': float(durations.max()),
                    'std_duration': float(durations.std())
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in survival_summary_statistics: {str(e)}")
            return {"error": f"Survival summary statistics failed: {str(e)}"}
    
    @staticmethod
    def hazard_ratio_analysis(df: pd.DataFrame, duration_column: str, event_column: str,
                             group_column: str, reference_group: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate hazard ratios between groups
        
        Args:
            df: Input DataFrame
            duration_column: Column containing survival times
            event_column: Column containing event indicators (1=event, 0=censored)
            group_column: Column containing group assignments
            reference_group: Reference group for hazard ratio calculation
            
        Returns:
            Dict containing hazard ratio analysis
        """
        try:
            if not LIFELINES_AVAILABLE:
                return {"error": "lifelines package not available. Please install with: pip install lifelines"}
            
            if duration_column not in df.columns or event_column not in df.columns or group_column not in df.columns:
                return {"error": "Required columns not found in DataFrame"}
            
            # Prepare data
            survival_data = df[[duration_column, event_column, group_column]].copy()
            survival_data = survival_data.dropna()
            
            if len(survival_data) == 0:
                return {"error": "No valid data available for hazard ratio analysis"}
            
            # Get unique groups
            groups = survival_data[group_column].unique()
            if len(groups) < 2:
                return {"error": "At least 2 groups required for hazard ratio analysis"}
            
            # Set reference group
            if reference_group is None:
                reference_group = groups[0]
            elif reference_group not in groups:
                return {"error": f"Reference group '{reference_group}' not found in data"}
            
            # Create dummy variables for groups
            group_dummies = pd.get_dummies(survival_data[group_column], prefix='group')
            survival_data = pd.concat([survival_data, group_dummies], axis=1)
            
            # Remove reference group column
            ref_col = f'group_{reference_group}'
            if ref_col in survival_data.columns:
                survival_data = survival_data.drop(columns=[ref_col])
            
            # Fit Cox model
            cph = CoxPHFitter()
            cph.fit(survival_data, duration_column=duration_column, event_col=event_column)
            
            # Calculate hazard ratios
            hazard_ratios = {}
            for group in groups:
                if group == reference_group:
                    hazard_ratios[group] = {
                        'hazard_ratio': 1.0,
                        'reference': True
                    }
                else:
                    group_col = f'group_{group}'
                    if group_col in cph.summary.index:
                        coef_info = cph.summary.loc[group_col]
                        hazard_ratios[group] = {
                            'hazard_ratio': float(coef_info['exp(coef)']),
                            'p_value': float(coef_info['p']),
                            'lower_ci': float(coef_info['lower 0.95']),
                            'upper_ci': float(coef_info['upper 0.95']),
                            'significant': coef_info['p'] < 0.05,
                            'reference': False
                        }
            
            return {
                'type': 'hazard_ratio_analysis',
                'duration_column': duration_column,
                'event_column': event_column,
                'group_column': group_column,
                'reference_group': reference_group,
                'hazard_ratios': hazard_ratios,
                'total_subjects': len(survival_data),
                'groups': groups.tolist(),
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in hazard_ratio_analysis: {str(e)}")
            return {"error": f"Hazard ratio analysis failed: {str(e)}"}
    
    @staticmethod
    def survival_curve_comparison(df: pd.DataFrame, duration_column: str, event_column: str,
                                 group_column: str, title: str = "Survival Curve Comparison") -> Dict[str, Any]:
        """
        Compare survival curves between groups
        
        Args:
            df: Input DataFrame
            duration_column: Column containing survival times
            event_column: Column containing event indicators (1=event, 0=censored)
            group_column: Column containing group assignments
            title: Title for the comparison
            
        Returns:
            Dict containing survival curve comparison results
        """
        try:
            if not LIFELINES_AVAILABLE:
                return {"error": "lifelines package not available. Please install with: pip install lifelines"}
            
            if duration_column not in df.columns or event_column not in df.columns or group_column not in df.columns:
                return {"error": "Required columns not found in DataFrame"}
            
            # Prepare data
            survival_data = df[[duration_column, event_column, group_column]].copy()
            survival_data = survival_data.dropna()
            
            if len(survival_data) == 0:
                return {"error": "No valid data available for survival curve comparison"}
            
            # Get unique groups
            groups = survival_data[group_column].unique()
            if len(groups) < 2:
                return {"error": "At least 2 groups required for survival curve comparison"}
            
            # Perform log-rank test
            logrank_result = multivariate_logrank_test(
                survival_data[duration_column],
                survival_data[group_column],
                survival_data[event_column]
            )
            
            # Calculate Kaplan-Meier curves for each group
            group_curves = {}
            for group in groups:
                group_data = survival_data[survival_data[group_column] == group]
                if len(group_data) < 2:
                    continue
                
                kmf = KaplanMeierFitter()
                kmf.fit(group_data[duration_column], group_data[event_column], label=str(group))
                
                group_curves[str(group)] = {
                    'survival_function': {
                        'timeline': kmf.survival_function_.index.tolist(),
                        'survival_probability': kmf.survival_function_.iloc[:, 0].tolist()
                    },
                    'median_survival_time': kmf.median_survival_time_,
                    'subjects': len(group_data),
                    'events': int(group_data[event_column].sum())
                }
            
            return {
                'type': 'survival_curve_comparison',
                'title': title,
                'duration_column': duration_column,
                'event_column': event_column,
                'group_column': group_column,
                'groups': groups.tolist(),
                'group_curves': group_curves,
                'logrank_test': {
                    'test_statistic': float(logrank_result.test_statistic),
                    'p_value': float(logrank_result.p_value),
                    'significant': logrank_result.p_value < 0.05
                },
                'total_subjects': len(survival_data),
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in survival_curve_comparison: {str(e)}")
            return {"error": f"Survival curve comparison failed: {str(e)}"}
