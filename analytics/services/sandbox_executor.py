"""
Sandbox Executor for Secure Code Execution

This service provides a secure sandbox environment for executing LLM-generated code
with comprehensive security measures, resource limits, and error handling.
"""

import os
import sys
import subprocess
import tempfile
import logging
import time
import psutil
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import ast
import re
import signal
import threading
from contextlib import contextmanager

from analytics.models import SandboxExecution, User, AnalysisSession, AuditTrail
from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)


class SandboxExecutor:
    """
    Service for secure code execution in isolated environment
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        
        # Security settings
        self.allowed_imports = {
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'scipy', 'sklearn',
            'math', 'statistics', 'json', 'csv', 'datetime', 'time',
            'collections', 'itertools', 'functools', 'operator'
        }
        
        self.forbidden_imports = {
            'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
            'pickle', 'shelve', 'dbm', 'sqlite3', 'psycopg2', 'pymongo',
            'boto3', 'azure', 'google', 'openai', 'anthropic'
        }
        
        self.forbidden_functions = {
            'exec', 'eval', 'compile', 'open', 'file', 'input', 'raw_input',
            'exit', 'quit', 'reload', 'dir', 'vars', 'globals', 'locals',
            'getattr', 'setattr', 'delattr', 'hasattr', 'callable'
        }
        
        # Resource limits
        self.max_execution_time = 30  # seconds
        self.max_memory_mb = 512  # MB
        self.max_cpu_percent = 80  # %
        self.max_output_size = 1024 * 1024  # 1MB
        
        # Sandbox directory
        self.sandbox_dir = Path(settings.MEDIA_ROOT) / 'sandbox'
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_code(self, code: str, language: str = 'python', user: User,
                    session: Optional[AnalysisSession] = None, 
                    timeout: Optional[int] = None) -> SandboxExecution:
        """
        Execute code in secure sandbox environment
        
        Args:
            code: Code to execute
            language: Programming language (currently only Python)
            user: User executing code
            session: Analysis session
            timeout: Custom timeout in seconds
            
        Returns:
            SandboxExecution object with results
        """
        execution_id = f"exec_{int(timezone.now().timestamp())}"
        start_time = time.time()
        
        try:
            # Security validation
            self._validate_code_security(code)
            
            # Create sandbox execution record
            with transaction.atomic():
                execution = SandboxExecution.objects.create(
                    code=code,
                    language=language,
                    status='running',
                    user=user,
                    session=session,
                    started_at=timezone.now()
                )
            
            # Execute in sandbox
            result = self._execute_in_sandbox(code, language, timeout or self.max_execution_time)
            
            # Update execution record
            execution.status = 'completed' if result['success'] else 'failed'
            execution.output = result['output']
            execution.error_message = result.get('error_message')
            execution.execution_time_ms = int((time.time() - start_time) * 1000)
            execution.memory_used_mb = result.get('memory_used_mb', 0)
            execution.cpu_usage_percent = result.get('cpu_usage_percent', 0)
            execution.security_scan_passed = result.get('security_scan_passed', True)
            execution.security_warnings = result.get('security_warnings', [])
            execution.finished_at = timezone.now()
            execution.save()
            
            # Log audit trail
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='sandbox_execution',
                resource_type='sandbox_execution',
                resource_id=execution.id,
                resource_name=f"Code Execution: {language}",
                action_description=f"Executed {language} code in sandbox",
                success=result['success'],
                execution_time_ms=execution.execution_time_ms
            )
            
            logger.info(f"Code execution completed for user {user.id}: {execution.status}")
            return execution
            
        except Exception as e:
            logger.error(f"Sandbox execution failed: {str(e)}", exc_info=True)
            
            # Update execution record with error
            try:
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.execution_time_ms = int((time.time() - start_time) * 1000)
                execution.finished_at = timezone.now()
                execution.save()
            except:
                pass
            
            raise ValueError(f"Sandbox execution failed: {str(e)}")
    
    def _validate_code_security(self, code: str) -> None:
        """Validate code for security threats"""
        try:
            # Parse code to AST
            tree = ast.parse(code)
            
            # Check for forbidden imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.forbidden_imports:
                            raise SecurityError(f"Forbidden import: {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module in self.forbidden_imports:
                        raise SecurityError(f"Forbidden import: {node.module}")
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in self.forbidden_functions:
                        raise SecurityError(f"Forbidden function call: {node.func.id}")
            
            # Check for dangerous patterns
            dangerous_patterns = [
                r'__import__\s*\(',
                r'getattr\s*\(',
                r'setattr\s*\(',
                r'exec\s*\(',
                r'eval\s*\(',
                r'compile\s*\(',
                r'open\s*\(',
                r'file\s*\(',
                r'input\s*\(',
                r'raw_input\s*\(',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    raise SecurityError(f"Dangerous pattern detected: {pattern}")
            
        except SyntaxError as e:
            raise SecurityError(f"Invalid syntax: {str(e)}")
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Security validation failed: {str(e)}")
    
    def _execute_in_sandbox(self, code: str, language: str, timeout: int) -> Dict[str, Any]:
        """Execute code in isolated sandbox environment"""
        try:
            if language != 'python':
                raise ValueError(f"Unsupported language: {language}")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with resource limits
                result = self._run_with_limits(temp_file, timeout)
                return result
            finally:
                # Clean up
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error_message': str(e),
                'memory_used_mb': 0,
                'cpu_usage_percent': 0,
                'security_scan_passed': False,
                'security_warnings': [str(e)]
            }
    
    def _run_with_limits(self, script_path: str, timeout: int) -> Dict[str, Any]:
        """Run script with resource limits"""
        start_time = time.time()
        process = None
        
        try:
            # Start process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.sandbox_dir)
            )
            
            # Monitor resources
            max_memory = self.max_memory_mb * 1024 * 1024  # Convert to bytes
            max_output = self.max_output_size
            
            output_lines = []
            error_lines = []
            memory_peak = 0
            
            # Read output with timeout
            while process.poll() is None:
                # Check timeout
                if time.time() - start_time > timeout:
                    process.terminate()
                    return {
                        'success': False,
                        'output': '',
                        'error_message': f'Execution timeout after {timeout} seconds',
                        'memory_used_mb': memory_peak / (1024 * 1024),
                        'cpu_usage_percent': 0,
                        'security_scan_passed': True,
                        'security_warnings': []
                    }
                
                # Check memory usage
                try:
                    memory_info = process.memory_info()
                    memory_peak = max(memory_peak, memory_info.rss)
                    
                    if memory_peak > max_memory:
                        process.terminate()
                        return {
                            'success': False,
                            'output': '',
                            'error_message': f'Memory limit exceeded: {memory_peak / (1024 * 1024):.1f}MB',
                            'memory_used_mb': memory_peak / (1024 * 1024),
                            'cpu_usage_percent': 0,
                            'security_scan_passed': True,
                            'security_warnings': []
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                # Read output
                try:
                    stdout, stderr = process.communicate(timeout=0.1)
                    if stdout:
                        output_lines.append(stdout)
                    if stderr:
                        error_lines.append(stderr)
                except subprocess.TimeoutExpired:
                    continue
                
                # Check output size
                total_output = len('\n'.join(output_lines))
                if total_output > max_output:
                    process.terminate()
                    return {
                        'success': False,
                        'output': '',
                        'error_message': f'Output size limit exceeded: {total_output} bytes',
                        'memory_used_mb': memory_peak / (1024 * 1024),
                        'cpu_usage_percent': 0,
                        'security_scan_passed': True,
                        'security_warnings': []
                    }
            
            # Get final output
            stdout, stderr = process.communicate()
            if stdout:
                output_lines.append(stdout)
            if stderr:
                error_lines.append(stderr)
            
            # Combine output
            output = '\n'.join(output_lines)
            error_output = '\n'.join(error_lines)
            
            # Get CPU usage
            cpu_percent = 0
            try:
                cpu_percent = process.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            return {
                'success': process.returncode == 0,
                'output': output,
                'error_message': error_output if process.returncode != 0 else None,
                'memory_used_mb': memory_peak / (1024 * 1024),
                'cpu_usage_percent': cpu_percent,
                'security_scan_passed': True,
                'security_warnings': []
            }
            
        except Exception as e:
            if process:
                process.terminate()
            return {
                'success': False,
                'output': '',
                'error_message': str(e),
                'memory_used_mb': 0,
                'cpu_usage_percent': 0,
                'security_scan_passed': False,
                'security_warnings': [str(e)]
            }
    
    def get_execution_result(self, execution_id: int, user: User) -> Optional[SandboxExecution]:
        """Get execution result by ID"""
        try:
            return SandboxExecution.objects.get(id=execution_id, user=user)
        except SandboxExecution.DoesNotExist:
            return None
    
    def list_user_executions(self, user: User, limit: int = 50) -> List[SandboxExecution]:
        """List executions for a user"""
        return SandboxExecution.objects.filter(user=user).order_by('-created_at')[:limit]
    
    def cleanup_old_executions(self, days: int = 7) -> int:
        """Clean up old execution records"""
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            old_executions = SandboxExecution.objects.filter(created_at__lt=cutoff_date)
            count = old_executions.count()
            old_executions.delete()
            
            logger.info(f"Cleaned up {count} old sandbox executions")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup old executions: {str(e)}")
            return 0


class SecurityError(Exception):
    """Custom exception for security violations"""
    pass
