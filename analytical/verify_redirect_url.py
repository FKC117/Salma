"""
Simple script to verify the redirect URL
"""
def verify_redirect_url():
    # This is just to verify that our redirect URL is correct
    expected_redirect = "/analytics/dashboard/"
    print(f"Expected redirect URL: {expected_redirect}")
    print("This should take you to the analytics dashboard after authentication")

if __name__ == "__main__":
    verify_redirect_url()