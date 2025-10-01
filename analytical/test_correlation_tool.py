"""
Test script to verify correlation analysis tool functionality
"""

import pandas as pd
import numpy as np
from analytics.tools.statistical_tools import StatisticalTools

def test_correlation_analysis():
    """Test the correlation analysis tool"""
    # Create sample data
    np.random.seed(42)
    data = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100),
        'z': np.random.randn(100)
    })
    
    # Add some correlation
    data['y'] = data['x'] * 0.7 + np.random.randn(100) * 0.3
    
    print("Sample data:")
    print(data.head())
    print("\nData shape:", data.shape)
    
    # Test correlation analysis
    result = StatisticalTools.correlation_analysis(data, method='pearson')
    
    print("\nCorrelation analysis result:")
    print("Type:", result.get('type'))
    print("Method:", result.get('method'))
    print("Summary:", result.get('summary'))
    
    if 'correlation_matrix' in result:
        print("\nCorrelation matrix:")
        corr_matrix = pd.DataFrame(result['correlation_matrix'])
        print(corr_matrix)
    
    if 'strong_correlations' in result:
        print("\nStrong correlations:")
        for corr in result['strong_correlations']:
            print(f"  {corr['variable1']} - {corr['variable2']}: {corr['correlation']:.3f}")
    
    return result

if __name__ == "__main__":
    test_correlation_analysis()