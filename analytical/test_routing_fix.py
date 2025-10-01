"""
Test script to verify the routing fix
"""
import requests

def test_routing_fix():
    print("Testing prescription app routing...")
    response = requests.get('http://127.0.0.1:8000/')
    print(f"Prescription app root status code: {response.status_code}")
    
    print("\nTesting analytics app routing...")
    response = requests.get('http://127.0.0.1:8000/analytics/')
    print(f"Analytics app root status code: {response.status_code}")
    print(f"Analytics app redirect location: {response.headers.get('location', 'No redirect')}")
    
    print("\nTesting analytics dashboard...")
    response = requests.get('http://127.0.0.1:8000/analytics/dashboard/')
    print(f"Analytics dashboard status code: {response.status_code}")
    
    print("\nTesting prescription URLs...")
    # Test that the prescription dashboard URL no longer exists
    response = requests.get('http://127.0.0.1:8000/dashboard/')
    print(f"Prescription dashboard (should be 404): {response.status_code}")
    
    print("\nRouting fix test completed!")

if __name__ == "__main__":
    test_routing_fix()