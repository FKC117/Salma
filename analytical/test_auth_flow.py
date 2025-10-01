"""
Test script to verify the authentication flow to dashboard
"""
import requests
from requests.sessions import Session

def test_auth_flow():
    # Create a session to maintain cookies
    session = Session()
    
    # Step 1: Try to access dashboard (should redirect to login)
    print("Step 1: Accessing dashboard without authentication...")
    response = session.get('http://127.0.0.1:8000/analytics/dashboard/', allow_redirects=False)
    print(f"Status code: {response.status_code}")
    print(f"Redirect location: {response.headers.get('location', 'No redirect')}")
    
    # Step 2: Get the login page
    print("\nStep 2: Getting login page...")
    response = session.get('http://127.0.0.1:8000/accounts/login/')
    print(f"Status code: {response.status_code}")
    
    # Extract CSRF token from the login page
    import re
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"CSRF token extracted: {csrf_token[:20]}...")
    else:
        print("Could not extract CSRF token")
        return
    
    # Step 3: Login with demo credentials
    print("\nStep 3: Logging in with demo credentials...")
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'username': 'demo',
        'password': 'demo123'
    }
    
    response = session.post('http://127.0.0.1:8000/accounts/login/', data=login_data, allow_redirects=False)
    print(f"Login status code: {response.status_code}")
    print(f"Redirect location after login: {response.headers.get('location', 'No redirect')}")
    
    # Step 4: Access dashboard after login
    print("\nStep 4: Accessing dashboard after authentication...")
    response = session.get('http://127.0.0.1:8000/analytics/dashboard/')
    print(f"Dashboard status code: {response.status_code}")
    
    # Check if we got the actual dashboard (not login page)
    if "Dashboard - Data Analysis System" in response.text:
        print("SUCCESS: Got the analytics dashboard!")
    elif "Login - Data Analysis System" in response.text:
        print("FAILED: Still getting login page")
    else:
        print("UNKNOWN: Got some other page")
    
    print("\nAuthentication flow test completed!")

if __name__ == "__main__":
    test_auth_flow()