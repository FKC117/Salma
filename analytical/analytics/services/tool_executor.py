"""
Tool Executor Service
Handles execution of analysis tools and result generation
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
from analytics.services.tool_registry import tool_registry, AnalysisTool
from analytics.services.chart_generator import chart_generator
from analytics.services.analysis_result_manager import analysis_result_manager

logger = logging.getLogger(__name__)

class ToolExecutionResult:
    """Result of tool execution"""
    
    def __init__(self, execution_id: str, tool_id: str, success: bool, 
                 result_data: Dict[str, Any] = None, error_message: str = None):
        self.execution_id = execution_id
        self.tool_id = tool_id
        self.success = success
        self.result_data = result_data or {}
        self.error_message = error_message
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_id': self.execution_id,
            'tool_id': self.tool_id,
            'success': self.success,
            'result_data': self.result_data,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat()
        }

class ToolExecutor:
    """
    Service for executing analysis tools and generating results
    """
    
    def __init__(self):
        self.tool_registry = tool_registry
        self.chart_generator = chart_generator
        self.analysis_result_manager = analysis_result_manager
        self.execution_history: Dict[str, ToolExecutionResult] = {}
    
    def execute_tool(self, tool_id: str, parameters: Dict[str, Any], 
                    dataset: pd.DataFrame, session_id: str) -> ToolExecutionResult:
        """
        Execute an analysis tool with given parameters
        
        Args:
            tool_id: ID of the tool to execute
            parameters: Tool parameters
            dataset: Dataset to analyze
            session_id: Current analysis session ID
            
        Returns:
            ToolExecutionResult with execution details
        """
        execution_id = str(uuid.uuid4())
        
        try:
            # Get tool definition
            tool = self.tool_registry.get_tool(tool_id)
            if not tool:
                return ToolExecutionResult(
                    execution_id, tool_id, False, 
                    error_message=f"Tool {tool_id} not found"
                )
            
            # Validate parameters
            is_valid, errors = self.tool_registry.validate_tool_parameters(
                tool_id, parameters, dataset
            )
            if not is_valid:
                return ToolExecutionResult(
                    execution_id, tool_id, False,
                    error_message=f"Parameter validation failed: {'; '.join(errors)}"
                )
            
            # Execute tool based on type
            result_data = self._execute_tool_function(tool, parameters, dataset)
            
            # Store execution result
            execution_result = ToolExecutionResult(
                execution_id, tool_id, True, result_data
            )
            self.execution_history[execution_id] = execution_result
            
            logger.info(f"Tool {tool_id} executed successfully: {execution_id}")
            return execution_result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}", exc_info=True)
            execution_result = ToolExecutionResult(
                execution_id, tool_id, False,
                error_message=str(e)
            )
            self.execution_history[execution_id] = execution_result
            return execution_result
    
    def _execute_tool_function(self, tool: AnalysisTool, parameters: Dict[str, Any], 
                              dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute the specific tool function"""
        function_name = tool.execution_function
        
        if function_name == "execute_descriptive_stats":
            return self._execute_descriptive_stats(parameters, dataset)
        elif function_name == "execute_correlation_analysis":
            return self._execute_correlation_analysis(parameters, dataset)
        elif function_name == "execute_regression_analysis":
            return self._execute_regression_analysis(parameters, dataset)
        elif function_name == "execute_scatter_plot":
            return self._execute_scatter_plot(parameters, dataset)
        elif function_name == "execute_histogram":
            return self._execute_histogram(parameters, dataset)
        elif function_name == "execute_box_plot":
            return self._execute_box_plot(parameters, dataset)
        elif function_name == "execute_missing_data_analysis":
            return self._execute_missing_data_analysis(parameters, dataset)
        elif function_name == "execute_outlier_detection":
            return self._execute_outlier_detection(parameters, dataset)
        elif function_name == "execute_kmeans_clustering":
            return self._execute_kmeans_clustering(parameters, dataset)
        elif function_name == "execute_time_series_plot":
            return self._execute_time_series_plot(parameters, dataset)
        elif function_name == "execute_kaplan_meier":
            return self._execute_kaplan_meier(parameters, dataset)
        else:
            raise ValueError(f"Unknown tool function: {function_name}")
    
    def _execute_descriptive_stats(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute descriptive statistics analysis"""
        columns = parameters.get('columns', [])
        include_percentiles = parameters.get('include_percentiles', True)
        include_skewness = parameters.get('include_skewness', True)
        
        print(f"🔧 DEBUG: Descriptive stats parameters: {parameters}")
        print(f"🔧 DEBUG: Columns received: {columns}")
        print(f"🔧 DEBUG: Columns type: {type(columns)}")
        print(f"🔧 DEBUG: Dataset shape: {dataset.shape}")
        print(f"🔧 DEBUG: Dataset columns: {dataset.columns.tolist()}")
        
        if not columns:
            columns = dataset.select_dtypes(include=[np.number]).columns.tolist()
            print(f"🔧 DEBUG: Using all numeric columns: {columns}")
        
        print(f"🔧 DEBUG: Final columns to analyze: {columns}")
        print(f"🔧 DEBUG: Columns count: {len(columns)}")
        
        # Calculate descriptive statistics
        stats = dataset[columns].describe()
        print(f"🔧 DEBUG: Initial stats shape: {stats.shape}")
        print(f"🔧 DEBUG: Initial stats columns: {stats.columns.tolist()}")
        
        if include_percentiles:
            percentiles = dataset[columns].quantile([0.25, 0.5, 0.75])
            stats = pd.concat([stats, percentiles])
            print(f"🔧 DEBUG: After percentiles - stats shape: {stats.shape}")
        
        if include_skewness:
            skewness = dataset[columns].skew()
            kurtosis = dataset[columns].kurtosis()
            stats.loc['skewness'] = skewness
            stats.loc['kurtosis'] = kurtosis
            print(f"🔧 DEBUG: After skewness - stats shape: {stats.shape}")
        
        # Format results
        # Ensure stats is a DataFrame
        if isinstance(stats, pd.Series):
            stats = stats.to_frame().T
            print(f"🔧 DEBUG: Converted Series to DataFrame - shape: {stats.shape}")
        
        print(f"🔧 DEBUG: Final stats shape: {stats.shape}")
        print(f"🔧 DEBUG: Final stats columns: {stats.columns.tolist()}")
        print(f"🔧 DEBUG: Final stats index: {stats.index.tolist()}")
        
        # Transpose the data so variables are rows and statistics are columns
        stats_transposed = stats.T
        
        # Generate visualizations automatically
        print(f"🔧 DEBUG: About to generate visualizations for columns: {columns}")
        visualizations = self._generate_visualizations(dataset[columns], columns)
        print(f"🔧 DEBUG: Visualizations generated: {type(visualizations)}")
        print(f"🔧 DEBUG: Histograms count: {len(visualizations.get('histograms', {}))}")
        print(f"🔧 DEBUG: Box plots count: {len(visualizations.get('boxplots', {}))}")
        print(f"🔧 DEBUG: Outliers count: {len(visualizations.get('outliers', {}))}")
        
        result = {
            'type': 'table',
            'title': 'Descriptive Statistics',
            'description': f'Statistical summary for {len(columns)} numeric columns',
            'table_data': {
                'columns': stats_transposed.columns.tolist(),  # Statistics as columns
                'rows': stats_transposed.values.tolist()      # Variables as rows
            },
            'summary_stats': [
                {'label': 'Variables Analyzed', 'value': len(columns)},
                {'label': 'Total Rows', 'value': len(dataset)},
                {'label': 'Missing Values', 'value': int(dataset[columns].isnull().sum().sum())}
            ],
            'visualizations': visualizations
        }
        
        print(f"🔧 DEBUG: Final result visualizations: {type(result.get('visualizations', {}))}")
        print(f"🔧 DEBUG: Final result visualizations keys: {list(result.get('visualizations', {}).keys())}")
        
        print(f"🔧 DEBUG: Result table_data columns: {result['table_data']['columns']}")
        print(f"🔧 DEBUG: Result table_data rows count: {len(result['table_data']['rows'])}")
        print(f"🔧 DEBUG: First few rows: {result['table_data']['rows'][:3]}")
        
        return result
    
    def _generate_visualizations(self, data: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """Generate histograms, box plots, and outlier detection automatically"""
        try:
            print(f"🔧 DEBUG: Starting visualization generation for {len(columns)} columns")
            import matplotlib.pyplot as plt
            import seaborn as sns
            import io
            import base64
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            
            # Set style for better looking charts
            plt.style.use('default')
            sns.set_palette("husl")
            
            visualizations = {
                'histograms': {},
                'boxplots': {},
                'outliers': {}
            }
            
            for i, column in enumerate(columns):
                if column in data.columns:
                    print(f"🔧 DEBUG: Processing column {i+1}/{len(columns)}: {column}")
                    
                    # Generate histogram
                    fig, ax = plt.subplots(figsize=(8, 6))
                    data[column].hist(bins=30, ax=ax, alpha=0.7, color='skyblue', edgecolor='black')
                    ax.set_title(f'Histogram of {column}', fontsize=14, fontweight='bold')
                    ax.set_xlabel(column, fontsize=12)
                    ax.set_ylabel('Frequency', fontsize=12)
                    ax.grid(True, alpha=0.3)
                    
                    # Convert to base64
                    buffer = io.BytesIO()
                    FigureCanvasAgg(fig).print_png(buffer)
                    buffer.seek(0)
                    histogram_base64 = base64.b64encode(buffer.getvalue()).decode()
                    plt.close(fig)
                    
                    visualizations['histograms'][column] = histogram_base64
                    print(f"🔧 DEBUG: Generated histogram for {column} (base64 length: {len(histogram_base64)})")
                    
                    # Generate box plot
                    fig, ax = plt.subplots(figsize=(8, 6))
                    data[column].plot(kind='box', ax=ax, patch_artist=True, 
                                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                                    medianprops=dict(color='red', linewidth=2))
                    ax.set_title(f'Box Plot of {column}', fontsize=14, fontweight='bold')
                    ax.set_ylabel(column, fontsize=12)
                    ax.grid(True, alpha=0.3)
                    
                    # Convert to base64
                    buffer = io.BytesIO()
                    FigureCanvasAgg(fig).print_png(buffer)
                    buffer.seek(0)
                    boxplot_base64 = base64.b64encode(buffer.getvalue()).decode()
                    plt.close(fig)
                    
                    visualizations['boxplots'][column] = boxplot_base64
                    print(f"🔧 DEBUG: Generated box plot for {column} (base64 length: {len(boxplot_base64)})")
                    
                    # Detect outliers using IQR method
                    Q1 = data[column].quantile(0.25)
                    Q3 = data[column].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    outliers = data[(data[column] < lower_bound) | (data[column] > upper_bound)][column]
                    
                    visualizations['outliers'][column] = {
                        'iqr_outliers': outliers.tolist(),
                        'outlier_count': len(outliers),
                        'outlier_percentage': (len(outliers) / len(data)) * 100,
                        'bounds': {'lower': lower_bound, 'upper': upper_bound}
                    }
                    print(f"🔧 DEBUG: Detected {len(outliers)} outliers for {column}")
                else:
                    print(f"🔧 DEBUG: Column {column} not found in data")
            
            print(f"🔧 DEBUG: Generated visualizations for {len(columns)} variables")
            print(f"🔧 DEBUG: Histograms: {len(visualizations['histograms'])}")
            print(f"🔧 DEBUG: Box plots: {len(visualizations['boxplots'])}")
            print(f"🔧 DEBUG: Outliers: {len(visualizations['outliers'])}")
            return visualizations
            
        except Exception as e:
            print(f"🔧 DEBUG: Error generating visualizations: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'histograms': {}, 'boxplots': {}, 'outliers': {}}
    
    def _execute_correlation_analysis(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute correlation analysis"""
        columns = parameters.get('columns', [])
        method = parameters.get('method', 'pearson')
        include_visualization = parameters.get('include_visualization', True)
        
        # Calculate correlation matrix
        corr_matrix = dataset[columns].corr(method=method)
        
        result = {
            'type': 'chart',
            'title': f'Correlation Analysis ({method.title()})',
            'description': f'Correlation matrix for {len(columns)} variables',
            'chart_summary': {
                'type': 'Correlation Heatmap',
                'data_points': len(dataset),
                'variables': len(columns),
                'insights_count': 3
            }
        }
        
        if include_visualization:
            # Generate correlation heatmap
            chart_result = self.chart_generator.generate_correlation_heatmap(
                dataset[columns],
                title=f'Correlation Matrix ({method.title()})'
            )
            
            if chart_result['success']:
                result['chart_data'] = chart_result
        
        # Add correlation insights
        result['chart_insights'] = self._generate_correlation_insights(corr_matrix)
        
        return result
    
    def _execute_regression_analysis(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute regression analysis"""
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score, mean_squared_error
        from sklearn.model_selection import train_test_split
        
        target_column = parameters.get('target_column')
        feature_columns = parameters.get('feature_columns', [])
        include_plots = parameters.get('include_plots', True)
        
        # Prepare data
        X = dataset[feature_columns].dropna()
        y = dataset[target_column].loc[X.index]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Fit model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        r2 = r2_score(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        
        # Feature importance
        feature_importance = dict(zip(feature_columns, model.coef_))
        
        result = {
            'type': 'text',
            'title': 'Linear Regression Analysis',
            'description': f'Regression analysis with {len(feature_columns)} features',
            'detailed_analysis': f"""
            <h5>Model Performance</h5>
            <p><strong>R² Score:</strong> {r2:.4f}</p>
            <p><strong>RMSE:</strong> {rmse:.4f}</p>
            <p><strong>MSE:</strong> {mse:.4f}</p>
            
            <h5>Feature Importance</h5>
            <ul>
            {''.join([f'<li><strong>{feature}:</strong> {coef:.4f}</li>' for feature, coef in feature_importance.items()])}
            </ul>
            
            <h5>Model Interpretation</h5>
            <p>The model explains {r2*100:.1f}% of the variance in the target variable. 
            {'The model shows good predictive power.' if r2 > 0.7 else 'The model shows moderate predictive power.' if r2 > 0.5 else 'The model shows limited predictive power.'}</p>
            """,
            'key_insights': [
                {
                    'text': f'Model explains {r2*100:.1f}% of variance',
                    'confidence': min(95, max(60, r2 * 100))
                },
                {
                    'text': f'Most important feature: {max(feature_importance, key=feature_importance.get)}',
                    'confidence': 85
                }
            ]
        }
        
        return result
    
    def _execute_scatter_plot(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute scatter plot visualization"""
        x_column = parameters.get('x_column')
        y_column = parameters.get('y_column')
        color_column = parameters.get('color_column')
        size_column = parameters.get('size_column')
        title = parameters.get('title', 'Scatter Plot')
        
        # Generate scatter plot
        chart_result = self.chart_generator.generate_chart(
            chart_type='scatter',
            data=dataset,
            x_column=x_column,
            y_column=y_column,
            hue_column=color_column,
            size_column=size_column,
            title=title
        )
        
        result = {
            'type': 'chart',
            'title': title,
            'description': f'Scatter plot: {x_column} vs {y_column}',
            'chart_summary': {
                'type': 'Scatter Plot',
                'data_points': len(dataset),
                'variables': 2 + (1 if color_column else 0) + (1 if size_column else 0),
                'insights_count': 3
            }
        }
        
        if chart_result['success']:
            result['chart_data'] = chart_result
        
        return result
    
    def _execute_histogram(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute histogram visualization"""
        column = parameters.get('column')
        bins = parameters.get('bins', 30)
        include_kde = parameters.get('include_kde', True)
        title = parameters.get('title', 'Histogram')
        
        # Generate histogram
        chart_result = self.chart_generator.generate_distribution_plot(
            data=dataset,
            column=column,
            plot_type='histogram',
            title=title
        )
        
        result = {
            'type': 'chart',
            'title': title,
            'description': f'Distribution of {column}',
            'chart_summary': {
                'type': 'Histogram',
                'data_points': len(dataset),
                'variables': 1,
                'insights_count': 2
            }
        }
        
        if chart_result['success']:
            result['chart_data'] = chart_result
        
        return result
    
    def _execute_box_plot(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute box plot visualization"""
        y_column = parameters.get('y_column')
        x_column = parameters.get('x_column')
        title = parameters.get('title', 'Box Plot')
        
        # Generate box plot
        chart_result = self.chart_generator.generate_chart(
            chart_type='box',
            data=dataset,
            x_column=x_column,
            y_column=y_column,
            title=title
        )
        
        result = {
            'type': 'chart',
            'title': title,
            'description': f'Box plot for {y_column}' + (f' by {x_column}' if x_column else ''),
            'chart_summary': {
                'type': 'Box Plot',
                'data_points': len(dataset),
                'variables': 1 + (1 if x_column else 0),
                'insights_count': 2
            }
        }
        
        if chart_result['success']:
            result['chart_data'] = chart_result
        
        return result
    
    def _execute_missing_data_analysis(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute missing data analysis"""
        columns = parameters.get('columns', dataset.columns.tolist())
        include_visualization = parameters.get('include_visualization', True)
        
        # Calculate missing data statistics
        missing_data = dataset[columns].isnull().sum()
        missing_percentage = (missing_data / len(dataset)) * 100
        
        # Create missing data summary
        missing_summary = pd.DataFrame({
            'Column': columns,
            'Missing_Count': missing_data.values,
            'Missing_Percentage': missing_percentage.values
        }).sort_values('Missing_Percentage', ascending=False)
        
        result = {
            'type': 'table',
            'title': 'Missing Data Analysis',
            'description': f'Missing data analysis for {len(columns)} columns',
            'table_data': {
                'columns': missing_summary.columns.tolist(),
                'rows': missing_summary.values.tolist()
            },
            'data_quality': {
                'metrics': [
                    {
                        'name': 'Overall Completeness',
                        'score': round(100 - missing_percentage.mean(), 2),
                        'status': 'excellent' if missing_percentage.mean() < 5 else 'good' if missing_percentage.mean() < 15 else 'warning'
                    }
                ]
            }
        }
        
        return result
    
    def _execute_outlier_detection(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute outlier detection analysis"""
        columns = parameters.get('columns', [])
        method = parameters.get('method', 'iqr')
        threshold = parameters.get('threshold', 1.5)
        include_visualization = parameters.get('include_visualization', True)
        
        outliers = {}
        outlier_counts = {}
        
        for column in columns:
            if method == 'iqr':
                Q1 = dataset[column].quantile(0.25)
                Q3 = dataset[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                outliers[column] = (dataset[column] < lower_bound) | (dataset[column] > upper_bound)
            elif method == 'zscore':
                z_scores = np.abs((dataset[column] - dataset[column].mean()) / dataset[column].std())
                outliers[column] = z_scores > threshold
            elif method == 'isolation_forest':
                from sklearn.ensemble import IsolationForest
                model = IsolationForest(contamination=0.1, random_state=42)
                outliers[column] = model.fit_predict(dataset[[column]]) == -1
            
            outlier_counts[column] = outliers[column].sum()
        
        result = {
            'type': 'chart',
            'title': 'Outlier Detection Analysis',
            'description': f'Outlier detection using {method.upper()} method',
            'chart_summary': {
                'type': 'Outlier Analysis',
                'data_points': len(dataset),
                'variables': len(columns),
                'insights_count': 2
            },
            'chart_insights': [
                {
                    'title': 'Outlier Summary',
                    'description': f'Total outliers detected: {sum(outlier_counts.values())}',
                    'value': sum(outlier_counts.values())
                }
            ]
        }
        
        return result
    
    def _execute_kmeans_clustering(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute K-means clustering analysis"""
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        columns = parameters.get('columns', [])
        n_clusters = parameters.get('n_clusters', 3)
        include_visualization = parameters.get('include_visualization', True)
        
        # Prepare data
        X = dataset[columns].dropna()
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Add cluster labels to dataset
        X_with_clusters = X.copy()
        X_with_clusters['cluster'] = clusters
        
        result = {
            'type': 'chart',
            'title': 'K-Means Clustering Analysis',
            'description': f'Clustering analysis with {n_clusters} clusters',
            'chart_summary': {
                'type': 'Clustering',
                'data_points': len(X),
                'variables': len(columns),
                'insights_count': 3
            }
        }
        
        if include_visualization and len(columns) >= 2:
            # Generate scatter plot with clusters
            chart_result = self.chart_generator.generate_chart(
                chart_type='scatter',
                data=X_with_clusters,
                x_column=columns[0],
                y_column=columns[1],
                hue_column='cluster',
                title='K-Means Clustering Results'
            )
            
            if chart_result['success']:
                result['chart_data'] = chart_result
        
        return result
    
    def _execute_time_series_plot(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute time series plot visualization"""
        date_column = parameters.get('date_column')
        value_column = parameters.get('value_column')
        group_column = parameters.get('group_column')
        title = parameters.get('title', 'Time Series Plot')
        
        # Generate time series plot
        chart_result = self.chart_generator.generate_chart(
            chart_type='line',
            data=dataset,
            x_column=date_column,
            y_column=value_column,
            hue_column=group_column,
            title=title
        )
        
        result = {
            'type': 'chart',
            'title': title,
            'description': f'Time series plot: {value_column} over time',
            'chart_summary': {
                'type': 'Time Series',
                'data_points': len(dataset),
                'variables': 2 + (1 if group_column else 0),
                'insights_count': 2
            }
        }
        
        if chart_result['success']:
            result['chart_data'] = chart_result
        
        return result
    
    def _execute_kaplan_meier(self, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Dict[str, Any]:
        """Execute Kaplan-Meier survival analysis"""
        try:
            from lifelines import KaplanMeierFitter
            from lifelines.plotting import plot_lifetimes
            
            duration_column = parameters.get('duration_column')
            event_column = parameters.get('event_column')
            group_column = parameters.get('group_column')
            title = parameters.get('title', 'Kaplan-Meier Survival Curves')
            
            # Prepare data
            df_clean = dataset[[duration_column, event_column]].dropna()
            if group_column:
                df_clean[group_column] = dataset[group_column].loc[df_clean.index]
            
            # Fit Kaplan-Meier model
            kmf = KaplanMeierFitter()
            
            if group_column:
                # Multiple groups
                groups = df_clean[group_column].unique()
                result_data = {}
                
                for group in groups:
                    group_data = df_clean[df_clean[group_column] == group]
                    kmf.fit(group_data[duration_column], group_data[event_column], label=str(group))
                    result_data[group] = {
                        'median_survival': kmf.median_survival_time_,
                        'survival_at_1_year': kmf.survival_function_.iloc[-1, 0] if len(kmf.survival_function_) > 0 else 0
                    }
            else:
                # Single group
                kmf.fit(df_clean[duration_column], df_clean[event_column])
                result_data = {
                    'median_survival': kmf.median_survival_time_,
                    'survival_at_1_year': kmf.survival_function_.iloc[-1, 0] if len(kmf.survival_function_) > 0 else 0
                }
            
            result = {
                'type': 'chart',
                'title': title,
                'description': 'Kaplan-Meier survival analysis',
                'chart_summary': {
                    'type': 'Survival Analysis',
                    'data_points': len(df_clean),
                    'variables': 2 + (1 if group_column else 0),
                    'insights_count': 2
                },
                'statistical_summary': [
                    {
                        'name': 'Survival Statistics',
                        'stats': result_data
                    }
                ]
            }
            
        except ImportError:
            result = {
                'type': 'text',
                'title': 'Kaplan-Meier Survival Analysis',
                'description': 'Survival analysis requires lifelines library',
                'detailed_analysis': 'The lifelines library is required for survival analysis. Please install it using: pip install lifelines'
            }
        
        return result
    
    def _generate_correlation_insights(self, corr_matrix: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate insights from correlation matrix"""
        insights = []
        
        # Find strongest correlations
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if not np.isnan(corr_val):
                    corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], abs(corr_val)))
        
        corr_pairs.sort(key=lambda x: x[2], reverse=True)
        
        if corr_pairs:
            strongest = corr_pairs[0]
            insights.append({
                'title': 'Strongest Correlation',
                'description': f'{strongest[0]} and {strongest[1]} have a correlation of {strongest[2]:.3f}',
                'value': f'{strongest[2]:.3f}'
            })
        
        return insights
    
    def get_execution_result(self, execution_id: str) -> Optional[ToolExecutionResult]:
        """Get execution result by ID"""
        return self.execution_history.get(execution_id)
    
    def get_execution_history(self, session_id: str) -> List[ToolExecutionResult]:
        """Get execution history for a session"""
        # In a real implementation, this would filter by session_id
        return list(self.execution_history.values())


# Global instance
tool_executor = ToolExecutor()
