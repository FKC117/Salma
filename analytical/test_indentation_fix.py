#!/usr/bin/env python3
"""
Test script to reproduce and fix indentation errors in sandbox execution
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from analytics.models import User, Dataset, AnalysisSession
from analytics.services.sandbox_executor import SandboxExecutor
from analytics.services.code_extraction_service import CodeExtractionService

def test_indentation_fix():
    """Test the indentation fixing functionality"""
    print("=== TESTING INDENTATION FIX ===")
    
    # Test code with indentation issues (similar to what LLM might generate)
    problematic_code = '''
import pandas as pd
import matplotlib.pyplot as plt

# Load data
data = {
    'x': [1, 2, 3, 4, 5],
    'y': [2, 4, 6, 8, 10]
}
df = pd.DataFrame(data)

# Create plot
plt.figure(figsize=(10, 6))
plt.plot(df['x'], df['y'])
plt.title('Test Plot')
plt.show()
'''
    
    print("Original problematic code:")
    print(problematic_code)
    print("\n" + "="*50 + "\n")
    
    # Test the sandbox executor's syntax correction
    executor = SandboxExecutor()
    
    print("Testing syntax correction...")
    corrected_code = executor._fix_common_syntax_errors(problematic_code)
    
    print("Corrected code:")
    print(corrected_code)
    print("\n" + "="*50 + "\n")
    
    # Test if the corrected code can be parsed
    import ast
    try:
        ast.parse(corrected_code)
        print("✅ Corrected code parses successfully!")
    except SyntaxError as e:
        print(f"❌ Corrected code still has syntax error: {e}")
        return False
    
    # Test execution with a user and session
    try:
        user = User.objects.first()
        if not user:
            print("❌ No user found in database")
            return False
        
        dataset = Dataset.objects.first()
        if not dataset:
            print("❌ No dataset found in database")
            return False
        
        session = AnalysisSession.objects.create(
            user=user,
            primary_dataset=dataset,
            name="Indentation Test Session"
        )
        
        print(f"✅ Using User: {user.username} (ID: {user.id})")
        print(f"✅ Using Dataset: {dataset.name} (ID: {dataset.id})")
        print(f"✅ Created Session: {session.id}")
        
        # Execute the corrected code
        print("\n=== EXECUTING CORRECTED CODE ===")
        result = executor.execute_code(
            code=corrected_code,
            user_id=user.id,
            session_id=session.id,
            language='python',
            timeout=30
        )
        
        print(f"Execution result: {'SUCCESS' if result.get('success') else 'FAILED'}")
        if result.get('success'):
            print(f"✅ Code executed successfully!")
            print(f"Output length: {len(result.get('output', ''))}")
        else:
            print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_indentation_fix()
        if success:
            print("\n🎉 INDENTATION FIX TEST SUCCESSFUL!")
        else:
            print("\n❌ INDENTATION FIX TEST FAILED!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
