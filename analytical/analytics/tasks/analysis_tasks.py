"""
Analysis Execution Celery Tasks
Handles background analysis operations and tool execution
"""

from celery import shared_task
from django.conf import settings
import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, Any, Optional
import time
from pathlib import Path

from analytics.models import Dataset, User
from analytics.services.analysis_executor import AnalysisExecutor
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.logging_service import StructuredLogger
from analytics.tools.tool_registry import ToolRegistry

logger = StructuredLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def execute_analysis_task(self, dataset_id: int, tool_name: str, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    Execute analysis tool in background
    
    Args:
        dataset_id: ID of dataset to analyze
        tool_name: Name of analysis tool
        parameters: Tool parameters
        user_id: ID of user requesting analysis
        
    Returns:
        Dict with analysis results
    """
    try:
        logger.info(f"Starting analysis: {tool_name} on dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'tool_name': tool_name})
        
        # Get dataset and user
        dataset = Dataset.objects.get(id=dataset_id)
        user = User.objects.get(id=user_id)
        
        # Initialize services
        executor = AnalysisExecutor()
        audit_manager = AuditTrailManager()
        tool_registry = ToolRegistry()
        
        # Load dataset
        parquet_path = f"media/{dataset.parquet_path}"
        if not Path(parquet_path).exists():
            raise FileNotFoundError(f"Dataset file not found: {parquet_path}")
        
        df = pd.read_parquet(parquet_path)
        
        # Get tool from registry
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Execute analysis
        start_time = time.time()
        result = executor.execute_tool(tool, df, parameters, user)
        execution_time = time.time() - start_time
        
        # Log audit trail
        audit_manager.log_action(
            user=user,
            action='analysis_executed',
            details={
                'dataset_id': dataset_id,
                'tool_name': tool_name,
                'parameters': parameters,
                'execution_time': execution_time,
                'result_type': type(result).__name__
            }
        )
        
        logger.info(f"Analysis completed: {tool_name}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'execution_time': execution_time})
        
        return {
            'status': 'success',
            'tool_name': tool_name,
            'result': result,
            'execution_time': execution_time,
            'dataset_info': {
                'id': dataset_id,
                'name': dataset.name,
                'row_count': len(df),
                'column_count': len(df.columns)
            }
        }
        
    except Exception as exc:
        logger.error(f"Analysis execution failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id, 'tool_name': tool_name})
        
        # Log audit trail for failure
        try:
            user = User.objects.get(id=user_id)
            audit_manager.log_action(
                user=user,
                action='analysis_failed',
                details={
                    'dataset_id': dataset_id,
                    'tool_name': tool_name,
                    'error': str(exc),
                    'retry_count': self.request.retries
                }
            )
        except:
            pass
        
        # Retry if not max retries reached
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying analysis (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Analysis failed after maximum retries'
        }


@shared_task(bind=True, max_retries=1)
def execute_batch_analysis(self, dataset_id: int, tool_configs: list, user_id: int) -> Dict[str, Any]:
    """
    Execute multiple analysis tools in sequence
    
    Args:
        dataset_id: ID of dataset to analyze
        tool_configs: List of tool configurations [{'tool_name': str, 'parameters': dict}]
        user_id: ID of user requesting analysis
        
    Returns:
        Dict with batch results
    """
    try:
        logger.info(f"Starting batch analysis on dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'tool_count': len(tool_configs)})
        
        results = []
        total_start_time = time.time()
        
        for i, config in enumerate(tool_configs):
            tool_name = config['tool_name']
            parameters = config.get('parameters', {})
            
            logger.info(f"Executing tool {i+1}/{len(tool_configs)}: {tool_name}")
            
            # Execute individual analysis
            result = execute_analysis_task(dataset_id, tool_name, parameters, user_id)
            results.append({
                'tool_name': tool_name,
                'parameters': parameters,
                'result': result
            })
            
            # Check if we should stop on first failure
            if result.get('status') == 'error':
                logger.warning(f"Batch analysis stopped due to error in {tool_name}")
                break
        
        total_execution_time = time.time() - total_start_time
        
        logger.info(f"Batch analysis completed", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'total_time': total_execution_time})
        
        return {
            'status': 'success',
            'results': results,
            'total_execution_time': total_execution_time,
            'tools_executed': len(results)
        }
        
    except Exception as exc:
        logger.error(f"Batch analysis failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Batch analysis failed'
        }


@shared_task
def generate_analysis_report(dataset_id: int, analysis_results: list, user_id: int) -> Dict[str, Any]:
    """
    Generate comprehensive analysis report
    
    Args:
        dataset_id: ID of dataset
        analysis_results: List of analysis results
        user_id: ID of user
        
    Returns:
        Dict with report data
    """
    try:
        logger.info(f"Generating analysis report for dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        dataset = Dataset.objects.get(id=dataset_id)
        user = User.objects.get(id=user_id)
        
        # Load dataset for summary
        parquet_path = f"media/{dataset.parquet_path}"
        df = pd.read_parquet(parquet_path)
        
        # Generate report sections
        report = {
            'dataset_summary': {
                'name': dataset.name,
                'description': dataset.description,
                'row_count': len(df),
                'column_count': len(df.columns),
                'file_size': dataset.file_size_bytes,
                'upload_date': dataset.created_at.isoformat()
            },
            'data_overview': {
                'columns': list(df.columns),
                'data_types': df.dtypes.astype(str).to_dict(),
                'null_counts': df.isnull().sum().to_dict(),
                'memory_usage': df.memory_usage(deep=True).sum()
            },
            'analysis_results': analysis_results,
            'generated_at': time.time(),
            'generated_by': user.username
        }
        
        # Add statistical summaries for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            report['statistical_summary'] = df[numeric_cols].describe().to_dict()
        
        logger.info(f"Analysis report generated for dataset {dataset_id}")
        
        return {
            'status': 'success',
            'report': report
        }
        
    except Exception as exc:
        logger.error(f"Report generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Report generation failed'
        }


@shared_task
def validate_analysis_parameters(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate analysis tool parameters
    
    Args:
        tool_name: Name of tool
        parameters: Parameters to validate
        
    Returns:
        Dict with validation results
    """
    try:
        tool_registry = ToolRegistry()
        tool = tool_registry.get_tool(tool_name)
        
        if not tool:
            return {'valid': False, 'error': f'Tool not found: {tool_name}'}
        
        # Validate parameters
        validation_result = tool.validate_parameters(parameters)
        
        return {
            'valid': validation_result.get('valid', True),
            'errors': validation_result.get('errors', []),
            'warnings': validation_result.get('warnings', [])
        }
        
    except Exception as exc:
        logger.error(f"Parameter validation error: {str(exc)}")
        
        return {
            'valid': False,
            'error': str(exc)
        }


@shared_task
def cleanup_analysis_cache():
    """
    Clean up old analysis cache files
    """
    try:
        logger.info("Starting analysis cache cleanup")
        
        # This would clean up temporary analysis files
        # Implementation depends on your caching strategy
        
        logger.info("Analysis cache cleanup completed")
        
    except Exception as exc:
        logger.error(f"Cache cleanup error: {str(exc)}")


@shared_task
def monitor_analysis_performance():
    """
    Monitor analysis performance and log metrics
    """
    try:
        logger.info("Monitoring analysis performance")
        
        # This would collect performance metrics
        # Implementation depends on your monitoring setup
        
        logger.info("Analysis performance monitoring completed")
        
    except Exception as exc:
        logger.error(f"Performance monitoring error: {str(exc)}")
