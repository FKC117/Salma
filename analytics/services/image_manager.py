"""
Image Manager for Visualization Handling

This service handles image generation, storage, and management for data visualizations,
including chart generation, image optimization, and secure storage.
"""

import os
import io
import base64
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from PIL import Image, ImageOps
import hashlib

from analytics.models import GeneratedImage, User, AnalysisResult, AuditTrail
from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)


class ImageManager:
    """
    Service for managing visualization images and charts
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self.media_root = Path(settings.MEDIA_ROOT)
        self.images_dir = self.media_root / 'images'
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Image settings
        self.default_dpi = 100
        self.max_image_size = (1920, 1080)  # Max resolution
        self.supported_formats = ['PNG', 'JPEG', 'SVG', 'PDF']
        self.compression_quality = 85
        
        # Configure matplotlib
        plt.style.use('default')
        sns.set_style("darkgrid")
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['figure.dpi'] = self.default_dpi
        plt.rcParams['savefig.dpi'] = self.default_dpi
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.facecolor'] = '#1a1a1a'
        plt.rcParams['figure.facecolor'] = '#1a1a1a'
        plt.rcParams['text.color'] = '#e9ecef'
        plt.rcParams['axes.labelcolor'] = '#e9ecef'
        plt.rcParams['xtick.color'] = '#e9ecef'
        plt.rcParams['ytick.color'] = '#e9ecef'
    
    def generate_chart(self, chart_data: Dict[str, Any], chart_type: str = 'line',
                      user: User, analysis_result: Optional[AnalysisResult] = None,
                      custom_style: Optional[Dict[str, Any]] = None) -> GeneratedImage:
        """
        Generate a chart from data and save as image
        
        Args:
            chart_data: Data for chart generation
            chart_type: Type of chart (line, bar, scatter, histogram, heatmap, etc.)
            user: User generating the chart
            analysis_result: Associated analysis result
            custom_style: Custom styling options
            
        Returns:
            GeneratedImage object
        """
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=chart_data.get('figsize', (10, 6)))
            
            # Apply custom style if provided
            if custom_style:
                self._apply_custom_style(ax, custom_style)
            
            # Generate chart based on type
            if chart_type == 'line':
                self._create_line_chart(ax, chart_data)
            elif chart_type == 'bar':
                self._create_bar_chart(ax, chart_data)
            elif chart_type == 'scatter':
                self._create_scatter_chart(ax, chart_data)
            elif chart_type == 'histogram':
                self._create_histogram_chart(ax, chart_data)
            elif chart_type == 'heatmap':
                self._create_heatmap_chart(ax, chart_data)
            elif chart_type == 'boxplot':
                self._create_boxplot_chart(ax, chart_data)
            elif chart_type == 'pie':
                self._create_pie_chart(ax, chart_data)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            # Apply common styling
            self._apply_common_styling(ax, chart_data)
            
            # Save to bytes
            image_bytes = self._save_figure_to_bytes(fig, chart_data.get('format', 'PNG'))
            
            # Create image record
            image = self._create_image_record(
                image_bytes, chart_type, user, analysis_result, chart_data
            )
            
            # Save image file
            self._save_image_file(image, image_bytes)
            
            # Log audit trail
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='generate_image',
                resource_type='image',
                resource_id=image.id,
                resource_name=f"Chart: {chart_data.get('title', 'Untitled')}",
                action_description=f"Generated {chart_type} chart",
                success=True
            )
            
            logger.info(f"Generated {chart_type} chart for user {user.id}")
            return image
            
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}", exc_info=True)
            raise ValueError(f"Chart generation failed: {str(e)}")
        finally:
            plt.close('all')  # Clean up matplotlib figures
    
    def create_data_visualization(self, data: pd.DataFrame, visualization_config: Dict[str, Any],
                                user: User, analysis_result: Optional[AnalysisResult] = None) -> GeneratedImage:
        """
        Create a data visualization from DataFrame
        
        Args:
            data: Pandas DataFrame with data
            visualization_config: Configuration for visualization
            user: User creating visualization
            analysis_result: Associated analysis result
            
        Returns:
            GeneratedImage object
        """
        try:
            viz_type = visualization_config.get('type', 'auto')
            
            # Auto-detect visualization type if not specified
            if viz_type == 'auto':
                viz_type = self._auto_detect_visualization_type(data, visualization_config)
            
            # Prepare chart data
            chart_data = self._prepare_chart_data(data, visualization_config, viz_type)
            
            # Generate chart
            return self.generate_chart(
                chart_data=chart_data,
                chart_type=viz_type,
                user=user,
                analysis_result=analysis_result,
                custom_style=visualization_config.get('style')
            )
            
        except Exception as e:
            logger.error(f"Data visualization creation failed: {str(e)}")
            raise ValueError(f"Data visualization creation failed: {str(e)}")
    
    def optimize_image(self, image: GeneratedImage, max_width: int = 1920, 
                      max_height: int = 1080, quality: int = 85) -> bool:
        """
        Optimize image for web display
        
        Args:
            image: GeneratedImage object
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            quality: JPEG quality (1-100)
            
        Returns:
            True if optimization successful
        """
        try:
            # Load image
            image_path = self.media_root / image.file_path
            if not image_path.exists():
                return False
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Optimize
                img = ImageOps.exif_transpose(img)  # Fix orientation
                
                # Save optimized version
                img.save(image_path, format=image.image_format, quality=quality, optimize=True)
                
                # Update image record
                image.width, image.height = img.size
                image.file_size_bytes = image_path.stat().st_size
                image.save(update_fields=['width', 'height', 'file_size_bytes'])
                
                logger.info(f"Optimized image {image.id}")
                return True
                
        except Exception as e:
            logger.error(f"Image optimization failed: {str(e)}")
            return False
    
    def get_image_url(self, image: GeneratedImage) -> str:
        """Get public URL for image"""
        return f"{settings.MEDIA_URL}{image.file_path}"
    
    def get_image_base64(self, image: GeneratedImage) -> str:
        """Get base64 encoded image data"""
        try:
            image_path = self.media_root / image.file_path
            if not image_path.exists():
                return ""
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
                
        except Exception as e:
            logger.error(f"Failed to get base64 image: {str(e)}")
            return ""
    
    def delete_image(self, image_id: int, user: User) -> bool:
        """Delete image and associated file"""
        try:
            image = GeneratedImage.objects.get(id=image_id, user=user)
            
            # Delete file
            image_path = self.media_root / image.file_path
            if image_path.exists():
                image_path.unlink()
            
            # Delete record
            image.delete()
            
            # Log audit trail
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='delete_image',
                resource_type='image',
                resource_id=image_id,
                resource_name=image.name,
                action_description="Image deleted",
                success=True,
                data_changed=True
            )
            
            logger.info(f"Deleted image {image_id} for user {user.id}")
            return True
            
        except GeneratedImage.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to delete image: {str(e)}")
            return False
    
    def list_user_images(self, user: User, limit: int = 50) -> List[GeneratedImage]:
        """List images for a user"""
        return GeneratedImage.objects.filter(user=user).order_by('-created_at')[:limit]
    
    def _create_line_chart(self, ax, chart_data: Dict[str, Any]):
        """Create line chart"""
        x_data = chart_data.get('x', [])
        y_data = chart_data.get('y', [])
        
        if isinstance(y_data, list) and len(y_data) > 0 and isinstance(y_data[0], list):
            # Multiple series
            labels = chart_data.get('labels', [f'Series {i+1}' for i in range(len(y_data))])
            for i, series in enumerate(y_data):
                ax.plot(x_data, series, label=labels[i] if i < len(labels) else f'Series {i+1}')
            ax.legend()
        else:
            # Single series
            ax.plot(x_data, y_data)
    
    def _create_bar_chart(self, ax, chart_data: Dict[str, Any]):
        """Create bar chart"""
        x_data = chart_data.get('x', [])
        y_data = chart_data.get('y', [])
        
        if isinstance(y_data, list) and len(y_data) > 0 and isinstance(y_data[0], list):
            # Multiple series
            labels = chart_data.get('labels', [f'Series {i+1}' for i in range(len(y_data))])
            x_pos = np.arange(len(x_data))
            width = 0.8 / len(y_data)
            
            for i, series in enumerate(y_data):
                ax.bar(x_pos + i * width, series, width, label=labels[i] if i < len(labels) else f'Series {i+1}')
            ax.set_xticks(x_pos + width * (len(y_data) - 1) / 2)
            ax.set_xticklabels(x_data)
            ax.legend()
        else:
            # Single series
            ax.bar(x_data, y_data)
    
    def _create_scatter_chart(self, ax, chart_data: Dict[str, Any]):
        """Create scatter chart"""
        x_data = chart_data.get('x', [])
        y_data = chart_data.get('y', [])
        colors = chart_data.get('colors', None)
        sizes = chart_data.get('sizes', None)
        
        ax.scatter(x_data, y_data, c=colors, s=sizes, alpha=0.7)
    
    def _create_histogram_chart(self, ax, chart_data: Dict[str, Any]):
        """Create histogram chart"""
        data = chart_data.get('data', [])
        bins = chart_data.get('bins', 10)
        
        ax.hist(data, bins=bins, alpha=0.7, edgecolor='black')
    
    def _create_heatmap_chart(self, ax, chart_data: Dict[str, Any]):
        """Create heatmap chart"""
        data = chart_data.get('data', [])
        x_labels = chart_data.get('x_labels', [])
        y_labels = chart_data.get('y_labels', [])
        
        if isinstance(data, list) and len(data) > 0:
            # Convert to numpy array if needed
            data_array = np.array(data)
            
            im = ax.imshow(data_array, cmap='viridis', aspect='auto')
            ax.set_xticks(range(len(x_labels)))
            ax.set_yticks(range(len(y_labels)))
            ax.set_xticklabels(x_labels)
            ax.set_yticklabels(y_labels)
            
            # Add colorbar
            plt.colorbar(im, ax=ax)
    
    def _create_boxplot_chart(self, ax, chart_data: Dict[str, Any]):
        """Create boxplot chart"""
        data = chart_data.get('data', [])
        labels = chart_data.get('labels', [])
        
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            # Multiple series
            ax.boxplot(data, labels=labels)
        else:
            # Single series
            ax.boxplot(data)
    
    def _create_pie_chart(self, ax, chart_data: Dict[str, Any]):
        """Create pie chart"""
        data = chart_data.get('data', [])
        labels = chart_data.get('labels', [])
        colors = chart_data.get('colors', None)
        
        ax.pie(data, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    
    def _apply_common_styling(self, ax, chart_data: Dict[str, Any]):
        """Apply common styling to chart"""
        # Title
        if 'title' in chart_data:
            ax.set_title(chart_data['title'], fontsize=14, fontweight='bold', color='#e9ecef')
        
        # Labels
        if 'xlabel' in chart_data:
            ax.set_xlabel(chart_data['xlabel'], color='#e9ecef')
        if 'ylabel' in chart_data:
            ax.set_ylabel(chart_data['ylabel'], color='#e9ecef')
        
        # Grid
        ax.grid(True, alpha=0.3, color='#6c757d')
        
        # Spines
        ax.spines['bottom'].set_color('#6c757d')
        ax.spines['top'].set_color('#6c757d')
        ax.spines['right'].set_color('#6c757d')
        ax.spines['left'].set_color('#6c757d')
    
    def _apply_custom_style(self, ax, custom_style: Dict[str, Any]):
        """Apply custom styling options"""
        if 'color' in custom_style:
            ax.set_facecolor(custom_style['color'])
        if 'alpha' in custom_style:
            ax.set_alpha(custom_style['alpha'])
    
    def _save_figure_to_bytes(self, fig, format: str = 'PNG') -> bytes:
        """Save matplotlib figure to bytes"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format=format, bbox_inches='tight', 
                   facecolor='#1a1a1a', edgecolor='none', dpi=self.default_dpi)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_image_record(self, image_bytes: bytes, chart_type: str, 
                           user: User, analysis_result: Optional[AnalysisResult],
                           chart_data: Dict[str, Any]) -> GeneratedImage:
        """Create GeneratedImage record"""
        # Generate unique filename
        timestamp = int(timezone.now().timestamp())
        hash_suffix = hashlib.md5(image_bytes).hexdigest()[:8]
        filename = f"chart_{chart_type}_{timestamp}_{hash_suffix}.png"
        
        return GeneratedImage.objects.create(
            name=chart_data.get('title', f'{chart_type.title()} Chart'),
            description=chart_data.get('description', f'Generated {chart_type} chart'),
            image_format='PNG',
            width=chart_data.get('width', 1000),
            height=chart_data.get('height', 600),
            dpi=self.default_dpi,
            tool_used=analysis_result.tool_used if analysis_result else None,
            parameters_used=chart_data,
            analysis_result=analysis_result,
            user=user
        )
    
    def _save_image_file(self, image: GeneratedImage, image_bytes: bytes):
        """Save image file to storage"""
        # Create user-specific directory
        user_dir = self.images_dir / f"user_{image.user.id}"
        user_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = user_dir / f"image_{image.id}.png"
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        # Update image record
        image.file_path = f"images/user_{image.user.id}/image_{image.id}.png"
        image.file_size_bytes = len(image_bytes)
        image.save(update_fields=['file_path', 'file_size_bytes'])
    
    def _auto_detect_visualization_type(self, data: pd.DataFrame, config: Dict[str, Any]) -> str:
        """Auto-detect best visualization type for data"""
        if data.empty:
            return 'line'
        
        # Check data types and patterns
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns
        
        if len(numeric_cols) >= 2:
            if config.get('show_distribution', False):
                return 'histogram'
            elif config.get('show_correlation', False):
                return 'heatmap'
            else:
                return 'scatter'
        elif len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            return 'bar'
        elif len(categorical_cols) >= 2:
            return 'pie'
        else:
            return 'line'
    
    def _prepare_chart_data(self, data: pd.DataFrame, config: Dict[str, Any], 
                           viz_type: str) -> Dict[str, Any]:
        """Prepare chart data from DataFrame"""
        chart_data = {
            'title': config.get('title', f'{viz_type.title()} Chart'),
            'description': config.get('description', ''),
            'xlabel': config.get('xlabel', ''),
            'ylabel': config.get('ylabel', ''),
            'format': config.get('format', 'PNG'),
            'figsize': config.get('figsize', (10, 6))
        }
        
        if viz_type in ['line', 'bar', 'scatter']:
            x_col = config.get('x_column', data.columns[0] if len(data.columns) > 0 else None)
            y_cols = config.get('y_columns', [data.columns[1]] if len(data.columns) > 1 else [])
            
            if x_col and x_col in data.columns:
                chart_data['x'] = data[x_col].tolist()
            
            if y_cols:
                if len(y_cols) == 1:
                    chart_data['y'] = data[y_cols[0]].tolist()
                else:
                    chart_data['y'] = [data[col].tolist() for col in y_cols]
                    chart_data['labels'] = y_cols
        
        elif viz_type == 'histogram':
            col = config.get('column', data.columns[0] if len(data.columns) > 0 else None)
            if col and col in data.columns:
                chart_data['data'] = data[col].dropna().tolist()
                chart_data['bins'] = config.get('bins', 10)
        
        elif viz_type == 'heatmap':
            # Use correlation matrix for numeric columns
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                corr_matrix = numeric_data.corr()
                chart_data['data'] = corr_matrix.values.tolist()
                chart_data['x_labels'] = corr_matrix.columns.tolist()
                chart_data['y_labels'] = corr_matrix.index.tolist()
        
        elif viz_type == 'pie':
            col = config.get('column', data.columns[0] if len(data.columns) > 0 else None)
            if col and col in data.columns:
                value_counts = data[col].value_counts()
                chart_data['data'] = value_counts.values.tolist()
                chart_data['labels'] = value_counts.index.tolist()
        
        return chart_data
