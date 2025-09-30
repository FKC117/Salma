"""
Inspect existing sandbox executions to verify user and session data
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def inspect_sandbox_executions():
    """Inspect existing sandbox executions to verify user and session data"""
    print("=== Inspecting Sandbox Executions ===")
    
    try:
        from analytics.models import SandboxExecution
        
        # Get all executions with user and session info
        executions = SandboxExecution.objects.select_related('user', 'session').order_by('-created_at')[:10]
        
        print(f"Found {SandboxExecution.objects.count()} total sandbox executions")
        print("\nLatest 10 executions:")
        
        for i, execution in enumerate(executions, 1):
            print(f"\n--- Execution {i} ---")
            print(f"ID: {execution.id}")
            print(f"Status: {execution.status}")
            print(f"Language: {execution.language}")
            print(f"Created: {execution.created_at}")
            
            # User information
            if execution.user:
                print(f"User ID: {execution.user.id}")
                print(f"Username: {execution.user.username}")
                print(f"Email: {execution.user.email}")
            else:
                print("User: None")
            
            # Session information
            if execution.session:
                print(f"Session ID: {execution.session.id}")
                print(f"Session Name: {execution.session.name}")
                print(f"Session User ID: {execution.session.user.id if execution.session.user else 'None'}")
            else:
                print("Session: None")
            
            # Code snippet
            code_snippet = execution.code[:100] if execution.code else "None"
            print(f"Code snippet: {code_snippet}...")
            
            # Output snippet
            output_snippet = str(execution.output)[:100] if execution.output else "None"
            print(f"Output snippet: {output_snippet}...")
            
            # Resource usage
            print(f"Execution time: {execution.execution_time_ms} ms")
            print(f"Memory used: {execution.memory_used_mb} MB")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    inspect_sandbox_executions()