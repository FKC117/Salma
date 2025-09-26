"""
File Processing Celery Tasks
Handles background file upload, validation, and processing operations
"""

from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
import numpy as np
import os
import hashlib
import mimetypes
from pathlib import Path
import logging
from typing import Dict, Any, Optional
import time

from analytics.models import Dataset, User
from analytics.services.file_processing import FileProcessingService
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.logging_service import StructuredLogger

logger = StructuredLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_uploaded_file(self, file_path: str, user_id: int, original_filename: str) -> Dict[str, Any]:
    """
    Process uploaded file in background
    
    Args:
        file_path: Path to uploaded file
        user_id: ID of user who uploaded the file
        original_filename: Original filename
        
    Returns:
        Dict with processing results
    """
    try:
        logger.info(f"Starting file processing for {original_filename}", 
                   extra={'user_id': user_id, 'file_path': file_path})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        file_service = FileProcessingService()
        audit_manager = AuditTrailManager()
        
        # Read file
        with default_storage.open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Check if file already exists
        existing_dataset = Dataset.objects.filter(file_hash=file_hash, user=user).first()
        if existing_dataset:
            logger.warning(f"File already exists: {original_filename}", 
                          extra={'user_id': user_id, 'dataset_id': existing_dataset.id})
            return {
                'status': 'duplicate',
                'dataset_id': existing_dataset.id,
                'message': 'File already exists'
            }
        
        # Detect file type
        file_type = mimetypes.guess_type(original_filename)[0]
        if not file_type:
            file_type = 'application/octet-stream'
        
        # Process file based on type
        if file_type.startswith('text/csv') or original_filename.endswith('.csv'):
            result = _process_csv_file(file_content, original_filename, user, file_hash)
        elif file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            result = _process_excel_file(file_content, original_filename, user, file_hash)
        elif file_type.startswith('text/') and original_filename.endswith('.json'):
            result = _process_json_file(file_content, original_filename, user, file_hash)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Create dataset record
        dataset = Dataset.objects.create(
            user=user,
            name=Path(original_filename).stem,
            description=f"Uploaded file: {original_filename}",
            original_filename=original_filename,
            file_size_bytes=len(file_content),
            file_hash=file_hash,
            original_format=file_type,
            parquet_path=result['parquet_path'],
            row_count=result.get('row_count', 0),
            column_count=result.get('column_count', 0),
            data_types=result.get('data_types', {}),
            processing_status='completed'
        )
        
        # Log audit trail
        audit_manager.log_action(
            user=user,
            action='file_processed',
            details={
                'filename': original_filename,
                'dataset_id': dataset.id,
                'file_size': len(file_content),
                'row_count': result.get('row_count', 0),
                'column_count': result.get('column_count', 0)
            }
        )
        
        logger.info(f"File processing completed: {original_filename}", 
                   extra={'user_id': user_id, 'dataset_id': dataset.id})
        
        return {
            'status': 'success',
            'dataset_id': dataset.id,
            'row_count': result.get('row_count', 0),
            'column_count': result.get('column_count', 0),
            'data_types': result.get('data_types', {})
        }
        
    except Exception as exc:
        logger.error(f"File processing failed: {str(exc)}", 
                    extra={'user_id': user_id, 'file_path': file_path})
        
        # Log audit trail for failure
        try:
            user = User.objects.get(id=user_id)
            audit_manager.log_action(
                user=user,
                action='file_processing_failed',
                details={
                    'filename': original_filename,
                    'error': str(exc),
                    'retry_count': self.request.retries
                }
            )
        except:
            pass
        
        # Retry if not max retries reached
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying file processing (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'File processing failed after maximum retries'
        }


def _process_csv_file(file_content: bytes, filename: str, user: User, file_hash: str) -> Dict[str, Any]:
    """Process CSV file"""
    try:
        # Read CSV
        df = pd.read_csv(ContentFile(file_content))
        
        # Clean data
        df = df.dropna(how='all')  # Remove completely empty rows
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
        
        # Convert to parquet
        parquet_filename = f"{file_hash}.parquet"
        parquet_path = f"datasets/{user.id}/{parquet_filename}"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(f"media/{parquet_path}"), exist_ok=True)
        
        # Save as parquet
        df.to_parquet(f"media/{parquet_path}", index=False)
        
        return {
            'parquet_path': parquet_path,
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
    except Exception as e:
        logger.error(f"CSV processing error: {str(e)}")
        raise


def _process_excel_file(file_content: bytes, filename: str, user: User, file_hash: str) -> Dict[str, Any]:
    """Process Excel file"""
    try:
        # Read Excel file
        df = pd.read_excel(ContentFile(file_content))
        
        # Clean data
        df = df.dropna(how='all')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Convert to parquet
        parquet_filename = f"{file_hash}.parquet"
        parquet_path = f"datasets/{user.id}/{parquet_filename}"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(f"media/{parquet_path}"), exist_ok=True)
        
        # Save as parquet
        df.to_parquet(f"media/{parquet_path}", index=False)
        
        return {
            'parquet_path': parquet_path,
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
    except Exception as e:
        logger.error(f"Excel processing error: {str(e)}")
        raise


def _process_json_file(file_content: bytes, filename: str, user: User, file_hash: str) -> Dict[str, Any]:
    """Process JSON file"""
    try:
        import json
        
        # Parse JSON
        data = json.loads(file_content.decode('utf-8'))
        
        # Convert to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.json_normalize(data)
        else:
            raise ValueError("Unsupported JSON structure")
        
        # Clean data
        df = df.dropna(how='all')
        
        # Convert to parquet
        parquet_filename = f"{file_hash}.parquet"
        parquet_path = f"datasets/{user.id}/{parquet_filename}"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(f"media/{parquet_path}"), exist_ok=True)
        
        # Save as parquet
        df.to_parquet(f"media/{parquet_path}", index=False)
        
        return {
            'parquet_path': parquet_path,
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
    except Exception as e:
        logger.error(f"JSON processing error: {str(e)}")
        raise


@shared_task(bind=True, max_retries=2)
def validate_file_format(self, file_path: str, user_id: int) -> Dict[str, Any]:
    """
    Validate file format and structure
    
    Args:
        file_path: Path to file to validate
        user_id: ID of user
        
    Returns:
        Dict with validation results
    """
    try:
        logger.info(f"Validating file format: {file_path}", extra={'user_id': user_id})
        
        with default_storage.open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Basic validation
        if len(file_content) == 0:
            return {'valid': False, 'error': 'File is empty'}
        
        if len(file_content) > 100 * 1024 * 1024:  # 100MB limit
            return {'valid': False, 'error': 'File too large (max 100MB)'}
        
        # Try to detect format
        try:
            # Try CSV
            pd.read_csv(ContentFile(file_content), nrows=5)
            return {'valid': True, 'format': 'csv'}
        except:
            pass
        
        try:
            # Try Excel
            pd.read_excel(ContentFile(file_content), nrows=5)
            return {'valid': True, 'format': 'excel'}
        except:
            pass
        
        try:
            # Try JSON
            import json
            json.loads(file_content.decode('utf-8'))
            return {'valid': True, 'format': 'json'}
        except:
            pass
        
        return {'valid': False, 'error': 'Unsupported file format'}
        
    except Exception as exc:
        logger.error(f"File validation error: {str(exc)}", extra={'user_id': user_id})
        return {'valid': False, 'error': str(exc)}


@shared_task
def cleanup_failed_uploads():
    """
    Clean up failed upload files
    """
    try:
        logger.info("Starting cleanup of failed uploads")
        
        # Find files older than 1 hour that haven't been processed
        cutoff_time = time.time() - 3600  # 1 hour ago
        
        # This would need to be implemented based on your file storage strategy
        # For now, just log the cleanup attempt
        logger.info("Cleanup completed")
        
    except Exception as exc:
        logger.error(f"Cleanup error: {str(exc)}")


@shared_task
def generate_file_metadata(dataset_id: int) -> Dict[str, Any]:
    """
    Generate additional metadata for a dataset
    
    Args:
        dataset_id: ID of dataset
        
    Returns:
        Dict with metadata
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        
        # Read parquet file
        parquet_path = f"media/{dataset.parquet_path}"
        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
        
        df = pd.read_parquet(parquet_path)
        
        # Generate metadata
        metadata = {
            'memory_usage': df.memory_usage(deep=True).sum(),
            'null_counts': df.isnull().sum().to_dict(),
            'unique_counts': df.nunique().to_dict(),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
            'datetime_columns': df.select_dtypes(include=['datetime']).columns.tolist()
        }
        
        # Update dataset with metadata
        dataset.metadata = metadata
        dataset.save()
        
        logger.info(f"Generated metadata for dataset {dataset_id}")
        
        return metadata
        
    except Exception as exc:
        logger.error(f"Metadata generation error: {str(exc)}")
        raise
