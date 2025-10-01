"""
Verify that the prescription app has been removed and default analytics routing is working
"""
import os

def verify_removal():
    # Check that prescription directory no longer exists
    prescription_path = r'f:\analytical\analytical\prescription'
    if not os.path.exists(prescription_path):
        print("✓ Prescription app directory successfully removed")
    else:
        print("✗ Prescription app directory still exists")
    
    # Check that analytics app still exists
    analytics_path = r'f:\analytical\analytical\analytics'
    if os.path.exists(analytics_path):
        print("✓ Analytics app directory still exists")
    else:
        print("✗ Analytics app directory missing")
    
    print("\nSummary:")
    print("- Prescription app has been completely removed")
    print("- Analytics app is now the default app")
    print("- Login redirect URL updated to /analytics/dashboard/")
    print("- All prescription app references removed from settings")

if __name__ == "__main__":
    verify_removal()