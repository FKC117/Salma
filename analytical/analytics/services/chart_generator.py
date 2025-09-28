"""
Chart Generation Service
Handles creation of charts with proper matplotlib/seaborn styling for analysis results
"""

import base64
import io
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np

logger = logging.getLogger(__name__)

class ChartGenerator:
    """
    Service for generating charts with consistent styling and proper matplotlib/seaborn integration
    """
    
    def __init__(self):
        self.setup_matplotlib()
        self.setup_seaborn()
    
    def setup_matplotlib(self):
        """Configure matplotlib for consistent chart generation"""
        # Use Agg backend for server-side rendering
        matplotlib.use('Agg')
        
        # Set default style
        plt.style.use('default')
        
        # Configure matplotlib parameters
        plt.rcParams.update({
            'figure.figsize': (10, 6),
            'figure.dpi': 100,
            'savefig.dpi': 100,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1,
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 10,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'figure.titlesize': 14,
            'axes.grid': True,
            'grid.alpha': 0.3,
            'axes.facecolor': 'white',
            'figure.facecolor': 'white',
            'axes.edgecolor': '#333333',
            'axes.linewidth': 0.8,
            'xtick.color': '#333333',
            'ytick.color': '#333333',
            'text.color': '#333333',
            'axes.labelcolor': '#333333',
            'axes.titlecolor': '#333333',
        })
    
    def setup_seaborn(self):
        """Configure seaborn for consistent styling"""
        # Set seaborn style
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        
        # Configure seaborn parameters
        sns.set_context("notebook", font_scale=1.0)
    
    def generate_chart(
        self,
        chart_type: str,
        data: pd.DataFrame,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        title: str = "Chart",
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        color_column: Optional[str] = None,
        size_column: Optional[str] = None,
        hue_column: Optional[str] = None,
        style_column: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        dpi: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chart with the specified parameters
        
        Args:
            chart_type: Type of chart ('line', 'bar', 'scatter', 'histogram', 'box', 'heatmap', etc.)
            data: DataFrame containing the data
            x_column: Column name for x-axis
            y_column: Column name for y-axis
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            color_column: Column for color mapping
            size_column: Column for size mapping
            hue_column: Column for hue mapping (seaborn)
            style_column: Column for style mapping (seaborn)
            figsize: Figure size tuple (width, height)
            dpi: Dots per inch
            **kwargs: Additional chart-specific parameters
            
        Returns:
            Dictionary containing chart metadata and base64 encoded image
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
            
            # Generate chart based on type
            if chart_type == 'line':
                self._create_line_chart(ax, data, x_column, y_column, hue_column, **kwargs)
            elif chart_type == 'bar':
                self._create_bar_chart(ax, data, x_column, y_column, hue_column, **kwargs)
            elif chart_type == 'scatter':
                self._create_scatter_chart(ax, data, x_column, y_column, hue_column, size_column, **kwargs)
            elif chart_type == 'histogram':
                self._create_histogram(ax, data, x_column, hue_column, **kwargs)
            elif chart_type == 'box':
                self._create_box_plot(ax, data, x_column, y_column, hue_column, **kwargs)
            elif chart_type == 'heatmap':
                self._create_heatmap(ax, data, **kwargs)
            elif chart_type == 'violin':
                self._create_violin_plot(ax, data, x_column, y_column, hue_column, **kwargs)
            elif chart_type == 'pair':
                self._create_pair_plot(data, hue_column, **kwargs)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            # Set labels and title
            if x_label:
                ax.set_xlabel(x_label)
            elif x_column:
                ax.set_xlabel(x_column)
                
            if y_label:
                ax.set_ylabel(y_label)
            elif y_column:
                ax.set_ylabel(y_column)
                
            ax.set_title(title, fontweight='bold', pad=20)
            
            # Improve layout
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Clean up
            plt.close(fig)
            img_buffer.close()
            
            return {
                'success': True,
                'image_base64': img_base64,
                'width': figsize[0] * dpi,
                'height': figsize[1] * dpi,
                'dpi': dpi,
                'format': 'PNG',
                'chart_type': chart_type,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chart_type': chart_type
            }
    
    def _create_line_chart(self, ax, data, x_column, y_column, hue_column, **kwargs):
        """Create a line chart"""
        if hue_column and hue_column in data.columns:
            sns.lineplot(data=data, x=x_column, y=y_column, hue=hue_column, ax=ax, **kwargs)
        else:
            sns.lineplot(data=data, x=x_column, y=y_column, ax=ax, **kwargs)
    
    def _create_bar_chart(self, ax, data, x_column, y_column, hue_column, **kwargs):
        """Create a bar chart"""
        if hue_column and hue_column in data.columns:
            sns.barplot(data=data, x=x_column, y=y_column, hue=hue_column, ax=ax, **kwargs)
        else:
            sns.barplot(data=data, x=x_column, y=y_column, ax=ax, **kwargs)
    
    def _create_scatter_chart(self, ax, data, x_column, y_column, hue_column, size_column, **kwargs):
        """Create a scatter plot"""
        plot_kwargs = {}
        if hue_column and hue_column in data.columns:
            plot_kwargs['hue'] = hue_column
        if size_column and size_column in data.columns:
            plot_kwargs['size'] = size_column
            
        sns.scatterplot(data=data, x=x_column, y=y_column, ax=ax, **plot_kwargs, **kwargs)
    
    def _create_histogram(self, ax, data, x_column, hue_column, **kwargs):
        """Create a histogram"""
        if hue_column and hue_column in data.columns:
            sns.histplot(data=data, x=x_column, hue=hue_column, ax=ax, **kwargs)
        else:
            sns.histplot(data=data, x=x_column, ax=ax, **kwargs)
    
    def _create_box_plot(self, ax, data, x_column, y_column, hue_column, **kwargs):
        """Create a box plot"""
        if hue_column and hue_column in data.columns:
            sns.boxplot(data=data, x=x_column, y=y_column, hue=hue_column, ax=ax, **kwargs)
        else:
            sns.boxplot(data=data, x=x_column, y=y_column, ax=ax, **kwargs)
    
    def _create_heatmap(self, ax, data, **kwargs):
        """Create a heatmap"""
        # For heatmap, we typically use correlation matrix or pivot table
        if 'correlation' in kwargs and kwargs['correlation']:
            corr_matrix = data.corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax, **kwargs)
        else:
            # Use data as is for heatmap
            sns.heatmap(data, annot=True, ax=ax, **kwargs)
    
    def _create_violin_plot(self, ax, data, x_column, y_column, hue_column, **kwargs):
        """Create a violin plot"""
        if hue_column and hue_column in data.columns:
            sns.violinplot(data=data, x=x_column, y=y_column, hue=hue_column, ax=ax, **kwargs)
        else:
            sns.violinplot(data=data, x=x_column, y=y_column, ax=ax, **kwargs)
    
    def _create_pair_plot(self, data, hue_column, **kwargs):
        """Create a pair plot (returns figure, not axis)"""
        if hue_column and hue_column in data.columns:
            return sns.pairplot(data, hue=hue_column, **kwargs)
        else:
            return sns.pairplot(data, **kwargs)
    
    def generate_correlation_heatmap(
        self,
        data: pd.DataFrame,
        title: str = "Correlation Matrix",
        figsize: Tuple[int, int] = (10, 8),
        dpi: int = 100
    ) -> Dict[str, Any]:
        """Generate a correlation heatmap"""
        try:
            # Calculate correlation matrix
            corr_matrix = data.corr()
            
            # Create figure
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
            
            # Create heatmap
            sns.heatmap(
                corr_matrix,
                annot=True,
                cmap='coolwarm',
                center=0,
                square=True,
                ax=ax,
                cbar_kws={'shrink': 0.8}
            )
            
            ax.set_title(title, fontweight='bold', pad=20)
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=dpi, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Clean up
            plt.close(fig)
            img_buffer.close()
            
            return {
                'success': True,
                'image_base64': img_base64,
                'width': figsize[0] * dpi,
                'height': figsize[1] * dpi,
                'dpi': dpi,
                'format': 'PNG',
                'chart_type': 'heatmap',
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error generating correlation heatmap: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chart_type': 'heatmap'
            }
    
    def generate_distribution_plot(
        self,
        data: pd.DataFrame,
        column: str,
        plot_type: str = 'histogram',
        title: str = "Distribution Plot",
        figsize: Tuple[int, int] = (10, 6),
        dpi: int = 100
    ) -> Dict[str, Any]:
        """Generate a distribution plot for a single column"""
        try:
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
            
            if plot_type == 'histogram':
                sns.histplot(data=data, x=column, ax=ax, kde=True)
            elif plot_type == 'kde':
                sns.kdeplot(data=data, x=column, ax=ax)
            elif plot_type == 'box':
                sns.boxplot(data=data, y=column, ax=ax)
            elif plot_type == 'violin':
                sns.violinplot(data=data, y=column, ax=ax)
            else:
                raise ValueError(f"Unsupported distribution plot type: {plot_type}")
            
            ax.set_title(title, fontweight='bold', pad=20)
            ax.set_xlabel(column)
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=dpi, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Clean up
            plt.close(fig)
            img_buffer.close()
            
            return {
                'success': True,
                'image_base64': img_base64,
                'width': figsize[0] * dpi,
                'height': figsize[1] * dpi,
                'dpi': dpi,
                'format': 'PNG',
                'chart_type': plot_type,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error generating distribution plot: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chart_type': plot_type
            }
    
    def get_chart_config(self, chart_type: str) -> Dict[str, Any]:
        """Get default configuration for a chart type"""
        configs = {
            'line': {
                'figure_size': (10, 6),
                'dpi': 100,
                'background_color': 'White',
                'color_palette': 'husl',
                'style': 'whitegrid'
            },
            'bar': {
                'figure_size': (10, 6),
                'dpi': 100,
                'background_color': 'White',
                'color_palette': 'husl',
                'style': 'whitegrid'
            },
            'scatter': {
                'figure_size': (10, 6),
                'dpi': 100,
                'background_color': 'White',
                'color_palette': 'husl',
                'style': 'whitegrid'
            },
            'histogram': {
                'figure_size': (10, 6),
                'dpi': 100,
                'background_color': 'White',
                'color_palette': 'husl',
                'style': 'whitegrid'
            },
            'box': {
                'figure_size': (10, 6),
                'dpi': 100,
                'background_color': 'White',
                'color_palette': 'husl',
                'style': 'whitegrid'
            },
            'heatmap': {
                'figure_size': (10, 8),
                'dpi': 100,
                'background_color': 'White',
                'color_palette': 'coolwarm',
                'style': 'whitegrid'
            }
        }
        
        return configs.get(chart_type, configs['line'])
    
    def validate_chart_data(self, data: pd.DataFrame, x_column: str = None, y_column: str = None) -> Dict[str, Any]:
        """Validate data for chart generation"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if data.empty:
            validation_result['valid'] = False
            validation_result['errors'].append("Data is empty")
            return validation_result
        
        if x_column and x_column not in data.columns:
            validation_result['valid'] = False
            validation_result['errors'].append(f"X column '{x_column}' not found in data")
        
        if y_column and y_column not in data.columns:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Y column '{y_column}' not found in data")
        
        # Check for numeric columns
        if x_column and not pd.api.types.is_numeric_dtype(data[x_column]):
            validation_result['warnings'].append(f"X column '{x_column}' is not numeric")
        
        if y_column and not pd.api.types.is_numeric_dtype(data[y_column]):
            validation_result['warnings'].append(f"Y column '{y_column}' is not numeric")
        
        return validation_result


# Global instance
chart_generator = ChartGenerator()
