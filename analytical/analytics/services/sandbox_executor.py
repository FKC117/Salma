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
from pathlib import Path
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
    
    def execute_code(self, code: str, language: str = 'python', timeout: int = 30, 
                    memory_limit: Optional[int] = None, user_id: Optional[int] = None, session_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute code in a secure sandbox environment
        
        Args:
            code: Code to execute
            language: Programming language ('python', 'r', 'javascript')
            timeout: Execution timeout in seconds
            memory_limit: Memory limit in MB
            user_id: User ID for tracking
            session_id: Session ID for tracking
            
        Returns:
            Dict with execution results
        """
        print(f"=== SANDBOX EXECUTOR DEBUG ===")
        print(f"User ID: {user_id}")
        print(f"Session ID: {session_id}")
        print(f"Language: {language}")
        print(f"Timeout: {timeout}")
        print(f"Memory limit: {memory_limit}")
        print(f"Code length: {len(code)}")
        print(f"Code preview: {code[:200]}{'...' if len(code) > 200 else ''}")
        print(f"============================")
        
        execution_id = None
        start_time = time.time()
        
        try:
            # Create execution record
            execution = SandboxExecution.objects.create(
                user_id=user_id,
                session_id=session_id,
                language=language,
                code=code,
                status='pending',
                timeout_seconds=timeout,
                max_memory_mb=memory_limit or self.max_memory_mb
            )
            execution_id = execution.id
            
            print(f"=== EXECUTION RECORD CREATED ===")
            print(f"Execution ID: {execution_id}")
            print(f"Status: {execution.status}")
            print(f"================================")
            
            # Validate code before execution
            validation_result = self._validate_code(code, language)
            if not validation_result['valid']:
                execution.status = 'failed'
                execution.error_message = validation_result['error']
                execution.save()
                
                print(f"=== CODE VALIDATION FAILED ===")
                print(f"Error: {validation_result['error']}")
                print(f"=============================")
                
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'execution_id': execution_id
                }
            
            print(f"=== CODE VALIDATION PASSED ===")
            
            # Execute based on language
            if language.lower() == 'python':
                result = self._execute_python_code(code, execution, timeout, memory_limit or self.max_memory_mb)
            elif language.lower() == 'r':
                result = self._execute_r_code(code, execution, timeout)
            elif language.lower() == 'javascript':
                result = self._execute_javascript_code(code, execution, timeout)
            else:
                raise ValueError(f"Unsupported language: {language}")
            
            # Update execution record with results
            execution.status = result['status']
            execution.output = result.get('output', '')
            execution.error_message = result.get('error', '')
            execution.execution_time_ms = int(result.get('execution_time', 0) * 1000)
            execution.memory_peak_mb = result.get('memory_peak', 0)
            execution.cpu_time_ms = result.get('cpu_time', 0)
            execution.save()
            
            print(f"=== EXECUTION RECORD UPDATED ===")
            print(f"Status: {execution.status}")
            print(f"Output length: {len(execution.output) if execution.output else 0}")
            print(f"Error: {execution.error_message}")
            print(f"Execution time: {execution.execution_time_ms}ms")
            print(f"Memory peak: {execution.memory_peak_mb}MB")
            print(f"================================")
            
            # Add execution_id to result
            result['execution_id'] = execution_id
            
            print(f"=== FINAL RESULT ===")
            print(f"Success: {result.get('success', 'N/A')}")
            print(f"Status: {result.get('status', 'N/A')}")
            print(f"Output preview: {result.get('output', '')[:200] if result.get('output') else 'None'}{'...' if result.get('output', '') and len(result.get('output', '')) > 200 else ''}")
            print(f"===================")
            
            return result
            
        except Exception as e:
            # Update execution record with error
            if execution_id:
                try:
                    execution = SandboxExecution.objects.get(id=execution_id)
                    execution.status = 'failed'
                    execution.error_message = str(e)
                    execution.execution_time_ms = int((time.time() - start_time) * 1000)
                    execution.save()
                except Exception as db_error:
                    print(f"=== DATABASE ERROR ===")
                    print(f"Failed to update execution record: {db_error}")
                    print(f"======================")
            
            error_msg = f"Sandbox execution failed: {str(e)}"
            print(f"=== SANDBOX EXECUTION ERROR ===")
            print(f"Error: {error_msg}")
            print(f"User ID: {user_id}")
            print(f"Session ID: {session_id}")
            print(f"Execution ID: {execution_id}")
            print(f"================================")
            
            return {
                'success': False,
                'error': error_msg,
                'execution_id': execution_id
            }
    
    def _validate_code(self, code: str, language: str) -> Dict[str, Any]:
        """Validate code for security threats"""
        try:
            if language.lower() == 'python':
                return self._validate_python_code(code)
            elif language.lower() == 'r':
                return self._validate_r_code(code)
            elif language.lower() == 'javascript':
                return self._validate_javascript_code(code)
            else:
                raise ValueError(f"Unsupported language: {language}")
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _validate_python_code(self, code: str) -> Dict[str, Any]:
        """Validate Python code for security threats"""
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
        
        return {
            'valid': True,
            'error': None
        }
    
    def _validate_r_code(self, code: str) -> Dict[str, Any]:
        """Validate R code for security threats"""
        # Add R-specific validation logic here
        return {
            'valid': True,
            'error': None
        }
    
    def _validate_javascript_code(self, code: str) -> Dict[str, Any]:
        """Validate JavaScript code for security threats"""
        # Add JavaScript-specific validation logic here
        return {
            'valid': True,
            'error': None
        }
    
    def _execute_python_code(self, code: str, execution: SandboxExecution, timeout: int, memory_limit: int) -> Dict[str, Any]:
        """Execute Python code in isolated sandbox environment"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with resource limits
                result = self._run_with_limits(temp_file, timeout, memory_limit)
                return result
            finally:
                # Clean up
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'execution_time': 0,
                'memory_peak': 0,
                'cpu_time': 0,
                'status': 'failed'
            }
    
    def _execute_r_code(self, code: str, execution: SandboxExecution, timeout: int) -> Dict[str, Any]:
        """Execute R code in isolated sandbox environment"""
        # Add R-specific execution logic here
        return {
            'success': False,
            'output': '',
            'error': 'R execution not implemented',
            'execution_time': 0,
            'memory_peak': 0,
            'cpu_time': 0,
            'status': 'failed'
        }
    
    def _execute_javascript_code(self, code: str, execution: SandboxExecution, timeout: int) -> Dict[str, Any]:
        """Execute JavaScript code in isolated sandbox environment"""
        # Add JavaScript-specific execution logic here
        return {
            'success': False,
            'output': '',
            'error': 'JavaScript execution not implemented',
            'execution_time': 0,
            'memory_peak': 0,
            'cpu_time': 0,
            'status': 'failed'
        }
    
    def _run_with_limits(self, script_path: str, timeout: int, memory_limit: int) -> Dict[str, Any]:
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
            
            # Create psutil process for resource monitoring
            psutil_process = psutil.Process(process.pid)
            
            # Monitor resources
            max_memory = memory_limit * 1024 * 1024  # Convert to bytes
            max_output = self.max_output_size
            
            memory_peak = 0
            
            # Wait for process completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return {
                    'success': False,
                    'output': stdout or '',
                    'error': f'Execution timeout after {timeout} seconds',
                    'execution_time': timeout,
                    'memory_peak': memory_peak / (1024 * 1024),
                    'cpu_time': 0,
                    'status': 'failed'
                }
            
            # Check memory usage after completion
            try:
                memory_info = psutil_process.memory_info()
                memory_peak = memory_info.rss
                if memory_peak > max_memory:
                    return {
                        'success': False,
                        'output': stdout or '',
                        'error': f'Memory limit exceeded: {memory_peak / (1024 * 1024):.1f}MB',
                        'execution_time': time.time() - start_time,
                        'memory_peak': memory_peak / (1024 * 1024),
                        'cpu_time': 0,
                        'status': 'failed'
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # Check output size
            total_output = len(stdout or '') + len(stderr or '')
            if total_output > max_output:
                return {
                    'success': False,
                    'output': stdout or '',
                    'error': f'Output size limit exceeded: {total_output} bytes',
                    'execution_time': time.time() - start_time,
                    'memory_peak': memory_peak / (1024 * 1024),
                    'cpu_time': 0,
                    'status': 'failed'
                }
            
            # Get CPU usage
            cpu_time = 0
            try:
                cpu_time = psutil_process.cpu_times().user
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            return {
                'success': process.returncode == 0,
                'output': stdout or '',
                'error': stderr or None if process.returncode != 0 else None,
                'execution_time': time.time() - start_time,
                'memory_peak': memory_peak / (1024 * 1024),
                'cpu_time': cpu_time,
                'status': 'completed' if process.returncode == 0 else 'failed'
            }
            
        except Exception as e:
            if process:
                process.terminate()
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'execution_time': 0,
                'memory_peak': 0,
                'cpu_time': 0,
                'status': 'failed'
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