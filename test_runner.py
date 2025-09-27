#!/usr/bin/env python
"""
Simple test runner to verify tests work
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run a simple test
    failures = test_runner.run_tests(['tests.integration.test_simple_upload'])
    
    if failures:
        print(f"Tests failed: {failures}")
        sys.exit(1)
    else:
        print("Tests passed!")
        sys.exit(0)
