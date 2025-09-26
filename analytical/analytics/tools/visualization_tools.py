"""
Visualization Tools

This module provides comprehensive visualization tools for the analytical system.
All tools are designed to work with pandas DataFrames and return standardized chart data.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from datetime import datetime
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class VisualizationTools:
    """
    Collection of visualization tools for data analysis
    """
    
    @staticmethod
    def line_chart(df: pd.DataFrame, x_column: str, y_columns: List[str], 
                   title: str = "Line Chart", xlabel: str = None, ylabel: str = None) -> Dict[str, Any]:
        """
        Create line chart data for multiple series
        
        Args:
            df: Input DataFrame
            x_column: Column for x-axis
            y_columns: List of columns for y-axis (multiple series)
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if x_column not in df.columns:
                return {"error": f"X column '{x_column}' not found in DataFrame"}
            
            missing_y_columns = [col for col in y_columns if col not in df.columns]
            if missing_y_columns:
                return {"error": f"Y columns not found: {missing_y_columns}"}
            
            # Prepare data
            x_data = df[x_column].tolist()
            y_data = []
            labels = []
            
            for col in y_columns:
                y_data.append(df[col].dropna().tolist())
                labels.append(col)
            
            return {
                'type': 'line_chart',
                'chart_data': {
                    'x': x_data,
                    'y': y_data,
                    'labels': labels,
                    'title': title,
                    'xlabel': xlabel or x_column,
                    'ylabel': ylabel or ', '.join(y_columns),
                    'figsize': (12, 8)
                },
                'metadata': {
                    'x_column': x_column,
                    'y_columns': y_columns,
                    'data_points': len(x_data),
                    'series_count': len(y_columns),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in line_chart: {str(e)}")
            return {"error": f"Line chart creation failed: {str(e)}"}
    
    @staticmethod
    def bar_chart(df: pd.DataFrame, x_column: str, y_column: str, 
                  title: str = "Bar Chart", xlabel: str = None, ylabel: str = None,
                  group_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Create bar chart data
        
        Args:
            df: Input DataFrame
            x_column: Column for x-axis (categories)
            y_column: Column for y-axis (values)
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            group_by: Optional column to group by (for grouped bar charts)
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if x_column not in df.columns or y_column not in df.columns:
                return {"error": "Specified columns not found in DataFrame"}
            
            if group_by and group_by not in df.columns:
                return {"error": f"Group column '{group_by}' not found in DataFrame"}
            
            if group_by:
                # Grouped bar chart
                grouped_data = df.groupby([x_column, group_by])[y_column].sum().unstack(fill_value=0)
                x_data = grouped_data.index.tolist()
                y_data = [grouped_data[col].tolist() for col in grouped_data.columns]
                labels = grouped_data.columns.tolist()
            else:
                # Simple bar chart
                x_data = df[x_column].tolist()
                y_data = [df[y_column].tolist()]
                labels = [y_column]
            
            return {
                'type': 'bar_chart',
                'chart_data': {
                    'x': x_data,
                    'y': y_data,
                    'labels': labels,
                    'title': title,
                    'xlabel': xlabel or x_column,
                    'ylabel': ylabel or y_column,
                    'figsize': (12, 8)
                },
                'metadata': {
                    'x_column': x_column,
                    'y_column': y_column,
                    'group_by': group_by,
                    'data_points': len(x_data),
                    'series_count': len(labels),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in bar_chart: {str(e)}")
            return {"error": f"Bar chart creation failed: {str(e)}"}
    
    @staticmethod
    def scatter_plot(df: pd.DataFrame, x_column: str, y_column: str, 
                     color_column: Optional[str] = None, size_column: Optional[str] = None,
                     title: str = "Scatter Plot", xlabel: str = None, ylabel: str = None) -> Dict[str, Any]:
        """
        Create scatter plot data
        
        Args:
            df: Input DataFrame
            x_column: Column for x-axis
            y_column: Column for y-axis
            color_column: Optional column for color mapping
            size_column: Optional column for size mapping
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if x_column not in df.columns or y_column not in df.columns:
                return {"error": "Specified columns not found in DataFrame"}
            
            # Prepare data
            x_data = df[x_column].dropna().tolist()
            y_data = df[y_column].dropna().tolist()
            
            # Ensure same length
            min_length = min(len(x_data), len(y_data))
            x_data = x_data[:min_length]
            y_data = y_data[:min_length]
            
            chart_data = {
                'x': x_data,
                'y': y_data,
                'title': title,
                'xlabel': xlabel or x_column,
                'ylabel': ylabel or y_column,
                'figsize': (10, 8)
            }
            
            # Add color mapping if specified
            if color_column and color_column in df.columns:
                color_data = df[color_column].dropna().tolist()[:min_length]
                chart_data['colors'] = color_data
            
            # Add size mapping if specified
            if size_column and size_column in df.columns:
                size_data = df[size_column].dropna().tolist()[:min_length]
                # Normalize size data to reasonable range
                size_data = np.array(size_data)
                size_data = (size_data - size_data.min()) / (size_data.max() - size_data.min()) * 100 + 10
                chart_data['sizes'] = size_data.tolist()
            
            return {
                'type': 'scatter_plot',
                'chart_data': chart_data,
                'metadata': {
                    'x_column': x_column,
                    'y_column': y_column,
                    'color_column': color_column,
                    'size_column': size_column,
                    'data_points': len(x_data),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in scatter_plot: {str(e)}")
            return {"error": f"Scatter plot creation failed: {str(e)}"}
    
    @staticmethod
    def histogram(df: pd.DataFrame, column: str, bins: int = 30, 
                  title: str = "Histogram", xlabel: str = None, ylabel: str = "Frequency") -> Dict[str, Any]:
        """
        Create histogram data
        
        Args:
            df: Input DataFrame
            column: Column to create histogram for
            bins: Number of bins
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if column not in df.columns:
                return {"error": f"Column '{column}' not found in DataFrame"}
            
            data = df[column].dropna()
            if len(data) == 0:
                return {"error": "No data available for histogram"}
            
            return {
                'type': 'histogram',
                'chart_data': {
                    'data': data.tolist(),
                    'bins': bins,
                    'title': title,
                    'xlabel': xlabel or column,
                    'ylabel': ylabel,
                    'figsize': (10, 6)
                },
                'metadata': {
                    'column': column,
                    'data_points': len(data),
                    'bins': bins,
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in histogram: {str(e)}")
            return {"error": f"Histogram creation failed: {str(e)}"}
    
    @staticmethod
    def box_plot(df: pd.DataFrame, column: str, group_by: Optional[str] = None,
                 title: str = "Box Plot", ylabel: str = None) -> Dict[str, Any]:
        """
        Create box plot data
        
        Args:
            df: Input DataFrame
            column: Column to create box plot for
            group_by: Optional column to group by
            title: Chart title
            ylabel: Y-axis label
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if column not in df.columns:
                return {"error": f"Column '{column}' not found in DataFrame"}
            
            if group_by and group_by not in df.columns:
                return {"error": f"Group column '{group_by}' not found in DataFrame"}
            
            if group_by:
                # Grouped box plot
                groups = df[group_by].unique()
                data = []
                labels = []
                
                for group in groups:
                    group_data = df[df[group_by] == group][column].dropna()
                    if len(group_data) > 0:
                        data.append(group_data.tolist())
                        labels.append(str(group))
            else:
                # Simple box plot
                data = [df[column].dropna().tolist()]
                labels = [column]
            
            return {
                'type': 'boxplot',
                'chart_data': {
                    'data': data,
                    'labels': labels,
                    'title': title,
                    'ylabel': ylabel or column,
                    'figsize': (10, 6)
                },
                'metadata': {
                    'column': column,
                    'group_by': group_by,
                    'groups': len(data),
                    'total_data_points': sum(len(group) for group in data),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in box_plot: {str(e)}")
            return {"error": f"Box plot creation failed: {str(e)}"}
    
    @staticmethod
    def pie_chart(df: pd.DataFrame, column: str, title: str = "Pie Chart") -> Dict[str, Any]:
        """
        Create pie chart data
        
        Args:
            df: Input DataFrame
            column: Column to create pie chart for
            title: Chart title
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if column not in df.columns:
                return {"error": f"Column '{column}' not found in DataFrame"}
            
            # Count values
            value_counts = df[column].value_counts()
            
            if len(value_counts) == 0:
                return {"error": "No data available for pie chart"}
            
            data = value_counts.values.tolist()
            labels = value_counts.index.tolist()
            
            return {
                'type': 'pie',
                'chart_data': {
                    'data': data,
                    'labels': labels,
                    'title': title,
                    'figsize': (8, 8)
                },
                'metadata': {
                    'column': column,
                    'categories': len(data),
                    'total_count': sum(data),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in pie_chart: {str(e)}")
            return {"error": f"Pie chart creation failed: {str(e)}"}
    
    @staticmethod
    def heatmap(df: pd.DataFrame, columns: Optional[List[str]] = None, 
                title: str = "Heatmap", cmap: str = 'viridis') -> Dict[str, Any]:
        """
        Create heatmap data for correlation matrix or data matrix
        
        Args:
            df: Input DataFrame
            columns: Specific columns to include (if None, all numeric columns)
            title: Chart title
            cmap: Color map for heatmap
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if columns is None:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            else:
                numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in ['int64', 'float64']]
            
            if len(numeric_cols) < 2:
                return {"error": "At least 2 numeric columns required for heatmap"}
            
            # Calculate correlation matrix
            corr_matrix = df[numeric_cols].corr()
            
            return {
                'type': 'heatmap',
                'chart_data': {
                    'data': corr_matrix.values.tolist(),
                    'x_labels': corr_matrix.columns.tolist(),
                    'y_labels': corr_matrix.index.tolist(),
                    'title': title,
                    'cmap': cmap,
                    'figsize': (max(8, len(numeric_cols)), max(6, len(numeric_cols)))
                },
                'metadata': {
                    'columns': numeric_cols,
                    'matrix_size': len(numeric_cols),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in heatmap: {str(e)}")
            return {"error": f"Heatmap creation failed: {str(e)}"}
    
    @staticmethod
    def time_series_plot(df: pd.DataFrame, time_column: str, value_columns: List[str],
                        title: str = "Time Series Plot", xlabel: str = None, ylabel: str = None) -> Dict[str, Any]:
        """
        Create time series plot data
        
        Args:
            df: Input DataFrame
            time_column: Column containing time/date data
            value_columns: List of columns containing values to plot
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if time_column not in df.columns:
                return {"error": f"Time column '{time_column}' not found in DataFrame"}
            
            missing_columns = [col for col in value_columns if col not in df.columns]
            if missing_columns:
                return {"error": f"Value columns not found: {missing_columns}"}
            
            # Sort by time column
            df_sorted = df.sort_values(time_column)
            
            # Prepare data
            x_data = df_sorted[time_column].tolist()
            y_data = []
            labels = []
            
            for col in value_columns:
                y_data.append(df_sorted[col].dropna().tolist())
                labels.append(col)
            
            return {
                'type': 'line_chart',  # Time series is essentially a line chart
                'chart_data': {
                    'x': x_data,
                    'y': y_data,
                    'labels': labels,
                    'title': title,
                    'xlabel': xlabel or time_column,
                    'ylabel': ylabel or ', '.join(value_columns),
                    'figsize': (14, 8)
                },
                'metadata': {
                    'time_column': time_column,
                    'value_columns': value_columns,
                    'data_points': len(x_data),
                    'series_count': len(value_columns),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in time_series_plot: {str(e)}")
            return {"error": f"Time series plot creation failed: {str(e)}"}
    
    @staticmethod
    def correlation_plot(df: pd.DataFrame, columns: Optional[List[str]] = None,
                        title: str = "Correlation Matrix", method: str = 'pearson') -> Dict[str, Any]:
        """
        Create correlation matrix plot data
        
        Args:
            df: Input DataFrame
            columns: Specific columns to include (if None, all numeric columns)
            title: Chart title
            method: Correlation method ('pearson', 'spearman', 'kendall')
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if columns is None:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            else:
                numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in ['int64', 'float64']]
            
            if len(numeric_cols) < 2:
                return {"error": "At least 2 numeric columns required for correlation plot"}
            
            # Calculate correlation matrix
            corr_matrix = df[numeric_cols].corr(method=method)
            
            return {
                'type': 'heatmap',
                'chart_data': {
                    'data': corr_matrix.values.tolist(),
                    'x_labels': corr_matrix.columns.tolist(),
                    'y_labels': corr_matrix.index.tolist(),
                    'title': f"{title} ({method.title()})",
                    'cmap': 'RdBu_r',
                    'figsize': (max(8, len(numeric_cols)), max(6, len(numeric_cols)))
                },
                'metadata': {
                    'columns': numeric_cols,
                    'method': method,
                    'matrix_size': len(numeric_cols),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in correlation_plot: {str(e)}")
            return {"error": f"Correlation plot creation failed: {str(e)}"}
    
    @staticmethod
    def distribution_plot(df: pd.DataFrame, column: str, plot_type: str = 'histogram',
                         title: str = "Distribution Plot", bins: int = 30) -> Dict[str, Any]:
        """
        Create distribution plot data (histogram, kde, or both)
        
        Args:
            df: Input DataFrame
            column: Column to plot distribution for
            plot_type: Type of plot ('histogram', 'kde', 'both')
            title: Chart title
            bins: Number of bins for histogram
            
        Returns:
            Dict containing chart data and metadata
        """
        try:
            if column not in df.columns:
                return {"error": f"Column '{column}' not found in DataFrame"}
            
            data = df[column].dropna()
            if len(data) == 0:
                return {"error": "No data available for distribution plot"}
            
            if plot_type == 'histogram':
                return VisualizationTools.histogram(df, column, bins, title)
            elif plot_type == 'kde':
                # For KDE, we'll return the data and let the frontend handle the plotting
                return {
                    'type': 'kde_plot',
                    'chart_data': {
                        'data': data.tolist(),
                        'title': title,
                        'xlabel': column,
                        'ylabel': 'Density',
                        'figsize': (10, 6)
                    },
                    'metadata': {
                        'column': column,
                        'data_points': len(data),
                        'plot_type': plot_type,
                        'created_at': datetime.now().isoformat()
                    }
                }
            elif plot_type == 'both':
                return {
                    'type': 'distribution_plot',
                    'chart_data': {
                        'data': data.tolist(),
                        'bins': bins,
                        'title': title,
                        'xlabel': column,
                        'ylabel': 'Density',
                        'figsize': (10, 6)
                    },
                    'metadata': {
                        'column': column,
                        'data_points': len(data),
                        'plot_type': plot_type,
                        'bins': bins,
                        'created_at': datetime.now().isoformat()
                    }
                }
            else:
                return {"error": f"Unknown plot type: {plot_type}"}
            
        except Exception as e:
            logger.error(f"Error in distribution_plot: {str(e)}")
            return {"error": f"Distribution plot creation failed: {str(e)}"}
