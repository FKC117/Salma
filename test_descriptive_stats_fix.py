#!/usr/bin/env python
"""
Test script to verify the fix for descriptive statistics variable names issue
"""
import sys
import os
import pandas as pd
import numpy as np

# Add the analytical directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytical'))

def test_descriptive_stats_fix():
    """Test that descriptive statistics now shows variable names correctly"""
    print("Testing descriptive statistics fix...")
    
    # Import ToolExecutor after setting up the path
    from analytics.services.tool_executor import ToolExecutor
    
    # Create a sample dataset
    data = {
        'age': np.random.randint(18, 80, 100),
        'income': np.random.normal(50000, 15000, 100),
        'score': np.random.uniform(0, 100, 100)
    }
    df = pd.DataFrame(data)
    
    print(f"Created sample dataset with columns: {list(df.columns)}")
    
    # Create tool executor
    executor = ToolExecutor()
    
    # Execute descriptive statistics
    parameters = {
        'columns': ['age', 'income', 'score'],
        'include_percentiles': True,
        'include_skewness': True
    }
    
    result = executor._execute_descriptive_stats(parameters, df)
    
    # Check the result structure
    print("\nResult structure:")
    print(f"Title: {result.get('title')}")
    print(f"Description: {result.get('description')}")
    
    table_data = result.get('table_data', {})
    print(f"\nTable data columns: {table_data.get('columns', [])}")
    print(f"Number of rows: {len(table_data.get('rows', []))}")
    
    # Verify that variable names are included
    columns = table_data.get('columns', [])
    rows = table_data.get('rows', [])
    
    if columns and rows:
        print(f"\nFirst column header: {columns[0]}")
        print(f"First row first element: {rows[0][0] if rows and len(rows[0]) > 0 else 'N/A'}")
        
        # Check that all variable names are present in the first column of rows
        variable_names = [row[0] for row in rows if row]
        expected_names = ['age', 'income', 'score']
        
        print(f"\nVariable names in result: {variable_names}")
        print(f"Expected variable names: {expected_names}")
        
        if set(variable_names) == set(expected_names):
            print("✅ SUCCESS: All variable names are correctly displayed!")
            return True
        else:
            print("❌ FAILURE: Variable names are missing or incorrect!")
            return False
    else:
        print("❌ FAILURE: No table data found!")
        return False

if __name__ == "__main__":
    success = test_descriptive_stats_fix()
    sys.exit(0 if success else 1)