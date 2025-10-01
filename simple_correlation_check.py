#!/usr/bin/env python
"""
Simple correlation test to verify the tool is working
"""

import pandas as pd
import numpy as np
import sys
import os

def test_correlation():
    """Simple test for correlation analysis"""
    # Create sample data
    np.random.seed(42)
    data = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100),
        'z': np.random.randn(100)
    })
    
    # Add correlation between x and y
    data['y'] = data['x'] * 0.7 + np.random.randn(100) * 0.3
    
    print("Sample data created")
    print("Data shape:", data.shape)
    
    # Calculate correlation matrix
    corr_matrix = data[['x', 'y', 'z']].corr()
    
    print("\nCorrelation matrix:")
    print(corr_matrix)
    
    # Check correlation between x and y
    x_y_corr = corr_matrix.loc['x', 'y']
    print(f"\nCorrelation between x and y: {x_y_corr:.3f}")
    
    if abs(x_y_corr) > 0.5:
        print("✓ Strong correlation detected as expected!")
        return True
    else:
        print("✗ Unexpected correlation result")
        return False

if __name__ == "__main__":
    success = test_correlation()
    sys.exit(0 if success else 1)