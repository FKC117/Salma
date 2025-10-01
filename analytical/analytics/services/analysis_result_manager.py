"""
Analysis Result Manager
Handles creation and management of analysis results with proper templating
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from django.template.loader import render_to_string
from django.conf import settings
from analytics.services.chart_generator import chart_generator
from analytics.services.ai_interpretation_service import ai_interpretation_service

logger = logging.getLogger(__name__)

class AnalysisResultManager:
    """
    Service for managing analysis results and rendering them with appropriate templates
    """
    
    def __init__(self):
        self.chart_generator = chart_generator
        self.ai_service = ai_interpretation_service
    
    def create_text_analysis_result(
        self,
        analysis_id: str,
        title: str,
        description: str,
        summary_stats: Optional[List[Dict[str, Any]]] = None,
        key_insights: Optional[List[Dict[str, Any]]] = None,
        detailed_analysis: Optional[str] = None,
        recommendations: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Create a text analysis result template
        """
        try:
            context = {
                'analysis_id': analysis_id,
                'title': title,
                'description': description,
                'summary_stats': summary_stats or [],
                'key_insights': key_insights or [],
                'detailed_analysis': detailed_analysis,
                'recommendations': recommendations or []
            }
            
            return render_to_string(
                'analytics/partials/analysis_results/text_analysis_result.html',
                context
            )
            
        except Exception as e:
            logger.error(f"Error creating text analysis result: {str(e)}")
            return self._create_error_template(analysis_id, str(e))
    
    def create_table_analysis_result(
        self,
        analysis_id: str,
        title: str,
        description: str,
        table_summary: Optional[Dict[str, Any]] = None,
        table_data: Optional[Dict[str, Any]] = None,
        statistical_analysis: Optional[Dict[str, Any]] = None,
        data_quality: Optional[Dict[str, Any]] = None,
        summary_stats: Optional[List[Dict[str, Any]]] = None,
        visualizations: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a table analysis result template
        """
        try:
            context = {
                'analysis_id': analysis_id,
                'title': title,
                'description': description,
                'table_summary': table_summary or {},
                'table_data': table_data or {},
                'statistical_analysis': statistical_analysis or {},
                'data_quality': data_quality or {},
                'summary_stats': summary_stats or [],
                'visualizations': visualizations or {}
            }
            
            print(f"🔧 DEBUG: Analysis result manager context visualizations: {type(context.get('visualizations', {}))}")
            print(f"🔧 DEBUG: Analysis result manager visualizations keys: {list(context.get('visualizations', {}).keys())}")
            if context.get('visualizations', {}).get('histograms'):
                print(f"🔧 DEBUG: Histograms available: {len(context['visualizations']['histograms'])}")
            if context.get('visualizations', {}).get('boxplots'):
                print(f"🔧 DEBUG: Box plots available: {len(context['visualizations']['boxplots'])}")
            if context.get('visualizations', {}).get('outliers'):
                print(f"🔧 DEBUG: Outliers available: {len(context['visualizations']['outliers'])}")
            
            return render_to_string(
                'analytics/partials/analysis_results/table_analysis_result.html',
                context
            )
            
        except Exception as e:
            logger.error(f"Error creating table analysis result: {str(e)}")
            return self._create_error_template(analysis_id, str(e))
    
    def create_chart_analysis_result(
        self,
        analysis_id: str,
        title: str,
        description: str,
        chart_type: str,
        data: Any,
        chart_config: Optional[Dict[str, Any]] = None,
        chart_insights: Optional[List[Dict[str, Any]]] = None,
        statistical_summary: Optional[Dict[str, Any]] = None,
        chart_summary: Optional[Dict[str, Any]] = None,
        chart_data: Optional[Dict[str, Any]] = None  # Add this parameter
    ) -> str:
        """
        Create a chart analysis result template
        """
        try:
            # Use provided chart_data or generate chart if data is provided
            if chart_data is None:
                chart_data = None
                if data is not None:
                    chart_result = self.chart_generator.generate_chart(
                        chart_type=chart_type,
                        data=data,
                        title=title,
                        **(chart_config or {})
                    )
                    
                    if chart_result['success']:
                        chart_data = chart_result
                    else:
                        logger.warning(f"Chart generation failed: {chart_result.get('error')}")
            
            # Use provided chart_summary or create one
            if chart_summary is None:
                chart_summary = self._create_chart_summary(chart_type, data, chart_data)
            
            context = {
                'analysis_id': analysis_id,
                'title': title,
                'description': description,
                'chart_summary': chart_summary,
                'chart_data': chart_data,
                'chart_config': chart_config or {},
                'chart_insights': chart_insights or [],
                'statistical_summary': statistical_summary or {}
            }
            
            return render_to_string(
                'analytics/partials/analysis_results/chart_analysis_result.html',
                context
            )
            
        except Exception as e:
            logger.error(f"Error creating chart analysis result: {str(e)}")
            return self._create_error_template(analysis_id, str(e))
    
    def create_analysis_result(
        self,
        result_type: str,
        analysis_id: str,
        title: str,
        description: str,
        **kwargs
    ) -> str:
        """
        Create an analysis result based on type
        """
        try:
            if result_type == 'text':
                return self.create_text_analysis_result(
                    analysis_id, title, description, **kwargs
                )
            elif result_type == 'table':
                return self.create_table_analysis_result(
                    analysis_id, title, description, **kwargs
                )
            elif result_type == 'chart':
                return self.create_chart_analysis_result(
                    analysis_id, title, description, **kwargs
                )
            else:
                return self._create_error_template(
                    analysis_id, f"Unknown result type: {result_type}"
                )
                
        except Exception as e:
            logger.error(f"Error creating analysis result: {str(e)}")
            return self._create_error_template(analysis_id, str(e))
    
    def _create_chart_summary(
        self,
        chart_type: str,
        data: Any,
        chart_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create chart summary information"""
        summary = {
            'type': chart_type.title(),
            'data_points': 0,
            'variables': 0,
            'insights_count': 0
        }
        
        if hasattr(data, 'shape'):
            summary['data_points'] = data.shape[0] if len(data.shape) > 0 else 0
            summary['variables'] = data.shape[1] if len(data.shape) > 1 else 0
        
        if chart_data and chart_data.get('success'):
            summary['insights_count'] = 3  # Default insight count
        
        return summary
    
    def _create_error_template(self, analysis_id: str, error_message: str) -> str:
        """Create an error template for failed analysis results"""
        return f"""
        <div class="analysis-result-container" data-analysis-id="{analysis_id}">
            <div class="analysis-header">
                <div class="analysis-title-section">
                    <div class="analysis-icon">
                        <i class="bi bi-exclamation-triangle"></i>
                    </div>
                    <div class="analysis-title-info">
                        <h4 class="analysis-title">Analysis Error</h4>
                        <p class="analysis-description">Failed to generate analysis result</p>
                    </div>
                </div>
            </div>
            <div class="analysis-content">
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    <strong>Error:</strong> {error_message}
                </div>
            </div>
        </div>
        """
    
    def get_analysis_insights(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str,
        insight_count: int = 5
    ) -> List[Dict[str, Any]]:
        """Get AI-generated insights for analysis results"""
        try:
            return self.ai_service.generate_insights(
                analysis_data, analysis_type, insight_count
            )
        except Exception as e:
            logger.error(f"Error getting analysis insights: {str(e)}")
            return []
    
    def get_analysis_recommendations(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str,
        recommendation_count: int = 3
    ) -> List[Dict[str, Any]]:
        """Get AI-generated recommendations for analysis results"""
        try:
            return self.ai_service.generate_recommendations(
                analysis_data, analysis_type, recommendation_count
            )
        except Exception as e:
            logger.error(f"Error getting analysis recommendations: {str(e)}")
            return []
    
    def format_statistical_summary(
        self,
        data: Any,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Format statistical summary for analysis results"""
        try:
            if hasattr(data, 'describe'):
                stats = data.describe()
                
                # Convert to dictionary format
                summary = {
                    'descriptive': {
                        'columns': stats.columns.tolist(),
                        'stats': {}
                    }
                }
                
                for stat_name in stats.index:
                    summary['descriptive']['stats'][stat_name] = stats.loc[stat_name].tolist()
                
                # Add correlation if numeric columns exist
                numeric_data = data.select_dtypes(include=['number'])
                if not numeric_data.empty and len(numeric_data.columns) > 1:
                    summary['correlation'] = numeric_data.corr().to_dict()
                
                return summary
            else:
                return {'descriptive': {'columns': [], 'stats': {}}}
                
        except Exception as e:
            logger.error(f"Error formatting statistical summary: {str(e)}")
            return {'descriptive': {'columns': [], 'stats': {}}}
    
    def format_data_quality_metrics(
        self,
        data: Any
    ) -> Dict[str, Any]:
        """Format data quality metrics for analysis results"""
        try:
            if not hasattr(data, 'isnull'):
                return {'metrics': []}
            
            total_rows = len(data)
            total_cells = data.size
            
            metrics = []
            
            # Completeness
            missing_cells = data.isnull().sum().sum()
            completeness = ((total_cells - missing_cells) / total_cells) * 100
            metrics.append({
                'name': 'Completeness',
                'score': round(completeness, 2),
                'status': 'excellent' if completeness >= 95 else 'good' if completeness >= 80 else 'warning' if completeness >= 60 else 'poor'
            })
            
            # Duplicates
            duplicate_rows = data.duplicated().sum()
            duplicate_percentage = (duplicate_rows / total_rows) * 100
            metrics.append({
                'name': 'Uniqueness',
                'score': round(100 - duplicate_percentage, 2),
                'status': 'excellent' if duplicate_percentage <= 5 else 'good' if duplicate_percentage <= 15 else 'warning' if duplicate_percentage <= 30 else 'poor'
            })
            
            # Data types consistency
            numeric_columns = data.select_dtypes(include=['number']).columns
            type_consistency = (len(numeric_columns) / len(data.columns)) * 100
            metrics.append({
                'name': 'Type Consistency',
                'score': round(type_consistency, 2),
                'status': 'excellent' if type_consistency >= 80 else 'good' if type_consistency >= 60 else 'warning' if type_consistency >= 40 else 'poor'
            })
            
            return {'metrics': metrics}
            
        except Exception as e:
            logger.error(f"Error formatting data quality metrics: {str(e)}")
            return {'metrics': []}


# Global instance
analysis_result_manager = AnalysisResultManager()
