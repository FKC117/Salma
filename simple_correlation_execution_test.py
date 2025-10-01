#!/usr/bin/env python
"""
Simple test to verify correlation analysis tool execution without Django
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the analytical directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytical'))

def test_correlation_execution():
    """Test correlation analysis execution without Django"""
    print("Testing correlation analysis execution...")
    
    try:
        # Import the StatisticalTools directly
        from analytics.tools.statistical_tools import StatisticalTools
        
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
        
        # Execute correlation analysis directly
        print("Executing correlation analysis...")
        result = StatisticalTools.correlation_analysis(df, method='pearson', columns=['x', 'y', 'z'])
        
        if 'error' in result:
            print(f"✗ Correlation analysis failed: {result['error']}")
            return False
        else:
            print("✓ Correlation analysis executed successfully")
            print(f"  Method: {result.get('method')}")
            print(f"  Total variables: {result.get('summary', {}).get('total_variables', 'Unknown')}")
            print(f"  Strong correlations: {result.get('summary', {}).get('strong_correlations_count', 'Unknown')}")
            
            # Check correlation matrix
            if 'correlation_matrix' in result:
                corr_matrix = pd.DataFrame(result['correlation_matrix'])
                print(f"  Correlation matrix shape: {corr_matrix.shape}")
                print("  Correlation matrix:")
                print(corr_matrix)
                
                # Check for strong correlations
                if 'strong_correlations' in result:
                    strong_corrs = result['strong_correlations']
                    print(f"  Found {len(strong_corrs)} strong correlations:")
                    for corr in strong_corrs:
                        print(f"    {corr['variable1']} - {corr['variable2']}: {corr['correlation']:.3f}")
            
            return True
            
    except Exception as e:
        print(f"✗ Error during correlation execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_correlation_execution()
    sys.exit(0 if success else 1)