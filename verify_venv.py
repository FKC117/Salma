#!/usr/bin/env python3
"""
Virtual Environment Verification Script (T006 - NON-NEGOTIABLE)

This script verifies that the virtual environment is properly activated
and all required packages are installed.
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_virtual_environment():
    """Check if virtual environment is activated."""
    print("🔍 Checking virtual environment...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ ERROR: Virtual environment is not activated!")
        print("\n📋 To activate virtual environment:")
        print("   Windows: .\\venv\\Scripts\\Activate.ps1")
        print("   Linux/Mac: source venv/bin/activate")
        print("\n⚠️  This is NON-NEGOTIABLE for security and dependency isolation.")
        return False
    
    print("✅ Virtual environment is activated")
    print(f"   Python executable: {sys.executable}")
    print(f"   Python version: {sys.version}")
    return True

def check_required_packages():
    """Check if all required packages are installed."""
    print("\n🔍 Checking required packages...")
    
    required_packages = [
        'django',
        'djangorestframework',
        'django_cors_headers',
        'django_redis',
        'psycopg2',
        'pyarrow',
        'pandas',
        'numpy',
        'celery',
        'redis',
        'flower',
        'lifelines',
        'matplotlib',
        'seaborn',
        'openpyxl',
        'langchain',
        'google.generativeai',
        'tiktoken',
        'docx',
        'PIL',
        'django_cleanup',
        'bleach',
        'psutil',
        'cryptography',
        'whitenoise',
        'gunicorn',
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Handle package name variations
            if package == 'django_cors_headers':
                importlib.import_module('corsheaders')
            elif package == 'django_redis':
                importlib.import_module('django_redis')
            elif package == 'psycopg2':
                importlib.import_module('psycopg2')
            elif package == 'google.generativeai':
                importlib.import_module('google.generativeai')
            elif package == 'docx':
                importlib.import_module('docx')
            elif package == 'PIL':
                importlib.import_module('PIL')
            elif package == 'django_cleanup':
                importlib.import_module('django_cleanup')
            else:
                importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("📋 Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All required packages are installed")
    return True

def check_database_connection():
    """Check PostgreSQL database connection."""
    print("\n🔍 Checking PostgreSQL database connection...")
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            database='analytical',
            user='postgres',
            password='Afroafri117!@',
            port='5432'
        )
        conn.close()
        print("✅ PostgreSQL database connection successful")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL database connection failed: {e}")
        print("📋 Make sure PostgreSQL is running and database 'analytical' exists")
        return False

def check_redis_connection():
    """Check Redis connection."""
    print("\n🔍 Checking Redis connection...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("📋 Make sure Redis is running on localhost:6379")
        return False

def main():
    """Main verification function."""
    print("🚀 Virtual Environment Verification Script")
    print("=" * 50)
    
    checks = [
        check_virtual_environment,
        check_required_packages,
        check_database_connection,
        check_redis_connection,
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! Environment is ready.")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
