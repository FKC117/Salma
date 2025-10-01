#!/usr/bin/env python
"""
Test script to verify correlation analysis tool execution
"""

import os
import sys
import django
import pandas as pd
import numpy as np

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.analytical.settings')
django.setup()

def test_correlation_tool_execution():
    """Test correlation analysis tool execution"""
    print("Testing correlation analysis tool execution...")
    
    try:
        # Import required modules
        from analytics.services.tool_executor import tool_executor
        from analytics.services.tool_registry import tool_registry
        
        # Create sample dataset with correlated variables
        np.random.seed(42)
        data = {
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        
        # Add correlation between x and y
        df['y'] = df['x'] * 0.7 + np.random.randn(100) * 0.3
        
        print(f"✓ Created sample dataset with {len(df)} rows and columns: {list(df.columns)}")
        
        # Get the correlation analysis tool
        correlation_tool = tool_registry.get_tool('correlation_analysis')
        if not correlation_tool:
            print("✗ Correlation analysis tool not found in registry")
            return False
            
        print(f"✓ Found correlation analysis tool: {correlation_tool.name}")
        
        # Test parameter validation
        parameters = {
            'columns': ['x', 'y', 'z'],
            'method': 'pearson',
            'include_visualization': True
        }
        
        is_valid, errors = tool_registry.validate_tool_parameters(
            'correlation_analysis',
            parameters,
            df
        )
        
        if is_valid:
            print("✓ Parameter validation passed")
        else:
            print(f"✗ Parameter validation failed: {errors}")
            return False
        
        # Execute the correlation analysis tool
        print("Executing correlation analysis...")
        result = tool_executor.execute_tool('correlation_analysis', parameters, df, None)
        
        if result:
            print("✓ Correlation analysis executed successfully")
            print(f"  Result type: {getattr(result, 'type', 'Unknown')}")
            print(f"  Result title: {getattr(result, 'title', 'Unknown')}")
            
            # Check if it's a successful result
            if hasattr(result, 'to_dict'):
                result_dict = result.to_dict()
                print(f"  Result dict keys: {list(result_dict.keys())}")
                
                # Check for chart data
                if 'chart_data' in result_dict:
                    print("✓ Chart data generated successfully")
                else:
                    print("ℹ Chart data not generated (may be expected)")
                    
                return True
            else:
                print("ℹ Result is not a ToolExecutionResult object")
                return True
        else:
            print("✗ Correlation analysis execution failed")
            return False
            
    except Exception as e:
        print(f"✗ Error during correlation tool execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_correlation_tool_execution()
    sys.exit(0 if success else 1)