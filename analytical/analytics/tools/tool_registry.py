"""
Tool Registry Manager

This module provides a comprehensive tool registry system for managing and discovering
analysis tools in the analytical system. It handles tool registration, discovery,
validation, and execution coordination.
"""

import importlib
import inspect
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError

from analytics.models import AnalysisTool
from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for managing analysis tools
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self._tool_cache = {}
        self._tool_metadata = {}
        
        # Tool module mappings
        self.tool_modules = {
            'statistical': 'analytics.tools.statistical_tools',
            'visualization': 'analytics.tools.visualization_tools',
            'machine_learning': 'analytics.tools.ml_tools',
            'survival': 'analytics.tools.survival_tools'
        }
        
        # Tool categories and their descriptions
        self.categories = {
            'descriptive': {
                'name': 'Descriptive Statistics',
                'description': 'Tools for summarizing and describing data',
                'icon': 'fas fa-chart-bar'
            },
            'inferential': {
                'name': 'Inferential Statistics',
                'description': 'Tools for making inferences about populations',
                'icon': 'fas fa-calculator'
            },
            'regression': {
                'name': 'Regression Analysis',
                'description': 'Tools for modeling relationships between variables',
                'icon': 'fas fa-trending-up'
            },
            'clustering': {
                'name': 'Clustering',
                'description': 'Tools for grouping similar data points',
                'icon': 'fas fa-project-diagram'
            },
            'classification': {
                'name': 'Classification',
                'description': 'Tools for predicting categorical outcomes',
                'icon': 'fas fa-tags'
            },
            'time_series': {
                'name': 'Time Series',
                'description': 'Tools for analyzing temporal data',
                'icon': 'fas fa-clock'
            },
            'visualization': {
                'name': 'Visualization',
                'description': 'Tools for creating charts and graphs',
                'icon': 'fas fa-chart-line'
            },
            'data_quality': {
                'name': 'Data Quality',
                'description': 'Tools for assessing and improving data quality',
                'icon': 'fas fa-check-circle'
            },
            'survival': {
                'name': 'Survival Analysis',
                'description': 'Tools for analyzing time-to-event data',
                'icon': 'fas fa-heartbeat'
            },
            'custom': {
                'name': 'Custom Tools',
                'description': 'User-defined analysis tools',
                'icon': 'fas fa-cog'
            }
        }
    
    def discover_tools(self, module_name: str) -> List[Dict[str, Any]]:
        """
        Discover tools in a module
        
        Args:
            module_name: Name of the module to scan
            
        Returns:
            List of discovered tool metadata
        """
        try:
            module = importlib.import_module(module_name)
            tools = []
            
            # Get all classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, '__module__') and obj.__module__ == module_name:
                    # Check if it's a tool class (has static methods)
                    static_methods = [method for method in dir(obj) 
                                    if inspect.isfunction(getattr(obj, method, None)) 
                                    and not method.startswith('_')]
                    
                    if static_methods:
                        tool_info = {
                            'class_name': name,
                            'module_name': module_name,
                            'methods': static_methods,
                            'description': obj.__doc__ or f"{name} tool class",
                            'category': self._infer_category(module_name, name)
                        }
                        tools.append(tool_info)
            
            return tools
            
        except Exception as e:
            logger.error(f"Error discovering tools in {module_name}: {str(e)}")
            return []
    
    def _infer_category(self, module_name: str, class_name: str) -> str:
        """Infer tool category from module and class name"""
        if 'statistical' in module_name.lower():
            return 'descriptive'
        elif 'visualization' in module_name.lower():
            return 'visualization'
        elif 'ml' in module_name.lower() or 'machine' in module_name.lower():
            return 'classification'
        elif 'survival' in module_name.lower():
            return 'survival'
        else:
            return 'custom'
    
    def register_tool(self, tool_name: str, class_name: str, method_name: str,
                     module_name: str, category: str, description: str,
                     parameters_schema: Dict[str, Any], required_parameters: List[str],
                     optional_parameters: List[str], **kwargs) -> AnalysisTool:
        """
        Register a tool in the database
        
        Args:
            tool_name: Unique name for the tool
            class_name: Name of the tool class
            method_name: Name of the method to execute
            module_name: Name of the module containing the tool
            category: Tool category
            description: Tool description
            parameters_schema: JSON schema for parameters
            required_parameters: List of required parameters
            optional_parameters: List of optional parameters
            **kwargs: Additional tool attributes
            
        Returns:
            AnalysisTool instance
        """
        try:
            with transaction.atomic():
                # Create or update tool
                tool, created = AnalysisTool.objects.update_or_create(
                    name=tool_name,
                    defaults={
                        'display_name': kwargs.get('display_name', tool_name.replace('_', ' ').title()),
                        'description': description,
                        'category': category,
                        'langchain_tool_name': f"{tool_name}_{method_name}",
                        'tool_class': f"{module_name}.{class_name}",
                        'tool_function': method_name,
                        'parameters_schema': parameters_schema,
                        'required_parameters': required_parameters,
                        'optional_parameters': optional_parameters,
                        'is_active': kwargs.get('is_active', True),
                        'is_premium': kwargs.get('is_premium', False),
                        'execution_timeout': kwargs.get('execution_timeout', 300),
                        'memory_limit_mb': kwargs.get('memory_limit_mb', 512),
                        'min_columns': kwargs.get('min_columns', 1),
                        'max_columns': kwargs.get('max_columns', 1000),
                        'min_rows': kwargs.get('min_rows', 1),
                        'max_rows': kwargs.get('max_rows', 1000000),
                        'required_column_types': kwargs.get('required_column_types', []),
                        'output_types': kwargs.get('output_types', ['json']),
                        'version': kwargs.get('version', '1.0.0'),
                        'author': kwargs.get('author', 'System'),
                        'tags': kwargs.get('tags', []),
                        'documentation_url': kwargs.get('documentation_url', ''),
                    }
                )
                
                # Log registration
                self.audit_manager.log_system_action(
                    action_type='register_tool',
                    resource_type='tool',
                    resource_id=tool.id,
                    resource_name=tool.display_name,
                    action_description=f"Tool {'created' if created else 'updated'}: {tool_name}",
                    success=True
                )
                
                logger.info(f"Tool {'registered' if created else 'updated'}: {tool_name}")
                return tool
                
        except Exception as e:
            logger.error(f"Error registering tool {tool_name}: {str(e)}")
            raise ValidationError(f"Tool registration failed: {str(e)}")
    
    def get_tool(self, tool_name: str) -> Optional[AnalysisTool]:
        """
        Get a tool by name
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            AnalysisTool instance or None
        """
        try:
            return AnalysisTool.objects.get(name=tool_name, is_active=True)
        except AnalysisTool.DoesNotExist:
            return None
    
    def get_tools_by_category(self, category: str) -> List[AnalysisTool]:
        """
        Get all tools in a category
        
        Args:
            category: Tool category
            
        Returns:
            List of AnalysisTool instances
        """
        return AnalysisTool.objects.filter(category=category, is_active=True).order_by('display_name')
    
    def get_all_tools(self, include_inactive: bool = False) -> List[AnalysisTool]:
        """
        Get all tools
        
        Args:
            include_inactive: Whether to include inactive tools
            
        Returns:
            List of AnalysisTool instances
        """
        queryset = AnalysisTool.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('category', 'display_name')
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], 
                    user_id: int = None) -> Dict[str, Any]:
        """
        Execute a tool with given parameters
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            user_id: ID of the user executing the tool
            
        Returns:
            Tool execution result
        """
        try:
            # Get tool from database
            tool = self.get_tool(tool_name)
            if not tool:
                return {"error": f"Tool '{tool_name}' not found or inactive"}
            
            # Validate parameters
            validation_result = self.validate_parameters(tool, parameters)
            if not validation_result['valid']:
                return {"error": f"Parameter validation failed: {validation_result['errors']}"}
            
            # Import and execute tool
            module_name = tool.tool_class.split('.')[0] + '.' + tool.tool_class.split('.')[1]
            class_name = tool.tool_class.split('.')[-1]
            method_name = tool.tool_function
            
            module = importlib.import_module(module_name)
            tool_class = getattr(module, class_name)
            tool_method = getattr(tool_class, method_name)
            
            # Execute tool
            start_time = datetime.now()
            result = tool_method(**parameters)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Record usage
            tool.record_usage(success=True, execution_time=execution_time)
            
            # Log execution
            if user_id:
                self.audit_manager.log_user_action(
                    user_id=user_id,
                    action_type='execute_tool',
                    resource_type='tool',
                    resource_id=tool.id,
                    resource_name=tool.display_name,
                    action_description=f"Executed tool: {tool_name}",
                    success=True
                )
            
            return {
                'success': True,
                'result': result,
                'execution_time': execution_time,
                'tool_name': tool_name
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            
            # Record failed usage
            if 'tool' in locals():
                tool.record_usage(success=False)
            
            return {
                'success': False,
                'error': f"Tool execution failed: {str(e)}",
                'tool_name': tool_name
            }
    
    def validate_parameters(self, tool: AnalysisTool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters against tool schema
        
        Args:
            tool: AnalysisTool instance
            parameters: Parameters to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            
            # Check required parameters
            for param in tool.required_parameters:
                if param not in parameters:
                    errors.append(f"Required parameter '{param}' is missing")
            
            # Check parameter types and values
            schema = tool.parameters_schema
            for param_name, param_value in parameters.items():
                if param_name in schema:
                    param_schema = schema[param_name]
                    validation_result = self._validate_parameter_value(
                        param_name, param_value, param_schema
                    )
                    if not validation_result['valid']:
                        errors.extend(validation_result['errors'])
            
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error validating parameters: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Parameter validation error: {str(e)}"]
            }
    
    def _validate_parameter_value(self, param_name: str, value: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single parameter value against its schema"""
        errors = []
        
        # Type validation
        expected_type = schema.get('type')
        if expected_type:
            if expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Parameter '{param_name}' must be a string")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Parameter '{param_name}' must be a number")
            elif expected_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Parameter '{param_name}' must be a boolean")
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append(f"Parameter '{param_name}' must be an array")
            elif expected_type == 'object' and not isinstance(value, dict):
                errors.append(f"Parameter '{param_name}' must be an object")
        
        # Range validation for numbers
        if isinstance(value, (int, float)) and 'minimum' in schema:
            if value < schema['minimum']:
                errors.append(f"Parameter '{param_name}' must be >= {schema['minimum']}")
        if isinstance(value, (int, float)) and 'maximum' in schema:
            if value > schema['maximum']:
                errors.append(f"Parameter '{param_name}' must be <= {schema['maximum']}")
        
        # Enum validation
        if 'enum' in schema and value not in schema['enum']:
            errors.append(f"Parameter '{param_name}' must be one of: {schema['enum']}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """
        Get the schema for a tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool schema
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        
        return {
            'name': tool.name,
            'display_name': tool.display_name,
            'description': tool.description,
            'category': tool.category,
            'parameters_schema': tool.parameters_schema,
            'required_parameters': tool.required_parameters,
            'optional_parameters': tool.optional_parameters,
            'output_types': tool.output_types,
            'execution_timeout': tool.execution_timeout,
            'memory_limit_mb': tool.memory_limit_mb,
            'min_columns': tool.min_columns,
            'max_columns': tool.max_columns,
            'min_rows': tool.min_rows,
            'max_rows': tool.max_rows,
            'required_column_types': tool.required_column_types,
            'version': tool.version,
            'author': tool.author,
            'tags': tool.tags,
            'documentation_url': tool.documentation_url
        }
    
    def search_tools(self, query: str, category: str = None) -> List[AnalysisTool]:
        """
        Search for tools by name, description, or tags
        
        Args:
            query: Search query
            category: Optional category filter
            
        Returns:
            List of matching AnalysisTool instances
        """
        from django.db.models import Q
        
        queryset = AnalysisTool.objects.filter(is_active=True)
        
        if category:
            queryset = queryset.filter(category=category)
        
        # Search in name, display_name, description, and tags
        search_filter = (
            Q(name__icontains=query) |
            Q(display_name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )
        
        return queryset.filter(search_filter).order_by('display_name')
    
    def get_tool_categories(self) -> Dict[str, Dict[str, str]]:
        """
        Get all available tool categories
        
        Returns:
            Dictionary of categories with metadata
        """
        return self.categories
    
    def get_tool_usage_stats(self, tool_name: str = None) -> Dict[str, Any]:
        """
        Get usage statistics for tools
        
        Args:
            tool_name: Specific tool name (if None, get stats for all tools)
            
        Returns:
            Usage statistics
        """
        if tool_name:
            tool = self.get_tool(tool_name)
            if not tool:
                return {"error": f"Tool '{tool_name}' not found"}
            
            return {
                'tool_name': tool.name,
                'usage_count': tool.usage_count,
                'success_count': tool.success_count,
                'error_count': tool.error_count,
                'success_rate': tool.success_rate,
                'error_rate': tool.error_rate,
                'average_execution_time': tool.average_execution_time,
                'last_used': tool.last_used
            }
        else:
            # Get stats for all tools
            tools = self.get_all_tools()
            total_usage = sum(tool.usage_count for tool in tools)
            total_success = sum(tool.success_count for tool in tools)
            total_errors = sum(tool.error_count for tool in tools)
            
            return {
                'total_tools': len(tools),
                'total_usage': total_usage,
                'total_success': total_success,
                'total_errors': total_errors,
                'overall_success_rate': (total_success / total_usage * 100) if total_usage > 0 else 0,
                'most_used_tools': [
                    {
                        'name': tool.name,
                        'display_name': tool.display_name,
                        'usage_count': tool.usage_count
                    }
                    for tool in sorted(tools, key=lambda x: x.usage_count, reverse=True)[:10]
                ]
            }
    
    def auto_register_tools(self) -> Dict[str, Any]:
        """
        Automatically discover and register tools from all modules
        
        Returns:
            Registration summary
        """
        registration_summary = {
            'discovered': 0,
            'registered': 0,
            'updated': 0,
            'errors': 0,
            'details': []
        }
        
        for module_name in self.tool_modules.values():
            try:
                tools = self.discover_tools(module_name)
                registration_summary['discovered'] += len(tools)
                
                for tool_info in tools:
                    try:
                        # Create tool name from class and method
                        for method in tool_info['methods']:
                            tool_name = f"{tool_info['class_name'].lower()}_{method}"
                            
                            # Basic parameter schema (can be enhanced)
                            parameters_schema = {
                                'df': {'type': 'object', 'description': 'Input DataFrame'},
                                'columns': {'type': 'array', 'description': 'Column names', 'required': False}
                            }
                            
                            # Register tool
                            tool = self.register_tool(
                                tool_name=tool_name,
                                class_name=tool_info['class_name'],
                                method_name=method,
                                module_name=module_name,
                                category=tool_info['category'],
                                description=tool_info['description'],
                                parameters_schema=parameters_schema,
                                required_parameters=['df'],
                                optional_parameters=['columns']
                            )
                            
                            registration_summary['registered'] += 1
                            registration_summary['details'].append({
                                'tool_name': tool_name,
                                'status': 'registered',
                                'module': module_name
                            })
                            
                    except Exception as e:
                        registration_summary['errors'] += 1
                        registration_summary['details'].append({
                            'tool_name': f"{tool_info['class_name']}_{method}",
                            'status': 'error',
                            'error': str(e)
                        })
                        
            except Exception as e:
                logger.error(f"Error auto-registering tools from {module_name}: {str(e)}")
                registration_summary['errors'] += 1
        
        return registration_summary
