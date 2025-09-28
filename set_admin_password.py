#!/usr/bin/env python3
"""
Set admin password
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'analytical'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Set admin password
try:
    admin_user = User.objects.get(username='admin')
    admin_user.set_password('admin123')
    admin_user.save()
    print("✅ Admin password set successfully!")
    print("Username: admin")
    print("Password: admin123")
except User.DoesNotExist:
    print("❌ Admin user not found")
except Exception as e:
    print(f"❌ Error: {e}")
