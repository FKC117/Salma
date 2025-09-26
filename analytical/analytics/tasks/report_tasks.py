"""
Report Generation Celery Tasks
Handles background report generation and document creation
"""

from celery import shared_task
from django.conf import settings
import json
import logging
from typing import Dict, Any, Optional, List
import time
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from analytics.models import Dataset, User
from analytics.services.report_generator import ReportGenerator
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.logging_service import StructuredLogger

logger = StructuredLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_analysis_report(self, dataset_id: int, analysis_results: List[Dict], user_id: int, report_format: str = 'html') -> Dict[str, Any]:
    """
    Generate comprehensive analysis report
    
    Args:
        dataset_id: ID of dataset
        analysis_results: List of analysis results
        user_id: ID of user
        report_format: Report format (html, pdf, json)
        
    Returns:
        Dict with report data
    """
    try:
        logger.info(f"Generating analysis report for dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'format': report_format})
        
        # Get dataset and user
        dataset = Dataset.objects.get(id=dataset_id)
        user = User.objects.get(id=user_id)
        
        # Initialize services
        report_generator = ReportGenerator()
        audit_manager = AuditTrailManager()
        
        # Generate report
        start_time = time.time()
        
        report = report_generator.generate_analysis_report(
            dataset=dataset,
            analysis_results=analysis_results,
            user=user,
            format=report_format
        )
        
        generation_time = time.time() - start_time
        
        # Log audit trail
        audit_manager.log_action(
            user=user,
            action='report_generated',
            details={
                'dataset_id': dataset_id,
                'report_format': report_format,
                'generation_time': generation_time,
                'report_size': len(report.get('content', '')),
                'analysis_count': len(analysis_results)
            }
        )
        
        logger.info(f"Analysis report generated successfully", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'generation_time': generation_time})
        
        return {
            'status': 'success',
            'report': report,
            'generation_time': generation_time
        }
        
    except Exception as exc:
        logger.error(f"Report generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        # Log audit trail for failure
        try:
            user = User.objects.get(id=user_id)
            audit_manager.log_action(
                user=user,
                action='report_generation_failed',
                details={
                    'dataset_id': dataset_id,
                    'report_format': report_format,
                    'error': str(exc),
                    'retry_count': self.request.retries
                }
            )
        except:
            pass
        
        # Retry if not max retries reached
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying report generation (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Report generation failed after maximum retries'
        }


@shared_task(bind=True, max_retries=1)
def generate_executive_summary(self, dataset_id: int, user_id: int, analysis_results: List[Dict]) -> Dict[str, Any]:
    """
    Generate executive summary report
    
    Args:
        dataset_id: ID of dataset
        user_id: ID of user
        analysis_results: List of analysis results
        
    Returns:
        Dict with executive summary
    """
    try:
        logger.info(f"Generating executive summary for dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        # Get dataset and user
        dataset = Dataset.objects.get(id=dataset_id)
        user = User.objects.get(id=user_id)
        
        # Initialize services
        report_generator = ReportGenerator()
        
        # Generate executive summary
        summary = report_generator.generate_executive_summary(
            dataset=dataset,
            analysis_results=analysis_results,
            user=user
        )
        
        logger.info(f"Executive summary generated", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'success',
            'summary': summary
        }
        
    except Exception as exc:
        logger.error(f"Executive summary generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Executive summary generation failed'
        }


@shared_task(bind=True, max_retries=1)
def generate_visualization_report(self, dataset_id: int, user_id: int, visualizations: List[Dict]) -> Dict[str, Any]:
    """
    Generate visualization report
    
    Args:
        dataset_id: ID of dataset
        user_id: ID of user
        visualizations: List of visualization data
        
    Returns:
        Dict with visualization report
    """
    try:
        logger.info(f"Generating visualization report for dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        # Get dataset and user
        dataset = Dataset.objects.get(id=dataset_id)
        user = User.objects.get(id=user_id)
        
        # Initialize services
        report_generator = ReportGenerator()
        
        # Generate visualization report
        report = report_generator.generate_visualization_report(
            dataset=dataset,
            visualizations=visualizations,
            user=user
        )
        
        logger.info(f"Visualization report generated", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'success',
            'report': report
        }
        
    except Exception as exc:
        logger.error(f"Visualization report generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Visualization report generation failed'
        }


@shared_task
def generate_data_profile_report(dataset_id: int, user_id: int) -> Dict[str, Any]:
    """
    Generate data profile report
    
    Args:
        dataset_id: ID of dataset
        user_id: ID of user
        
    Returns:
        Dict with data profile report
    """
    try:
        logger.info(f"Generating data profile report for dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        # Get dataset and user
        dataset = Dataset.objects.get(id=dataset_id)
        user = User.objects.get(id=user_id)
        
        # Initialize services
        report_generator = ReportGenerator()
        
        # Generate data profile
        profile = report_generator.generate_data_profile(
            dataset=dataset,
            user=user
        )
        
        logger.info(f"Data profile report generated", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'success',
            'profile': profile
        }
        
    except Exception as exc:
        logger.error(f"Data profile report generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Data profile report generation failed'
        }


@shared_task
def generate_comparison_report(dataset_ids: List[int], user_id: int, comparison_type: str = 'statistical') -> Dict[str, Any]:
    """
    Generate comparison report between datasets
    
    Args:
        dataset_ids: List of dataset IDs to compare
        user_id: ID of user
        comparison_type: Type of comparison (statistical, visual, comprehensive)
        
    Returns:
        Dict with comparison report
    """
    try:
        logger.info(f"Generating comparison report for datasets {dataset_ids}", 
                   extra={'user_id': user_id, 'dataset_count': len(dataset_ids), 'comparison_type': comparison_type})
        
        # Get datasets and user
        datasets = Dataset.objects.filter(id__in=dataset_ids)
        user = User.objects.get(id=user_id)
        
        # Initialize services
        report_generator = ReportGenerator()
        
        # Generate comparison report
        report = report_generator.generate_comparison_report(
            datasets=list(datasets),
            user=user,
            comparison_type=comparison_type
        )
        
        logger.info(f"Comparison report generated", 
                   extra={'user_id': user_id, 'dataset_count': len(dataset_ids)})
        
        return {
            'status': 'success',
            'report': report
        }
        
    except Exception as exc:
        logger.error(f"Comparison report generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_ids': dataset_ids})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Comparison report generation failed'
        }


@shared_task
def cleanup_report_cache():
    """
    Clean up old report files and cache
    """
    try:
        logger.info("Starting report cache cleanup")
        
        # This would clean up old report files
        # Implementation depends on your file storage strategy
        
        logger.info("Report cache cleanup completed")
        
    except Exception as exc:
        logger.error(f"Report cache cleanup error: {str(exc)}")


@shared_task
def generate_report_metrics():
    """
    Generate report generation metrics
    """
    try:
        logger.info("Generating report metrics")
        
        # This would collect report generation metrics
        # Implementation depends on your monitoring setup
        
        logger.info("Report metrics generation completed")
        
    except Exception as exc:
        logger.error(f"Report metrics generation error: {str(exc)}")


@shared_task
def export_report_to_file(report_id: str, user_id: int, export_format: str = 'pdf') -> Dict[str, Any]:
    """
    Export report to file
    
    Args:
        report_id: ID of report
        user_id: ID of user
        export_format: Export format (pdf, html, json)
        
    Returns:
        Dict with export results
    """
    try:
        logger.info(f"Exporting report {report_id} to {export_format}", 
                   extra={'user_id': user_id, 'report_id': report_id, 'format': export_format})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        report_generator = ReportGenerator()
        
        # Export report
        export_result = report_generator.export_report(
            report_id=report_id,
            user=user,
            format=export_format
        )
        
        logger.info(f"Report exported successfully", 
                   extra={'user_id': user_id, 'report_id': report_id})
        
        return {
            'status': 'success',
            'export': export_result
        }
        
    except Exception as exc:
        logger.error(f"Report export failed: {str(exc)}", 
                    extra={'user_id': user_id, 'report_id': report_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Report export failed'
        }
