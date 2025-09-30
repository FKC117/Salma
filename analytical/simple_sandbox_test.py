import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def check_sandbox_executions():
    """Check if sandbox executions are being saved"""
    print("=== Checking Sandbox Execution Saving ===")
    
    try:
        from analytics.models import SandboxExecution
        
        # Count total executions
        total_executions = SandboxExecution.objects.count()
        print(f"Total sandbox executions in database: {total_executions}")
        
        # Show latest executions
        if total_executions > 0:
            print("\nLatest 3 executions:")
            latest_executions = SandboxExecution.objects.order_by('-created_at')[:3]
            for i, execution in enumerate(latest_executions, 1):
                print(f"  {i}. ID: {execution.id}")
                print(f"     Status: {execution.status}")
                print(f"     Language: {execution.language}")
                print(f"     Created: {execution.created_at}")
                print(f"     Code snippet: {execution.code[:50]}...")
                print(f"     Output snippet: {str(execution.output)[:50] if execution.output else 'None'}...")
                print()
            
            print("✅ SUCCESS: Sandbox executions are being saved to the database!")
            return True
        else:
            print("⚠️  INFO: No sandbox executions found in database")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    check_sandbox_executions()