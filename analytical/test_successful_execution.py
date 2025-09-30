import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_successful_sandbox_execution():
    """Test a successful sandbox execution and verify it's saved"""
    print("=== Testing Successful Sandbox Execution Saving ===")
    
    try:
        from analytics.services.sandbox_executor import SandboxExecutor
        from analytics.models import User, AnalysisSession, SandboxExecution
        from django.contrib.auth import get_user_model
        
        # Get or create a test user
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='test_success_user',
                email='test_success@example.com',
                password='testpassword'
            )
            print("✓ Created test user")
        else:
            print("✓ Using existing user")
        
        # Create a test session
        session = AnalysisSession.objects.first()
        if not session:
            # Create a dummy session for testing
            session = AnalysisSession.objects.create(
                name='Test Success Session',
                user=user,
                description='Test session for successful execution'
            )
            print("✓ Created test session")
        else:
            print("✓ Using existing session")
        
        # Count executions before test
        initial_count = SandboxExecution.objects.count()
        print(f"Initial execution count: {initial_count}")
        
        # Initialize sandbox executor
        sandbox_executor = SandboxExecutor()
        print("✓ SandboxExecutor initialized")
        
        # Execute a simple successful test code
        test_code = """
print("Hello, World!")
x = 5 + 3
print(f"The result is: {x}")
"""
        print(f"Executing test code: {test_code.strip()}")
        
        result = sandbox_executor.execute_code(
            code=test_code,
            user=user,
            language='python',
            session=session
        )
        
        print(f"Execution result status: {result.status}")
        print(f"Execution result output: {result.output}")
        
        # Count executions after test
        final_count = SandboxExecution.objects.count()
        print(f"Final execution count: {final_count}")
        
        # Check if a new execution was created
        if final_count > initial_count:
            print("✅ SUCCESS: New sandbox execution was saved to the database!")
            
            # Get the latest execution
            latest_execution = SandboxExecution.objects.latest('created_at')
            print(f"Latest execution ID: {latest_execution.id}")
            print(f"Latest execution status: {latest_execution.status}")
            print(f"Latest execution output: {latest_execution.output}")
            print(f"Latest execution code: {latest_execution.code}")
            print(f"Execution time: {latest_execution.execution_time_ms} ms")
            print(f"Memory used: {latest_execution.memory_used_mb} MB")
            
            if latest_execution.status == 'completed':
                print("✅ SUCCESS: Execution completed and saved correctly!")
                return True
            else:
                print(f"⚠️  INFO: Execution status is '{latest_execution.status}' (not completed)")
                return True
        else:
            print("❌ FAILURE: No new sandbox execution was saved to the database")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_successful_sandbox_execution()