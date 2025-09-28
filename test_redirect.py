import requests

# Test the root URL redirect
response = requests.get('http://127.0.0.1:8000/', allow_redirects=False)
print(f"Root URL status code: {response.status_code}")
print(f"Root URL redirect location: {response.headers.get('Location', 'None')}")

# Test the login page
response = requests.get('http://127.0.0.1:8000/accounts/login/')
print(f"Login page status code: {response.status_code}")
print(f"Login page title: {response.text[:100]}")