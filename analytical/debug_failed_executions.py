"""
Debug failed sandbox executions to understand why they're failing
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def debug_failed_executions():
    """Debug failed sandbox executions to understand why they're failing"""
    print("=== Debugging Failed Sandbox Executions ===")
    
    try:
        from analytics.models import SandboxExecution
        
        # Get the latest failed execution
        latest_failed = SandboxExecution.objects.filter(status='failed').order_by('-created_at').first()
        
        if not latest_failed:
            print("No failed executions found")
            return True
            
        print(f"Latest failed execution (ID: {latest_failed.id}):")
        print(f"Status: {latest_failed.status}")
        print(f"Language: {latest_failed.language}")
        print(f"Created: {latest_failed.created_at}")
        print(f"Started: {latest_failed.started_at}")
        print(f"Finished: {latest_failed.finished_at}")
        
        # User information
        if latest_failed.user:
            print(f"User ID: {latest_failed.user.id}")
            print(f"Username: {latest_failed.user.username}")
        
        # Session information
        if latest_failed.session:
            print(f"Session ID: {latest_failed.session.id}")
            print(f"Session Name: {latest_failed.session.name}")
        
        # Code
        print(f"\nCode:")
        print("---")
        print(latest_failed.code)
        print("---")
        
        # Error message
        print(f"\nError message:")
        print(f"{latest_failed.error_message}")
        
        # Security information
        print(f"\nSecurity scan passed: {latest_failed.security_scan_passed}")
        print(f"Security warnings: {latest_failed.security_warnings}")
        
        # Resource usage
        print(f"\nResource usage:")
        print(f"Execution time: {latest_failed.execution_time_ms} ms")
        print(f"Memory used: {latest_failed.memory_used_mb} MB")
        print(f"CPU usage: {latest_failed.cpu_usage_percent}%")
        
        # Output
        print(f"\nOutput:")
        print(f"{latest_failed.output}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_execution():
    """Test a simple execution to see if it works"""
    print("\n=== Testing Simple Execution ===")
    
    try:
        from analytics.services.sandbox_executor import SandboxExecutor
        from analytics.models import User, AnalysisSession
        from django.contrib.auth import get_user_model
        
        # Get user
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='test_debug_user',
                email='test_debug@example.com',
                password='testpassword'
            )
        
        # Get session
        session = AnalysisSession.objects.first()
        
        # Initialize sandbox executor
        sandbox_executor = SandboxExecutor()
        
        # Execute simple code
        test_code = "print('Hello from debug test')"
        
        print(f"Executing: {test_code}")
        
        result = sandbox_executor.execute_code(
            code=test_code,
            user=user,
            language='python',
            session=session
        )
        
        print(f"Execution result:")
        print(f"  Status: {result.status}")
        print(f"  Output: {result.output}")
        print(f"  Error: {result.error_message}")
        print(f"  Execution time: {result.execution_time_ms} ms")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR in simple execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    debug_failed_executions()
    test_simple_execution()