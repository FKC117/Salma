"""
Simple test script to verify correlation analysis functionality without Django
"""

import pandas as pd
import numpy as np
import sys
import os

# Add the analytics tools path
sys.path.append(os.path.join(os.path.dirname(__file__), 'analytical'))

def correlation_analysis(df: pd.DataFrame, method: str = 'pearson', 
                        columns: list = None):
    """
    Calculate correlation matrix and analysis (simplified version)
    """
    try:
        if columns is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            numeric_cols = [col for col in columns if col in df.columns and df[col].dtype in ['int64', 'float64']]
        
        if len(numeric_cols) < 2:
            return {"error": "At least 2 numeric columns required for correlation analysis"}
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr(method=method)
        
        # Find strong correlations (|r| > 0.7)
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:
                    strong_correlations.append({
                        'variable1': corr_matrix.columns[i],
                        'variable2': corr_matrix.columns[j],
                        'correlation': float(corr_value),
                        'strength': 'strong' if abs(corr_value) > 0.8 else 'moderate'
                    })
        
        return {
            'type': 'correlation_analysis',
            'method': method,
            'correlation_matrix': corr_matrix.to_dict(),
            'strong_correlations': strong_correlations,
            'summary': {
                'total_variables': len(numeric_cols),
                'strong_correlations_count': len(strong_correlations)
            }
        }
        
    except Exception as e:
        return {"error": f"Correlation analysis failed: {str(e)}"}

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
    result = correlation_analysis(data, method='pearson')
    
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