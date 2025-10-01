"""
Test script to verify navigation to analytics dashboard
"""
import requests

def test_analytics_navigation():
    # Test the analytics dashboard URL directly
    response = requests.get('http://127.0.0.1:8000/analytics/dashboard/')
    print(f"Analytics dashboard URL status code: {response.status_code}")
    
    # Test the analytics home URL (should redirect to dashboard if authenticated)
    response = requests.get('http://127.0.0.1:8000/analytics/')
    print(f"Analytics home URL status code: {response.status_code}")
    print(f"Analytics home URL redirect location: {response.headers.get('Location', 'No redirect')}")
    
    print("Analytics navigation test completed!")

if __name__ == "__main__":
    test_analytics_navigation()