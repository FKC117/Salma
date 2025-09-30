"""
Debug script to verify sandbox execution parameters
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def debug_sandbox_execution():
    """Debug sandbox execution with detailed parameter logging"""
    print("=== Debugging Sandbox Execution Parameters ===")
    
    try:
        from analytics.services.sandbox_executor import SandboxExecutor
        from analytics.models import User, AnalysisSession, SandboxExecution
        from django.contrib.auth import get_user_model
        
        # Get or create a test user
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='debug_sandbox_user',
                email='debug_sandbox@example.com',
                password='testpassword'
            )
            print("✓ Created test user")
        else:
            print(f"✓ Using existing user - ID: {user.id}, Username: {user.username}")
        
        # Get current session
        session = None
        try:
            # Try to get the latest session for the user
            session = AnalysisSession.objects.filter(user=user).order_by('-created_at').first()
            if session:
                print(f"✓ Found session - ID: {session.id}, Name: {session.name}")
            else:
                print("⚠️ No session found for user")
        except AnalysisSession.DoesNotExist:
            print("⚠️ Session does not exist")
            pass
        
        # Count executions before test
        initial_count = SandboxExecution.objects.count()
        print(f"Initial execution count: {initial_count}")
        
        # Initialize sandbox executor
        sandbox_executor = SandboxExecutor()
        print("✓ SandboxExecutor initialized")
        
        # Execute a simple test code
        test_code = """
print("Debug test execution")
print("User ID verification test")
x = 5 + 3
print(f"Calculation result: {x}")
"""
        print(f"Executing test code with {len(test_code)} characters")
        
        # Execute code with debug parameters
        result = sandbox_executor.execute_code(
            code=test_code,
            user=user,
            language='python',
            session=session
        )
        
        print(f"Execution result:")
        print(f"  - Execution ID: {result.id}")
        print(f"  - Status: {result.status}")
        print(f"  - User ID: {result.user.id}")
        print(f"  - User Username: {result.user.username}")
        if result.session:
            print(f"  - Session ID: {result.session.id}")
            print(f"  - Session Name: {result.session.name}")
        else:
            print(f"  - Session: None")
        print(f"  - Language: {result.language}")
        print(f"  - Output: {result.output}")
        print(f"  - Execution time: {result.execution_time_ms} ms")
        
        # Count executions after test
        final_count = SandboxExecution.objects.count()
        print(f"Final execution count: {final_count}")
        
        # Verify the execution was saved correctly
        if final_count > initial_count:
            print("✅ SUCCESS: New sandbox execution was saved to the database!")
            
            # Get the latest execution from database
            latest_execution = SandboxExecution.objects.latest('created_at')
            print(f"Database record verification:")
            print(f"  - ID: {latest_execution.id}")
            print(f"  - Status: {latest_execution.status}")
            print(f"  - User ID: {latest_execution.user.id}")
            print(f"  - User Username: {latest_execution.user.username}")
            if latest_execution.session:
                print(f"  - Session ID: {latest_execution.session.id}")
                print(f"  - Session Name: {latest_execution.session.name}")
            else:
                print(f"  - Session: None")
            print(f"  - Language: {latest_execution.language}")
            print(f"  - Code snippet: {latest_execution.code[:50]}...")
            print(f"  - Output snippet: {str(latest_execution.output)[:50] if latest_execution.output else 'None'}...")
            
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
    debug_sandbox_execution()