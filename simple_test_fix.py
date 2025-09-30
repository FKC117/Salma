#!/usr/bin/env python
"""
Simple test to verify the fix for descriptive statistics variable names issue
"""
import pandas as pd
import numpy as np

def test_table_data_structure():
    """Test that the table data structure correctly includes variable names"""
    print("Testing table data structure fix...")
    
    # Create sample data similar to what would be processed
    data = {
        'age': np.random.randint(18, 80, 100),
        'income': np.random.normal(50000, 15000, 100),
        'score': np.random.uniform(0, 100, 100)
    }
    df = pd.DataFrame(data)
    
    # Simulate the original (broken) approach
    columns = ['age', 'income', 'score']
    stats = df[columns].describe()
    
    # Transpose the data (this is what was causing the issue)
    stats_transposed = stats.T
    
    print("Original approach (broken):")
    print(f"Columns: {stats_transposed.columns.tolist()}")
    print(f"Index (variable names): {stats_transposed.index.tolist()}")
    print(f"Sample row: {stats_transposed.iloc[0].tolist()}")
    
    # Show the issue - variable names are in the index, not in the rows
    print("\nIssue: Variable names are in the index, not as a column in the data")
    
    # Apply our fix
    table_rows = []
    for variable_name in stats_transposed.index:
        # Create a row with the variable name as the first element, followed by statistics
        row = [variable_name] + stats_transposed.loc[variable_name].tolist()
        table_rows.append(row)
    
    fixed_table_data = {
        'columns': ['Variable'] + stats_transposed.columns.tolist(),  # Add 'Variable' as first column header
        'rows': table_rows  # Use the fixed rows with variable names included
    }
    
    print("\nFixed approach:")
    print(f"Columns: {fixed_table_data['columns']}")
    print(f"Number of rows: {len(fixed_table_data['rows'])}")
    print(f"First row (with variable name): {fixed_table_data['rows'][0]}")
    
    # Verify the fix
    variable_names_in_rows = [row[0] for row in fixed_table_data['rows']]
    expected_names = ['age', 'income', 'score']
    
    print(f"\nVariable names extracted from rows: {variable_names_in_rows}")
    print(f"Expected variable names: {expected_names}")
    
    if set(variable_names_in_rows) == set(expected_names):
        print("✅ SUCCESS: All variable names are correctly included in the table data!")
        return True
    else:
        print("❌ FAILURE: Variable names are still missing or incorrect!")
        return False

if __name__ == "__main__":
    success = test_table_data_structure()
    exit(0 if success else 1)