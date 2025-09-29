#!/usr/bin/env python
"""
Test script to check for remaining errors
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from analytics.models import User, AnalysisSuggestion, SandboxExecution, ChatMessage
from analytics.services.analysis_suggestion_service import AnalysisSuggestionService

def check_system_errors():
    """Check for various system errors"""
    print("[CHECK] Analyzing system for errors...")
    
    # Check suggestion execution
    user = User.objects.first()
    service = AnalysisSuggestionService()
    suggestion = AnalysisSuggestion.objects.filter(is_executed=False).first()
    
    if suggestion:
        print(f"[INFO] Found unexecuted suggestion: {suggestion.analysis_tool.display_name}")
        print("[TEST] Testing suggestion execution...")
        result = service.execute_suggestion(suggestion.id, user)
        print(f"[RESULT] Execution success: {result['success']}")
        if not result['success']:
            print(f"[ERROR] Execution failed: {result['error']}")
    else:
        print("[INFO] No unexecuted suggestions found")
    
    # Check sandbox executions
    print(f"\n[SANDBOX] Total executions: {SandboxExecution.objects.count()}")
    print(f"[SANDBOX] Completed: {SandboxExecution.objects.filter(status='completed').count()}")
    print(f"[SANDBOX] Failed: {SandboxExecution.objects.filter(status='failed').count()}")
    
    # Check recent failures
    recent_failures = SandboxExecution.objects.filter(status='failed').order_by('-created_at')[:3]
    for failure in recent_failures:
        print(f"[FAILURE] {failure.created_at}: {failure.error_message}")
    
    # Check chat messages
    print(f"\n[CHAT] Total messages: {ChatMessage.objects.count()}")
    recent_messages = ChatMessage.objects.order_by('-created_at')[:3]
    for msg in recent_messages:
        print(f"[MESSAGE] {msg.created_at}: {msg.content[:50]}...")

if __name__ == "__main__":
    check_system_errors()
