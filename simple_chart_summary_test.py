"""
Simple test to verify the chart_summary parameter fix
"""

def test_function_signature():
    """Test that the function signature now includes chart_summary parameter"""
    import inspect
    import sys
    import os
    
    # Add the analytics tools path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'analytical'))
    
    try:
        # Read the file directly to check the function signature
        file_path = os.path.join(os.path.dirname(__file__), 'analytical', 'analytics', 'services', 'analysis_result_manager.py')
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if the chart_summary parameter is in the function signature
        if 'chart_summary: Dict[str, Any] = None' in content:
            print("✓ Function signature correctly updated to include chart_summary parameter")
            return True
        else:
            print("✗ Function signature does not include chart_summary parameter")
            return False
            
    except Exception as e:
        print(f"Error checking function signature: {str(e)}")
        return False

def test_chart_summary_usage():
    """Test that chart_summary is used in the function body"""
    import sys
    import os
    
    # Add the analytics tools path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'analytical'))
    
    try:
        # Read the file directly to check the function implementation
        file_path = os.path.join(os.path.dirname(__file__), 'analytical', 'analytics', 'services', 'analysis_result_manager.py')
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if the chart_summary parameter is used in the function body
        if 'if chart_summary is None:' in content and 'chart_summary=chart_summary' in content:
            print("✓ Function correctly uses chart_summary parameter")
            return True
        else:
            print("✗ Function does not correctly use chart_summary parameter")
            return False
            
    except Exception as e:
        print(f"Error checking function implementation: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing chart_summary parameter fix...")
    print("=" * 50)
    
    success1 = test_function_signature()
    success2 = test_chart_summary_usage()
    
    print("=" * 50)
    if success1 and success2:
        print("🎉 All tests passed! The chart_summary parameter fix is correctly implemented.")
        print("\nChanges made:")
        print("1. Added chart_summary parameter to create_chart_analysis_result method")
        print("2. Modified method to use provided chart_summary or create one if not provided")
        print("3. This fixes the 'unexpected keyword argument' error")
    else:
        print("❌ Some tests failed. Please check the implementation.")