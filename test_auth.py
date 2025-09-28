import requests

# Test the registration page
response = requests.get('http://127.0.0.1:8000/register/')
print(f"Registration page status code: {response.status_code}")
print(f"Registration page content length: {len(response.text)}")

# Test the login page
response = requests.get('http://127.0.0.1:8000/accounts/login/')
print(f"Login page status code: {response.status_code}")
print(f"Login page content length: {len(response.text)}")