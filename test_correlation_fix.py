#!/usr/bin/env python
"""
Test script to verify the correlation analysis tool fix
"""

import os
import sys
import django
import pandas as pd
import numpy as np

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add analytical to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytical'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_correlation_analysis_fix():
    """Test that the correlation analysis tool works without the chart_data error"""
    print("Testing correlation analysis fix...")
    
    # Import required modules after Django setup
    from analytics.services.tool_executor import ToolExecutor
    from analytics.services.analysis_result_manager import AnalysisResultManager
    
    # Create a sample dataset with correlated variables
    np.random.seed(42)
    data = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100),
        'z': np.random.randn(100)
    })
    
    # Add some correlation between x and y
    data['y'] = data['x'] * 0.7 + np.random.randn(100) * 0.3
    
    print(f"Created sample dataset with columns: {list(data.columns)}")
    print(f"Dataset shape: {data.shape}")
    
    # Create tool executor and analysis result manager
    executor = ToolExecutor()
    result_manager = AnalysisResultManager()
    
    # Test correlation analysis execution
    parameters = {
        'columns': ['x', 'y', 'z'],
        'method': 'pearson',
        'include_visualization': True
    }
    
    print("\nExecuting correlation analysis...")
    try:
        result = executor._execute_correlation_analysis(parameters, data)
        print("✓ Correlation analysis executed successfully")
        print(f"Result type: {result.get('type')}")
        print(f"Result title: {result.get('title')}")
        print(f"Chart data present: {'chart_data' in result}")
        print(f"Chart summary present: {'chart_summary' in result}")
        
        # Test creating chart analysis result with the result
        print("\nCreating chart analysis result...")
        chart_html = result_manager.create_chart_analysis_result(
            analysis_id="test_correlation_001",
            title=result.get('title', 'Correlation Analysis'),
            description=result.get('description', 'Correlation matrix visualization'),
            chart_type='heatmap',
            data=data[['x', 'y', 'z']],
            chart_data=result.get('chart_data'),  # This should now work
            chart_summary=result.get('chart_summary')
        )
        print("✓ Chart analysis result created successfully")
        print(f"Chart HTML length: {len(chart_html)}")
        
        print("\n🎉 Correlation analysis tool fix verified successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error during correlation analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_correlation_analysis_fix()
    sys.exit(0 if success else 1)