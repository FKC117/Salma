"""
Image Processing Celery Tasks
Handles background image processing, optimization, and analysis
"""

from celery import shared_task
from django.conf import settings
import logging
from typing import Dict, Any, Optional
import time
from pathlib import Path
import os
from PIL import Image, ImageOps
import io
import base64

from analytics.models import User
from analytics.services.image_manager import ImageManager
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.logging_service import StructuredLogger

logger = StructuredLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_uploaded_image(self, image_path: str, user_id: int, processing_options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process uploaded image in background
    
    Args:
        image_path: Path to uploaded image
        user_id: ID of user
        processing_options: Image processing options
        
    Returns:
        Dict with processing results
    """
    try:
        logger.info(f"Processing uploaded image for user {user_id}", 
                   extra={'user_id': user_id, 'image_path': image_path})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        image_manager = ImageManager()
        audit_manager = AuditTrailManager()
        
        # Process image
        start_time = time.time()
        
        result = image_manager.process_image(
            image_path=image_path,
            user=user,
            options=processing_options
        )
        
        processing_time = time.time() - start_time
        
        # Log audit trail
        audit_manager.log_action(
            user=user,
            action='image_processed',
            details={
                'image_path': image_path,
                'processing_time': processing_time,
                'original_size': result.get('original_size', 0),
                'processed_size': result.get('processed_size', 0),
                'format': result.get('format', 'unknown')
            }
        )
        
        logger.info(f"Image processing completed", 
                   extra={'user_id': user_id, 'processing_time': processing_time})
        
        return {
            'status': 'success',
            'result': result,
            'processing_time': processing_time
        }
        
    except Exception as exc:
        logger.error(f"Image processing failed: {str(exc)}", 
                    extra={'user_id': user_id, 'image_path': image_path})
        
        # Log audit trail for failure
        try:
            user = User.objects.get(id=user_id)
            audit_manager.log_action(
                user=user,
                action='image_processing_failed',
                details={
                    'image_path': image_path,
                    'error': str(exc),
                    'retry_count': self.request.retries
                }
            )
        except:
            pass
        
        # Retry if not max retries reached
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying image processing (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Image processing failed after maximum retries'
        }


@shared_task(bind=True, max_retries=1)
def optimize_image(self, image_path: str, user_id: int, optimization_level: str = 'medium') -> Dict[str, Any]:
    """
    Optimize image for web display
    
    Args:
        image_path: Path to image
        user_id: ID of user
        optimization_level: Optimization level (low, medium, high)
        
    Returns:
        Dict with optimization results
    """
    try:
        logger.info(f"Optimizing image for user {user_id}", 
                   extra={'user_id': user_id, 'image_path': image_path, 'level': optimization_level})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        image_manager = ImageManager()
        
        # Optimize image
        result = image_manager.optimize_image(
            image_path=image_path,
            user=user,
            level=optimization_level
        )
        
        logger.info(f"Image optimization completed", 
                   extra={'user_id': user_id, 'compression_ratio': result.get('compression_ratio', 0)})
        
        return {
            'status': 'success',
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"Image optimization failed: {str(exc)}", 
                    extra={'user_id': user_id, 'image_path': image_path})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Image optimization failed'
        }


@shared_task(bind=True, max_retries=1)
def generate_image_thumbnails(self, image_path: str, user_id: int, thumbnail_sizes: list = None) -> Dict[str, Any]:
    """
    Generate image thumbnails
    
    Args:
        image_path: Path to image
        user_id: ID of user
        thumbnail_sizes: List of thumbnail sizes [(width, height), ...]
        
    Returns:
        Dict with thumbnail generation results
    """
    try:
        if thumbnail_sizes is None:
            thumbnail_sizes = [(150, 150), (300, 300), (600, 600)]
        
        logger.info(f"Generating thumbnails for user {user_id}", 
                   extra={'user_id': user_id, 'image_path': image_path, 'sizes': thumbnail_sizes})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        image_manager = ImageManager()
        
        # Generate thumbnails
        result = image_manager.generate_thumbnails(
            image_path=image_path,
            user=user,
            sizes=thumbnail_sizes
        )
        
        logger.info(f"Thumbnail generation completed", 
                   extra={'user_id': user_id, 'thumbnail_count': len(result.get('thumbnails', []))})
        
        return {
            'status': 'success',
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"Thumbnail generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'image_path': image_path})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Thumbnail generation failed'
        }


@shared_task
def analyze_image_metadata(image_path: str, user_id: int) -> Dict[str, Any]:
    """
    Analyze image metadata
    
    Args:
        image_path: Path to image
        user_id: ID of user
        
    Returns:
        Dict with image metadata
    """
    try:
        logger.info(f"Analyzing image metadata for user {user_id}", 
                   extra={'user_id': user_id, 'image_path': image_path})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        image_manager = ImageManager()
        
        # Analyze metadata
        metadata = image_manager.analyze_metadata(
            image_path=image_path,
            user=user
        )
        
        logger.info(f"Image metadata analysis completed", 
                   extra={'user_id': user_id, 'image_path': image_path})
        
        return {
            'status': 'success',
            'metadata': metadata
        }
        
    except Exception as exc:
        logger.error(f"Image metadata analysis failed: {str(exc)}", 
                    extra={'user_id': user_id, 'image_path': image_path})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Image metadata analysis failed'
        }


@shared_task
def convert_image_format(image_path: str, user_id: int, target_format: str) -> Dict[str, Any]:
    """
    Convert image to different format
    
    Args:
        image_path: Path to image
        user_id: ID of user
        target_format: Target format (jpeg, png, webp, etc.)
        
    Returns:
        Dict with conversion results
    """
    try:
        logger.info(f"Converting image format for user {user_id}", 
                   extra={'user_id': user_id, 'image_path': image_path, 'target_format': target_format})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        image_manager = ImageManager()
        
        # Convert format
        result = image_manager.convert_format(
            image_path=image_path,
            user=user,
            target_format=target_format
        )
        
        logger.info(f"Image format conversion completed", 
                   extra={'user_id': user_id, 'original_format': result.get('original_format'), 
                          'target_format': target_format})
        
        return {
            'status': 'success',
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"Image format conversion failed: {str(exc)}", 
                    extra={'user_id': user_id, 'image_path': image_path})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Image format conversion failed'
        }


@shared_task
def cleanup_image_cache():
    """
    Clean up old image cache and temporary files
    """
    try:
        logger.info("Starting image cache cleanup")
        
        # This would clean up old image cache files
        # Implementation depends on your caching strategy
        
        logger.info("Image cache cleanup completed")
        
    except Exception as exc:
        logger.error(f"Image cache cleanup error: {str(exc)}")


@shared_task
def monitor_image_storage():
    """
    Monitor image storage usage and cleanup
    """
    try:
        logger.info("Monitoring image storage")
        
        # This would monitor image storage usage
        # Implementation depends on your storage monitoring
        
        logger.info("Image storage monitoring completed")
        
    except Exception as exc:
        logger.error(f"Image storage monitoring error: {str(exc)}")


@shared_task
def batch_process_images(image_paths: list, user_id: int, processing_options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process multiple images in batch
    
    Args:
        image_paths: List of image paths
        user_id: ID of user
        processing_options: Processing options
        
    Returns:
        Dict with batch processing results
    """
    try:
        logger.info(f"Batch processing images for user {user_id}", 
                   extra={'user_id': user_id, 'image_count': len(image_paths)})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        image_manager = ImageManager()
        
        # Process images in batch
        results = []
        for i, image_path in enumerate(image_paths):
            logger.info(f"Processing image {i+1}/{len(image_paths)}: {image_path}")
            
            result = image_manager.process_image(
                image_path=image_path,
                user=user,
                options=processing_options
            )
            
            results.append({
                'image_path': image_path,
                'result': result
            })
        
        logger.info(f"Batch image processing completed", 
                   extra={'user_id': user_id, 'processed_count': len(results)})
        
        return {
            'status': 'success',
            'results': results,
            'processed_count': len(results)
        }
        
    except Exception as exc:
        logger.error(f"Batch image processing failed: {str(exc)}", 
                    extra={'user_id': user_id, 'image_count': len(image_paths)})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Batch image processing failed'
        }
