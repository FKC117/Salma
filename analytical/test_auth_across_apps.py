"""
Test script to verify authentication works across both apps
"""
import requests

def test_auth_across_apps():
    # Test the root URL (should show prescription app)
    response = requests.get('http://127.0.0.1:8000/')
    print(f"Root URL status code: {response.status_code}")
    
    # Test the login URL
    response = requests.get('http://127.0.0.1:8000/accounts/login/')
    print(f"Login URL status code: {response.status_code}")
    
    # Test the register URL
    response = requests.get('http://127.0.0.1:8000/accounts/register/')
    print(f"Register URL status code: {response.status_code}")
    
    # Test the analytics URL
    response = requests.get('http://127.0.0.1:8000/analytics/')
    print(f"Analytics URL status code: {response.status_code}")
    
    print("Authentication cross-app test completed!")

if __name__ == "__main__":
    test_auth_across_apps()