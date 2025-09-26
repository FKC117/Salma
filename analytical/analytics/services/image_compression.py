"""
Image Compression and Optimization Service

This service provides comprehensive image compression, optimization, and format conversion
for the analytical system. It handles various image formats, implements multiple compression
algorithms, and provides automatic optimization based on use case and quality requirements.
"""

import os
import io
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np
import hashlib
import base64

from analytics.models import GeneratedImage, User, AuditTrail
from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)


class ImageCompressionService:
    """
    Comprehensive image compression and optimization service
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self.media_root = Path(settings.MEDIA_ROOT)
        self.images_dir = self.media_root / 'images'
        self.compressed_dir = self.images_dir / 'compressed'
        self.thumbnails_dir = self.images_dir / 'thumbnails'
        
        # Create directories
        for directory in [self.images_dir, self.compressed_dir, self.thumbnails_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Compression settings
        self.compression_levels = {
            'ultra': {'quality': 30, 'optimize': True, 'progressive': True},
            'high': {'quality': 60, 'optimize': True, 'progressive': True},
            'medium': {'quality': 80, 'optimize': True, 'progressive': False},
            'low': {'quality': 95, 'optimize': False, 'progressive': False}
        }
        
        # Image size presets
        self.size_presets = {
            'thumbnail': (150, 150),
            'small': (300, 300),
            'medium': (600, 600),
            'large': (1200, 1200),
            'xlarge': (1920, 1080),
            'original': None
        }
        
        # Supported formats and their optimization settings
        self.format_settings = {
            'JPEG': {
                'extensions': ['.jpg', '.jpeg'],
                'lossy': True,
                'supports_transparency': False,
                'default_quality': 85,
                'optimization_options': ['quality', 'progressive', 'optimize']
            },
            'PNG': {
                'extensions': ['.png'],
                'lossy': False,
                'supports_transparency': True,
                'default_quality': 95,
                'optimization_options': ['compress_level', 'optimize']
            },
            'WEBP': {
                'extensions': ['.webp'],
                'lossy': True,
                'supports_transparency': True,
                'default_quality': 80,
                'optimization_options': ['quality', 'lossless']
            }
        }
        
        # Performance metrics
        self.metrics = {
            'images_compressed': 0,
            'bytes_saved': 0,
            'compression_ratio': 0.0,
            'processing_time': 0.0
        }
    
    def compress_image(self, image_path: str, compression_level: str = 'medium',
                      output_format: Optional[str] = None, 
                      target_size: Optional[Tuple[int, int]] = None,
                      preserve_transparency: bool = True) -> Dict[str, Any]:
        """
        Compress an image with specified settings
        
        Args:
            image_path: Path to the input image
            compression_level: Compression level ('ultra', 'high', 'medium', 'low')
            output_format: Output format ('JPEG', 'PNG', 'WEBP')
            target_size: Target size as (width, height) tuple
            preserve_transparency: Whether to preserve transparency
            
        Returns:
            Dict with compression results
        """
        try:
            start_time = time.time()
            
            # Load image
            with Image.open(image_path) as img:
                original_size = os.path.getsize(image_path)
                original_format = img.format
                
                # Convert to RGB if needed for JPEG
                if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    if preserve_transparency:
                        # Use PNG instead if transparency is needed
                        output_format = 'PNG'
                    else:
                        # Create white background
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                
                # Resize if target size specified
                if target_size:
                    img = self._resize_image(img, target_size)
                
                # Apply compression
                compressed_img = self._apply_compression(img, compression_level, output_format)
                
                # Save compressed image
                output_path = self._get_output_path(image_path, compression_level, output_format)
                compressed_img.save(output_path, **self._get_save_options(output_format, compression_level))
                
                # Calculate metrics
                compressed_size = os.path.getsize(output_path)
                compression_ratio = (original_size - compressed_size) / original_size
                processing_time = time.time() - start_time
                
                # Update metrics
                self.metrics['images_compressed'] += 1
                self.metrics['bytes_saved'] += (original_size - compressed_size)
                self.metrics['compression_ratio'] = compression_ratio
                self.metrics['processing_time'] += processing_time
                
                result = {
                    'success': True,
                    'original_path': image_path,
                    'compressed_path': output_path,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': compression_ratio,
                    'bytes_saved': original_size - compressed_size,
                    'processing_time': processing_time,
                    'original_format': original_format,
                    'output_format': output_format or original_format,
                    'compression_level': compression_level,
                    'target_size': target_size
                }
                
                logger.info(f"Image compressed: {compression_ratio:.2%} reduction, {result['bytes_saved']} bytes saved")
                return result
                
        except Exception as e:
            logger.error(f"Image compression failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'original_path': image_path
            }
    
    def _resize_image(self, img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        try:
            # Calculate new size maintaining aspect ratio
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            logger.error(f"Image resize failed: {str(e)}")
            return img
    
    def _apply_compression(self, img: Image.Image, compression_level: str, 
                          output_format: Optional[str]) -> Image.Image:
        """Apply compression to image"""
        try:
            # Get compression settings
            settings = self.compression_levels.get(compression_level, self.compression_levels['medium'])
            
            # Apply image enhancements based on compression level
            if compression_level in ['ultra', 'high']:
                # Apply slight sharpening for high compression
                img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            return img
            
        except Exception as e:
            logger.error(f"Compression application failed: {str(e)}")
            return img
    
    def _get_save_options(self, output_format: str, compression_level: str) -> Dict[str, Any]:
        """Get save options for the specified format and compression level"""
        settings = self.compression_levels.get(compression_level, self.compression_levels['medium'])
        
        if output_format == 'JPEG':
            return {
                'format': 'JPEG',
                'quality': settings['quality'],
                'optimize': settings['optimize'],
                'progressive': settings['progressive']
            }
        elif output_format == 'PNG':
            return {
                'format': 'PNG',
                'optimize': settings['optimize'],
                'compress_level': 9 if compression_level == 'ultra' else 6
            }
        elif output_format == 'WEBP':
            return {
                'format': 'WEBP',
                'quality': settings['quality'],
                'optimize': settings['optimize']
            }
        else:
            return {'format': output_format}
    
    def _get_output_path(self, original_path: str, compression_level: str, 
                        output_format: Optional[str]) -> str:
        """Generate output path for compressed image"""
        original_path = Path(original_path)
        base_name = original_path.stem
        extension = original_path.suffix
        
        if output_format:
            extension = f'.{output_format.lower()}'
        
        output_filename = f"{base_name}_{compression_level}{extension}"
        return str(self.compressed_dir / output_filename)
    
    def create_thumbnail(self, image_path: str, size_preset: str = 'thumbnail',
                        quality: int = 85) -> Dict[str, Any]:
        """
        Create a thumbnail of the image
        
        Args:
            image_path: Path to the input image
            size_preset: Size preset ('thumbnail', 'small', 'medium', 'large')
            quality: JPEG quality for thumbnails
            
        Returns:
            Dict with thumbnail creation results
        """
        try:
            start_time = time.time()
            
            # Get target size
            target_size = self.size_presets.get(size_preset)
            if not target_size:
                raise ValueError(f"Invalid size preset: {size_preset}")
            
            # Load and resize image
            with Image.open(image_path) as img:
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Create thumbnail path
                original_path = Path(image_path)
                thumbnail_filename = f"{original_path.stem}_{size_preset}.jpg"
                thumbnail_path = str(self.thumbnails_dir / thumbnail_filename)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
                
                processing_time = time.time() - start_time
                
                result = {
                    'success': True,
                    'thumbnail_path': thumbnail_path,
                    'size_preset': size_preset,
                    'target_size': target_size,
                    'actual_size': img.size,
                    'processing_time': processing_time
                }
                
                logger.info(f"Thumbnail created: {size_preset} ({img.size})")
                return result
                
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'image_path': image_path
            }
    
    def batch_compress_images(self, image_paths: List[str], 
                             compression_level: str = 'medium',
                             output_format: Optional[str] = None) -> Dict[str, Any]:
        """
        Compress multiple images in batch
        
        Args:
            image_paths: List of image paths to compress
            compression_level: Compression level for all images
            output_format: Output format for all images
            
        Returns:
            Dict with batch compression results
        """
        try:
            start_time = time.time()
            results = []
            successful = 0
            failed = 0
            total_bytes_saved = 0
            
            for image_path in image_paths:
                result = self.compress_image(image_path, compression_level, output_format)
                results.append(result)
                
                if result['success']:
                    successful += 1
                    total_bytes_saved += result.get('bytes_saved', 0)
                else:
                    failed += 1
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'total_images': len(image_paths),
                'successful': successful,
                'failed': failed,
                'total_bytes_saved': total_bytes_saved,
                'processing_time': processing_time,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Batch compression failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total_images': len(image_paths)
            }
    
    def optimize_generated_image(self, generated_image: GeneratedImage,
                               compression_level: str = 'medium') -> Dict[str, Any]:
        """
        Optimize a GeneratedImage model instance
        
        Args:
            generated_image: GeneratedImage instance to optimize
            compression_level: Compression level to apply
            
        Returns:
            Dict with optimization results
        """
        try:
            # Get original image path
            original_path = generated_image.file_path
            if not os.path.exists(original_path):
                return {
                    'success': False,
                    'error': 'Original image file not found',
                    'image_id': generated_image.id
                }
            
            # Compress the image
            compression_result = self.compress_image(original_path, compression_level)
            
            if not compression_result['success']:
                return compression_result
            
            # Update the GeneratedImage record
            with transaction.atomic():
                generated_image.file_path = compression_result['compressed_path']
                generated_image.file_size_bytes = compression_result['compressed_size']
                generated_image.save(update_fields=['file_path', 'file_size_bytes'])
                
                # Create audit trail
                self.audit_manager.log_user_action(
                    user_id=generated_image.user.id,
                    action_type='optimize_image',
                    resource_type='image',
                    resource_id=generated_image.id,
                    resource_name=generated_image.name,
                    action_description=f"Optimized image with {compression_level} compression",
                    success=True
                )
            
            # Add optimization metadata
            optimization_result = compression_result.copy()
            optimization_result.update({
                'image_id': generated_image.id,
                'image_name': generated_image.name,
                'optimization_applied': True
            })
            
            logger.info(f"GeneratedImage {generated_image.id} optimized: {compression_result['compression_ratio']:.2%} reduction")
            return optimization_result
            
        except Exception as e:
            logger.error(f"GeneratedImage optimization failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'image_id': generated_image.id
            }
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        Get detailed information about an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict with image information
        """
        try:
            with Image.open(image_path) as img:
                file_size = os.path.getsize(image_path)
                
                return {
                    'path': image_path,
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'has_transparency': img.mode in ('RGBA', 'LA', 'P'),
                    'color_count': len(img.getcolors(maxcolors=256*256*256)) if img.mode == 'P' else None,
                    'dpi': img.info.get('dpi', (72, 72)),
                    'exif': img._getexif() if hasattr(img, '_getexif') else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get image info: {str(e)}")
            return {
                'error': str(e),
                'path': image_path
            }
    
    def convert_image_format(self, image_path: str, target_format: str,
                           quality: int = 85) -> Dict[str, Any]:
        """
        Convert image to different format
        
        Args:
            image_path: Path to the input image
            target_format: Target format ('JPEG', 'PNG', 'WEBP')
            quality: Quality setting for lossy formats
            
        Returns:
            Dict with conversion results
        """
        try:
            start_time = time.time()
            
            with Image.open(image_path) as img:
                original_size = os.path.getsize(image_path)
                
                # Handle format-specific conversions
                if target_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB for JPEG
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Generate output path
                original_path = Path(image_path)
                output_filename = f"{original_path.stem}.{target_format.lower()}"
                output_path = str(self.compressed_dir / output_filename)
                
                # Save in target format
                save_options = self._get_save_options(target_format, 'medium')
                save_options['quality'] = quality
                img.save(output_path, **save_options)
                
                converted_size = os.path.getsize(output_path)
                processing_time = time.time() - start_time
                
                return {
                    'success': True,
                    'original_path': image_path,
                    'converted_path': output_path,
                    'original_format': img.format,
                    'target_format': target_format,
                    'original_size': original_size,
                    'converted_size': converted_size,
                    'size_change': converted_size - original_size,
                    'processing_time': processing_time
                }
                
        except Exception as e:
            logger.error(f"Image format conversion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'image_path': image_path
            }
    
    def auto_optimize_image(self, image_path: str, target_size_mb: float = 1.0) -> Dict[str, Any]:
        """
        Automatically optimize image to target size
        
        Args:
            image_path: Path to the input image
            target_size_mb: Target size in MB
            
        Returns:
            Dict with auto-optimization results
        """
        try:
            target_size_bytes = target_size_mb * 1024 * 1024
            current_size = os.path.getsize(image_path)
            
            if current_size <= target_size_bytes:
                return {
                    'success': True,
                    'optimization_needed': False,
                    'current_size': current_size,
                    'target_size': target_size_bytes,
                    'message': 'Image already meets target size'
                }
            
            # Try different compression levels
            compression_levels = ['medium', 'high', 'ultra']
            
            for level in compression_levels:
                result = self.compress_image(image_path, level)
                
                if result['success'] and result['compressed_size'] <= target_size_bytes:
                    return {
                        'success': True,
                        'optimization_needed': True,
                        'compression_level': level,
                        'original_size': current_size,
                        'compressed_size': result['compressed_size'],
                        'target_size': target_size_bytes,
                        'compressed_path': result['compressed_path']
                    }
            
            # If still too large, try resizing
            with Image.open(image_path) as img:
                # Calculate resize factor
                resize_factor = (target_size_bytes / current_size) ** 0.5
                new_size = (int(img.width * resize_factor), int(img.height * resize_factor))
                
                result = self.compress_image(image_path, 'ultra', target_size=new_size)
                
                return {
                    'success': True,
                    'optimization_needed': True,
                    'compression_level': 'ultra',
                    'resize_applied': True,
                    'new_size': new_size,
                    'original_size': current_size,
                    'compressed_size': result['compressed_size'],
                    'target_size': target_size_bytes,
                    'compressed_path': result['compressed_path']
                }
                
        except Exception as e:
            logger.error(f"Auto-optimization failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'image_path': image_path
            }
    
    def cleanup_old_compressed_images(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Clean up old compressed images
        
        Args:
            days_old: Remove images older than this many days
            
        Returns:
            Dict with cleanup results
        """
        try:
            cutoff_time = timezone.now() - timezone.timedelta(days=days_old)
            cleaned_count = 0
            bytes_freed = 0
            
            # Clean up compressed images directory
            for file_path in self.compressed_dir.glob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time.replace(tzinfo=timezone.get_current_timezone()) < cutoff_time:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_count += 1
                        bytes_freed += file_size
            
            # Clean up thumbnails directory
            for file_path in self.thumbnails_dir.glob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time.replace(tzinfo=timezone.get_current_timezone()) < cutoff_time:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_count += 1
                        bytes_freed += file_size
            
            logger.info(f"Cleaned up {cleaned_count} old compressed images, freed {bytes_freed} bytes")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'bytes_freed': bytes_freed,
                'days_old': days_old
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """
        Get compression statistics
        
        Returns:
            Dict with compression statistics
        """
        return {
            'metrics': self.metrics.copy(),
            'compression_levels': list(self.compression_levels.keys()),
            'size_presets': list(self.size_presets.keys()),
            'supported_formats': list(self.format_settings.keys()),
            'directories': {
                'images': str(self.images_dir),
                'compressed': str(self.compressed_dir),
                'thumbnails': str(self.thumbnails_dir)
            },
            'timestamp': timezone.now().isoformat()
        }


# Global instance for easy access
image_compression_service = ImageCompressionService()


# Convenience functions for easy integration
def compress_image(image_path: str, compression_level: str = 'medium',
                 output_format: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to compress an image
    
    Args:
        image_path: Path to the input image
        compression_level: Compression level
        output_format: Output format
        
    Returns:
        Dict with compression results
    """
    return image_compression_service.compress_image(image_path, compression_level, output_format)


def create_thumbnail(image_path: str, size_preset: str = 'thumbnail') -> Dict[str, Any]:
    """
    Convenience function to create a thumbnail
    
    Args:
        image_path: Path to the input image
        size_preset: Size preset
        
    Returns:
        Dict with thumbnail creation results
    """
    return image_compression_service.create_thumbnail(image_path, size_preset)


def optimize_generated_image(generated_image: GeneratedImage, 
                           compression_level: str = 'medium') -> Dict[str, Any]:
    """
    Convenience function to optimize a GeneratedImage
    
    Args:
        generated_image: GeneratedImage instance
        compression_level: Compression level
        
    Returns:
        Dict with optimization results
    """
    return image_compression_service.optimize_generated_image(generated_image, compression_level)


def auto_optimize_image(image_path: str, target_size_mb: float = 1.0) -> Dict[str, Any]:
    """
    Convenience function to auto-optimize an image
    
    Args:
        image_path: Path to the input image
        target_size_mb: Target size in MB
        
    Returns:
        Dict with auto-optimization results
    """
    return image_compression_service.auto_optimize_image(image_path, target_size_mb)
