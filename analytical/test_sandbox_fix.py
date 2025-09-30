"""
Test the sandbox fix
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_sandbox_fix():
    """Test the sandbox fix"""
    print("=== Testing Sandbox Fix ===")
    
    try:
        from analytics.services.sandbox_executor import SandboxExecutor
        from analytics.models import User, AnalysisSession
        from django.contrib.auth import get_user_model
        
        # Get user
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='test_fix_user',
                email='test_fix@example.com',
                password='testpassword'
            )
        
        # Get session
        session = AnalysisSession.objects.first()
        
        # Initialize sandbox executor
        sandbox_executor = SandboxExecutor()
        
        # Execute simple code
        test_code = "print('Hello from fixed sandbox!')"
        
        print(f"Executing: {test_code}")
        
        result = sandbox_executor.execute_code(
            code=test_code,
            user=user,
            language='python',
            session=session
        )
        
        print(f"Execution result:")
        print(f"  Status: {result.status}")
        print(f"  Output: {repr(result.output)}")
        print(f"  Error: {result.error_message}")
        print(f"  Execution time: {result.execution_time_ms} ms")
        print(f"  Memory used: {result.memory_used_mb} MB")
        
        if result.status == 'completed':
            print("✅ SUCCESS: Sandbox execution completed!")
            return True
        else:
            print("❌ FAILURE: Sandbox execution failed")
            return False
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_sandbox_fix()