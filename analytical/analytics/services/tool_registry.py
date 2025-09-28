"""
Tool Registry Service
Manages analysis tools, their configurations, and execution capabilities
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    """Analysis tool categories"""
    STATISTICAL = "statistical"
    VISUALIZATION = "visualization"
    MACHINE_LEARNING = "machine_learning"
    DATA_QUALITY = "data_quality"
    TIME_SERIES = "time_series"
    SURVIVAL_ANALYSIS = "survival_analysis"
    CUSTOM = "custom"

class ParameterType(Enum):
    """Parameter types for tool configuration"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTISELECT = "multiselect"
    COLUMN = "column"
    MULTICOLUMN = "multicolumn"
    DATE = "date"
    RANGE = "range"

@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: ParameterType
    label: str
    description: str
    required: bool = True
    default_value: Any = None
    options: List[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    validation_rules: List[str] = None

@dataclass
class AnalysisTool:
    """Analysis tool definition"""
    id: str
    name: str
    category: ToolCategory
    description: str
    parameters: List[ToolParameter]
    result_type: str  # 'text', 'table', 'chart'
    execution_function: str
    icon: str = "bi-graph-up"
    tags: List[str] = None
    min_columns: int = 1
    max_columns: int = None
    required_column_types: List[str] = None

class ToolRegistry:
    """
    Registry for managing analysis tools and their configurations
    """
    
    def __init__(self):
        self.tools: Dict[str, AnalysisTool] = {}
        self.categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
        print("🔧 DEBUG: Initializing ToolRegistry")
        self._initialize_default_tools()
        print(f"🔧 DEBUG: ToolRegistry initialized with {len(self.tools)} tools")
    
    def _initialize_default_tools(self):
        """Initialize default analysis tools"""
        print("🔧 DEBUG: Initializing default tools")
        self._add_statistical_tools()
        self._add_visualization_tools()
        self._add_data_quality_tools()
        self._add_machine_learning_tools()
        self._add_time_series_tools()
        self._add_survival_analysis_tools()
        print(f"🔧 DEBUG: Default tools initialized. Total tools: {len(self.tools)}")
    
    def _add_statistical_tools(self):
        """Add statistical analysis tools"""
        print("🔧 DEBUG: Adding statistical tools")
        # Descriptive Statistics
        self.register_tool(AnalysisTool(
            id="descriptive_stats",
            name="Descriptive Statistics",
            category=ToolCategory.STATISTICAL,
            description="Generate comprehensive descriptive statistics for numeric columns",
            parameters=[
                ToolParameter("columns", ParameterType.MULTICOLUMN, "Columns", "Select numeric columns to analyze", required=True),
                ToolParameter("include_percentiles", ParameterType.BOOLEAN, "Include Percentiles", "Include 25th, 50th, 75th percentiles", default_value=True),
                ToolParameter("include_skewness", ParameterType.BOOLEAN, "Include Skewness", "Include skewness and kurtosis", default_value=True),
            ],
            result_type="table",
            execution_function="execute_descriptive_stats",
            icon="bi-calculator",
            tags=["statistics", "summary", "numeric"],
            required_column_types=["numeric"]
        ))
        print("🔧 DEBUG: Descriptive stats tool registered")
        
        # Correlation Analysis
        self.register_tool(AnalysisTool(
            id="correlation_analysis",
            name="Correlation Analysis",
            category=ToolCategory.STATISTICAL,
            description="Calculate correlation matrix and generate heatmap visualization",
            parameters=[
                ToolParameter("columns", ParameterType.MULTICOLUMN, "Columns", "Select numeric columns for correlation analysis", required=True),
                ToolParameter("method", ParameterType.SELECT, "Correlation Method", "Correlation calculation method", 
                            options=["pearson", "spearman", "kendall"], default_value="pearson"),
                ToolParameter("include_visualization", ParameterType.BOOLEAN, "Include Heatmap", "Generate correlation heatmap", default_value=True),
            ],
            result_type="chart",
            execution_function="execute_correlation_analysis",
            icon="bi-diagram-3",
            tags=["correlation", "relationships", "numeric"],
            required_column_types=["numeric"],
            min_columns=2
        ))
        print("🔧 DEBUG: Correlation analysis tool registered")
        
        # Regression Analysis
        self.register_tool(AnalysisTool(
            id="regression_analysis",
            name="Regression Analysis",
            category=ToolCategory.STATISTICAL,
            description="Perform linear regression analysis between variables",
            parameters=[
                ToolParameter("target_column", ParameterType.COLUMN, "Target Variable", "Dependent variable for regression", required=True),
                ToolParameter("feature_columns", ParameterType.MULTICOLUMN, "Feature Variables", "Independent variables for regression", required=True),
                ToolParameter("include_plots", ParameterType.BOOLEAN, "Include Plots", "Generate residual and diagnostic plots", default_value=True),
            ],
            result_type="text",
            execution_function="execute_regression_analysis",
            icon="bi-graph-up-arrow",
            tags=["regression", "prediction", "relationships"],
            required_column_types=["numeric"],
            min_columns=2
        ))
    
    def _add_visualization_tools(self):
        """Add visualization tools"""
        # Scatter Plot
        self.register_tool(AnalysisTool(
            id="scatter_plot",
            name="Scatter Plot",
            category=ToolCategory.VISUALIZATION,
            description="Create scatter plot visualization between two variables",
            parameters=[
                ToolParameter("x_column", ParameterType.COLUMN, "X Variable", "Variable for x-axis", required=True),
                ToolParameter("y_column", ParameterType.COLUMN, "Y Variable", "Variable for y-axis", required=True),
                ToolParameter("color_column", ParameterType.COLUMN, "Color Variable", "Variable for color mapping (optional)", required=False),
                ToolParameter("size_column", ParameterType.COLUMN, "Size Variable", "Variable for size mapping (optional)", required=False),
                ToolParameter("title", ParameterType.STRING, "Chart Title", "Custom title for the chart", default_value="Scatter Plot"),
            ],
            result_type="chart",
            execution_function="execute_scatter_plot",
            icon="bi-scatter",
            tags=["scatter", "relationships", "visualization"],
            required_column_types=["numeric"],
            min_columns=2
        ))
        
        # Histogram
        self.register_tool(AnalysisTool(
            id="histogram",
            name="Histogram",
            category=ToolCategory.VISUALIZATION,
            description="Create histogram to show distribution of a variable",
            parameters=[
                ToolParameter("column", ParameterType.COLUMN, "Variable", "Variable to create histogram for", required=True),
                ToolParameter("bins", ParameterType.INTEGER, "Number of Bins", "Number of histogram bins", default_value=30, min_value=5, max_value=100),
                ToolParameter("include_kde", ParameterType.BOOLEAN, "Include KDE", "Include kernel density estimation", default_value=True),
                ToolParameter("title", ParameterType.STRING, "Chart Title", "Custom title for the chart", default_value="Histogram"),
            ],
            result_type="chart",
            execution_function="execute_histogram",
            icon="bi-bar-chart",
            tags=["histogram", "distribution", "visualization"],
            required_column_types=["numeric"]
        ))
        
        # Box Plot
        self.register_tool(AnalysisTool(
            id="box_plot",
            name="Box Plot",
            category=ToolCategory.VISUALIZATION,
            description="Create box plot to show distribution and outliers",
            parameters=[
                ToolParameter("y_column", ParameterType.COLUMN, "Y Variable", "Variable for y-axis", required=True),
                ToolParameter("x_column", ParameterType.COLUMN, "X Variable", "Grouping variable for x-axis (optional)", required=False),
                ToolParameter("title", ParameterType.STRING, "Chart Title", "Custom title for the chart", default_value="Box Plot"),
            ],
            result_type="chart",
            execution_function="execute_box_plot",
            icon="bi-box",
            tags=["boxplot", "distribution", "outliers"],
            required_column_types=["numeric"]
        ))
    
    def _add_data_quality_tools(self):
        """Add data quality analysis tools"""
        # Missing Data Analysis
        self.register_tool(AnalysisTool(
            id="missing_data_analysis",
            name="Missing Data Analysis",
            category=ToolCategory.DATA_QUALITY,
            description="Analyze missing data patterns and completeness",
            parameters=[
                ToolParameter("columns", ParameterType.MULTICOLUMN, "Columns", "Columns to analyze (leave empty for all)", required=False),
                ToolParameter("include_visualization", ParameterType.BOOLEAN, "Include Visualization", "Generate missing data heatmap", default_value=True),
            ],
            result_type="table",
            execution_function="execute_missing_data_analysis",
            icon="bi-exclamation-triangle",
            tags=["missing", "quality", "completeness"]
        ))
        
        # Outlier Detection
        self.register_tool(AnalysisTool(
            id="outlier_detection",
            name="Outlier Detection",
            category=ToolCategory.DATA_QUALITY,
            description="Detect outliers using statistical methods",
            parameters=[
                ToolParameter("columns", ParameterType.MULTICOLUMN, "Columns", "Numeric columns to analyze", required=True),
                ToolParameter("method", ParameterType.SELECT, "Detection Method", "Outlier detection method", 
                            options=["iqr", "zscore", "isolation_forest"], default_value="iqr"),
                ToolParameter("threshold", ParameterType.FLOAT, "Threshold", "Outlier detection threshold", default_value=1.5, min_value=0.1, max_value=5.0),
                ToolParameter("include_visualization", ParameterType.BOOLEAN, "Include Visualization", "Generate outlier plots", default_value=True),
            ],
            result_type="chart",
            execution_function="execute_outlier_detection",
            icon="bi-bullseye",
            tags=["outliers", "quality", "anomalies"],
            required_column_types=["numeric"]
        ))
    
    def _add_machine_learning_tools(self):
        """Add machine learning tools"""
        # K-Means Clustering
        self.register_tool(AnalysisTool(
            id="kmeans_clustering",
            name="K-Means Clustering",
            category=ToolCategory.MACHINE_LEARNING,
            description="Perform K-means clustering analysis",
            parameters=[
                ToolParameter("columns", ParameterType.MULTICOLUMN, "Features", "Numeric columns for clustering", required=True),
                ToolParameter("n_clusters", ParameterType.INTEGER, "Number of Clusters", "Number of clusters to create", default_value=3, min_value=2, max_value=10),
                ToolParameter("include_visualization", ParameterType.BOOLEAN, "Include Visualization", "Generate cluster visualization", default_value=True),
            ],
            result_type="chart",
            execution_function="execute_kmeans_clustering",
            icon="bi-diagram-2",
            tags=["clustering", "ml", "segmentation"],
            required_column_types=["numeric"],
            min_columns=2
        ))
    
    def _add_time_series_tools(self):
        """Add time series analysis tools"""
        # Time Series Plot
        self.register_tool(AnalysisTool(
            id="time_series_plot",
            name="Time Series Plot",
            category=ToolCategory.TIME_SERIES,
            description="Create time series visualization",
            parameters=[
                ToolParameter("date_column", ParameterType.COLUMN, "Date Column", "Column containing dates", required=True),
                ToolParameter("value_column", ParameterType.COLUMN, "Value Column", "Column containing values to plot", required=True),
                ToolParameter("group_column", ParameterType.COLUMN, "Group Column", "Column for grouping series (optional)", required=False),
                ToolParameter("title", ParameterType.STRING, "Chart Title", "Custom title for the chart", default_value="Time Series Plot"),
            ],
            result_type="chart",
            execution_function="execute_time_series_plot",
            icon="bi-graph-up",
            tags=["timeseries", "trends", "temporal"],
            required_column_types=["datetime", "numeric"]
        ))
    
    def _add_survival_analysis_tools(self):
        """Add survival analysis tools"""
        # Kaplan-Meier Survival Curve
        self.register_tool(AnalysisTool(
            id="kaplan_meier",
            name="Kaplan-Meier Survival Analysis",
            category=ToolCategory.SURVIVAL_ANALYSIS,
            description="Generate Kaplan-Meier survival curves",
            parameters=[
                ToolParameter("duration_column", ParameterType.COLUMN, "Duration Column", "Column containing survival times", required=True),
                ToolParameter("event_column", ParameterType.COLUMN, "Event Column", "Column indicating events (1) or censoring (0)", required=True),
                ToolParameter("group_column", ParameterType.COLUMN, "Group Column", "Column for grouping survival curves (optional)", required=False),
                ToolParameter("title", ParameterType.STRING, "Chart Title", "Custom title for the chart", default_value="Kaplan-Meier Survival Curves"),
            ],
            result_type="chart",
            execution_function="execute_kaplan_meier",
            icon="bi-heart-pulse",
            tags=["survival", "lifelines", "medical"],
            required_column_types=["numeric"]
        ))
    
    def register_tool(self, tool: AnalysisTool):
        """Register a new analysis tool"""
        self.tools[tool.id] = tool
        self.categories[tool.category].append(tool.id)
        print(f"🔧 DEBUG: Registered tool: {tool.name} ({tool.id}) in category {tool.category}")
        logger.info(f"Registered tool: {tool.name} ({tool.id})")
    
    def get_tool(self, tool_id: str) -> Optional[AnalysisTool]:
        """Get a tool by ID"""
        print(f"🔧 DEBUG: Getting tool with ID: {tool_id}")
        print(f"🔧 DEBUG: Available tools: {list(self.tools.keys())}")
        tool = self.tools.get(tool_id)
        print(f"🔧 DEBUG: Tool found: {tool is not None}")
        if tool:
            print(f"🔧 DEBUG: Tool name: {tool.name}")
            print(f"🔧 DEBUG: Tool parameters: {len(tool.parameters)}")
        return tool
    
    def get_tools_by_category(self, category: ToolCategory) -> List[AnalysisTool]:
        """Get all tools in a category"""
        return [self.tools[tool_id] for tool_id in self.categories[category] if tool_id in self.tools]
    
    def get_all_tools(self) -> List[AnalysisTool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def search_tools(self, query: str, category: Optional[ToolCategory] = None) -> List[AnalysisTool]:
        """Search tools by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        tools_to_search = self.get_tools_by_category(category) if category else self.get_all_tools()
        
        for tool in tools_to_search:
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower() or 
                any(query_lower in tag.lower() for tag in (tool.tags or []))):
                results.append(tool)
        
        return results
    
    def validate_tool_parameters(self, tool_id: str, parameters: Dict[str, Any], dataset: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate tool parameters against dataset"""
        tool = self.get_tool(tool_id)
        if not tool:
            return False, [f"Tool {tool_id} not found"]
        
        errors = []
        
        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in parameters:
                errors.append(f"Required parameter '{param.label}' is missing")
        
        # Validate column parameters
        for param in tool.parameters:
            if param.type in [ParameterType.COLUMN, ParameterType.MULTICOLUMN]:
                if param.name in parameters:
                    columns = parameters[param.name]
                    if isinstance(columns, str):
                        columns = [columns]
                    
                    # Check if columns exist in dataset
                    for col in columns:
                        if col not in dataset.columns:
                            errors.append(f"Column '{col}' not found in dataset")
                    
                    # Check column types if specified
                    if tool.required_column_types:
                        for col in columns:
                            if col in dataset.columns:
                                col_type = self._get_column_type(dataset[col])
                                if col_type not in tool.required_column_types:
                                    errors.append(f"Column '{col}' must be {', '.join(tool.required_column_types)} but is {col_type}")
        
        # Check column count constraints
        if tool.min_columns:
            total_columns = sum(len(parameters.get(param.name, [])) if isinstance(parameters.get(param.name), list) else 1 
                              for param in tool.parameters if param.type in [ParameterType.COLUMN, ParameterType.MULTICOLUMN] and param.name in parameters)
            if total_columns < tool.min_columns:
                errors.append(f"Tool requires at least {tool.min_columns} columns")
        
        if tool.max_columns:
            total_columns = sum(len(parameters.get(param.name, [])) if isinstance(parameters.get(param.name), list) else 1 
                              for param in tool.parameters if param.type in [ParameterType.COLUMN, ParameterType.MULTICOLUMN] and param.name in parameters)
            if total_columns > tool.max_columns:
                errors.append(f"Tool requires at most {tool.max_columns} columns")
        
        return len(errors) == 0, errors
    
    def _get_column_type(self, series: pd.Series) -> str:
        """Determine column type for validation"""
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        elif pd.api.types.is_categorical_dtype(series) or series.dtype == 'object':
            return "categorical"
        else:
            return "unknown"
    
    def get_tool_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get tools organized by category for UI display"""
        result = {}
        for category, tool_ids in self.categories.items():
            if tool_ids:  # Only include categories with tools
                tools = [self.tools[tool_id] for tool_id in tool_ids if tool_id in self.tools]
                result[category.value] = [
                    {
                        'id': tool.id,
                        'name': tool.name,
                        'description': tool.description,
                        'icon': tool.icon,
                        'tags': tool.tags or [],
                        'result_type': tool.result_type,
                        'parameters': [
                            {
                                'name': param.name,
                                'type': param.type.value,
                                'label': param.label,
                                'description': param.description,
                                'required': param.required,
                                'default_value': param.default_value,
                                'options': param.options,
                                'min_value': param.min_value,
                                'max_value': param.max_value
                            }
                            for param in tool.parameters
                        ]
                    }
                    for tool in tools
                ]
        return result


# Global instance
tool_registry = ToolRegistry()
