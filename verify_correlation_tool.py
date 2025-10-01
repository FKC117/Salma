#!/usr/bin/env python
"""
Verify that the correlation analysis tool is properly registered and working
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.analytical.settings')
django.setup()

def verify_correlation_tool():
    """Verify that the correlation analysis tool is properly registered"""
    print("Verifying correlation analysis tool registration...")
    
    try:
        # Import the tool registry
        from analytics.services.tool_registry import tool_registry
        
        # Check if correlation analysis tool is registered
        correlation_tool = tool_registry.get_tool('correlation_analysis')
        if correlation_tool:
            print("✓ Correlation analysis tool is registered")
            print(f"  Tool ID: {correlation_tool.id}")
            print(f"  Tool Name: {correlation_tool.name}")
            print(f"  Tool Category: {correlation_tool.category}")
            print(f"  Execution Function: {correlation_tool.execution_function}")
            print(f"  Result Type: {correlation_tool.result_type}")
            print(f"  Required Columns: {correlation_tool.min_columns} minimum")
            
            # Check parameters
            print(f"  Parameters:")
            for param in correlation_tool.parameters:
                print(f"    - {param.name}: {param.type} ({'required' if param.required else 'optional'})")
            
            return True
        else:
            print("✗ Correlation analysis tool is not registered")
            return False
            
    except Exception as e:
        print(f"✗ Error verifying correlation tool: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_correlation_tool()
    sys.exit(0 if success else 1)