"""
Test script to verify that sandbox executions are being saved to the SandboxExecution model
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_sandbox_execution_saving():
    """Test that sandbox executions are saved to the database"""
    print("=== Testing Sandbox Execution Saving ===")
    
    try:
        from analytics.services.sandbox_executor import SandboxExecutor
        from analytics.models import User, AnalysisSession, SandboxExecution
        from django.contrib.auth import get_user_model
        
        # Get or create a test user
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='test_sandbox_user',
                email='test_sandbox@example.com',
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
                name='Test Session',
                user=user,
                description='Test session for sandbox execution'
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
        
        # Execute a simple test code
        test_code = "print('Hello, World!')"
        print(f"Executing test code: {test_code}")
        
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
            
            if latest_execution.status == 'completed':
                print("✅ SUCCESS: Execution completed and saved correctly!")
                return True
            else:
                print("❌ ISSUE: Execution did not complete successfully")
                return False
        else:
            print("❌ FAILURE: No new sandbox execution was saved to the database")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_sandbox_endpoint():
    """Test the sandbox execution endpoint"""
    print("\n=== Testing Sandbox Execution Endpoint ===")
    
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        import json
        
        # Create test client
        client = Client()
        
        # Get or create user
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='test_endpoint_user',
                email='test_endpoint@example.com',
                password='testpassword'
            )
        
        # Login
        client.login(username='test_endpoint_user', password='testpassword')
        
        # Test successful code execution
        print("Testing successful code execution via endpoint...")
        response = client.post('/api/sandbox/execute/', {
            'code': 'print("Hello from endpoint!")',
            'language': 'python'
        }, content_type='application/json')
        
        print(f"Response status code: {response.status_code}")
        response_data = response.json()
        print(f"Response data: {response_data}")
        
        if response.status_code == 200 and response_data.get('success'):
            print("✅ SUCCESS: Sandbox endpoint executed code successfully!")
            return True
        else:
            print("❌ FAILURE: Sandbox endpoint failed to execute code")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing sandbox execution saving functionality...\n")
    
    success1 = test_sandbox_execution_saving()
    success2 = test_sandbox_endpoint()
    
    print("\n=== Summary ===")
    print(f"Sandbox Executor Test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Sandbox Endpoint Test: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Sandbox executions are being saved correctly.")
    else:
        print("\n💥 Some tests failed. There may be issues with saving sandbox executions.")