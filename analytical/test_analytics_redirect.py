"""
Test script to verify the analytics redirect fix
"""
import requests
from requests.sessions import Session

def test_analytics_redirect():
    # Create a session to maintain cookies
    session = Session()
    
    # Step 1: Access analytics home (should redirect to login for unauthenticated users)
    print("Step 1: Accessing analytics home without authentication...")
    response = session.get('http://127.0.0.1:8000/analytics/', allow_redirects=False)
    print(f"Status code: {response.status_code}")
    print(f"Redirect location: {response.headers.get('location', 'No redirect')}")
    
    # Step 2: Get the login page
    print("\nStep 2: Getting login page...")
    response = session.get('http://127.0.0.1:8000/accounts/login/')
    print(f"Status code: {response.status_code}")
    
    # Step 3: Check if we can access the analytics dashboard directly
    print("\nStep 3: Accessing analytics dashboard directly...")
    response = session.get('http://127.0.0.1:8000/analytics/dashboard/')
    print(f"Status code: {response.status_code}")
    if response.status_code == 302:
        print(f"Redirect location: {response.headers.get('location', 'No redirect')}")
    
    print("\nAnalytics redirect test completed!")

if __name__ == "__main__":
    test_analytics_redirect()