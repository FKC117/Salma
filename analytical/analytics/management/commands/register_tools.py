"""
Management command to register all analysis tools in the database
"""

from django.core.management.base import BaseCommand
from analytics.models import AnalysisTool
from analytics.services.tool_registry import tool_registry

class Command(BaseCommand):
    help = 'Register all analysis tools in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-registration of all tools',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Get all tools from registry
        registry_tools = tool_registry.tools
        
        self.stdout.write(f"Found {len(registry_tools)} tools in registry")
        
        # Register each tool
        registered_count = 0
        updated_count = 0
        error_count = 0
        
        for tool_id, tool in registry_tools.items():
            try:
                # Check if tool already exists
                if not force:
                    try:
                        existing_tool = AnalysisTool.objects.get(name=tool_id)
                        # Update existing tool
                        existing_tool.display_name = tool.name
                        existing_tool.description = tool.description
                        existing_tool.category = tool.category.value
                        existing_tool.parameters_schema = self._convert_parameters(tool.parameters)
                        existing_tool.required_parameters = [p.name for p in tool.parameters if p.required]
                        existing_tool.optional_parameters = [p.name for p in tool.parameters if not p.required]
                        existing_tool.is_active = True
                        existing_tool.save()
                        updated_count += 1
                        self.stdout.write(f"Updated tool: {tool_id}")
                        continue
                    except AnalysisTool.DoesNotExist:
                        pass  # Tool doesn't exist, will create new one
                
                # Create or update tool in database
                tool_obj, created = AnalysisTool.objects.update_or_create(
                    name=tool_id,
                    defaults={
                        'display_name': tool.name,
                        'description': tool.description,
                        'category': tool.category.value,
                        'langchain_tool_name': f"{tool_id}_{tool.execution_function}",
                        'tool_class': f"analytics.tools.{tool.category.value}_tools.{tool.category.value.title()}Tools",
                        'tool_function': tool.execution_function,
                        'parameters_schema': self._convert_parameters(tool.parameters),
                        'required_parameters': [p.name for p in tool.parameters if p.required],
                        'optional_parameters': [p.name for p in tool.parameters if not p.required],
                        'required_column_types': tool.required_column_types or [],
                        'min_columns': tool.min_columns or 1,
                        'max_columns': tool.max_columns,
                        'is_active': True,
                        'output_types': [tool.result_type],
                        'tags': tool.tags or [],
                    }
                )
                
                if created:
                    registered_count += 1
                    self.stdout.write(f"Registered new tool: {tool_id}")
                else:
                    updated_count += 1
                    self.stdout.write(f"Updated existing tool: {tool_id}")
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(f"Error registering tool {tool_id}: {str(e)}")
        
        # Summary
        self.stdout.write(
            f"Successfully registered {registered_count} tools, "
            f"updated {updated_count} tools, "
            f"encountered {error_count} errors"
        )

    def _convert_parameters(self, parameters):
        """Convert tool parameters to schema format"""
        schema = {}
        for param in parameters:
            param_schema = {
                'type': param.type.value,
                'description': param.description,
                'required': param.required
            }
            
            if param.default_value is not None:
                param_schema['default'] = param.default_value
                
            if param.options:
                param_schema['enum'] = param.options
                
            if param.min_value is not None:
                param_schema['minimum'] = param.min_value
                
            if param.max_value is not None:
                param_schema['maximum'] = param.max_value
                
            schema[param.name] = param_schema
            
        return schema