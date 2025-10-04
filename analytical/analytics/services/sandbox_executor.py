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

from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)


class SandboxExecutor:
    """
    Service for secure code execution in isolated environment
    """
    
    def __init__(self):
        from analytics.services.audit_trail_manager import AuditTrailManager
        self.audit_manager = AuditTrailManager()
        
        # Security settings
        self.allowed_imports = {
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'scipy', 'sklearn',
            'statsmodels', 'patsy', 'plotly', 'altair', 'plotnine', 'xlsxwriter',
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
            'quit', 'reload',
            'getattr', 'setattr', 'delattr', 'hasattr'
        }
        
        # Resource limits
        self.max_execution_time = 30  # seconds
        self.max_memory_mb = 512  # MB
        self.max_cpu_percent = 80  # %
        self.max_output_size = 20 * 1024 * 1024  # 20MB (increased from 1MB)
        
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
            # Import models here to avoid circular imports
            from analytics.models import SandboxExecution
            # Create execution record
            execution = SandboxExecution.objects.create(
                user_id=user_id,
                session_id=session_id,
                language=language,
                code=code,
                status='pending'
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
            
            # Create SandboxResult if execution was successful
            if result.get('success', False) and execution.status == 'completed':
                try:
                    from analytics.services.sandbox_result_processor import SandboxResultProcessor
                    processor = SandboxResultProcessor()
                    sandbox_result = processor.create_sandbox_result(execution)
                    if sandbox_result:
                        result['sandbox_result_id'] = sandbox_result.id
                        print(f"=== SANDBOX RESULT CREATED ===")
                        print(f"SandboxResult ID: {sandbox_result.id}")
                        print(f"Image count: {sandbox_result.image_count}")
                        print(f"=============================")
                except Exception as e:
                    print(f"=== SANDBOX RESULT ERROR ===")
                    print(f"Failed to create SandboxResult: {str(e)}")
                    print(f"=============================")
            
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
                    from analytics.models import SandboxExecution
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
            # Try to parse code, with automatic syntax correction
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                # Attempt to fix common LLM syntax errors
                corrected_code = self._fix_common_syntax_errors(code)
                if corrected_code != code:
                    print(f"=== SYNTAX CORRECTION APPLIED ===")
                    print(f"Original error: {e}")
                    print(f"Applied automatic syntax correction")
                    print(f"================================")
                    tree = ast.parse(corrected_code)
                else:
                    raise e
            
            # Check for forbidden imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.forbidden_imports:
                            available_libs = ', '.join(sorted(self.allowed_imports))
                            raise SecurityError(f"Forbidden import: {alias.name}. Available libraries: {available_libs}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module in self.forbidden_imports:
                        available_libs = ', '.join(sorted(self.allowed_imports))
                        raise SecurityError(f"Forbidden import: {node.module}. Available libraries: {available_libs}")
                
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
    
    def _fix_common_syntax_errors(self, code: str) -> str:
        """Fix common LLM-generated syntax errors using multiple approaches"""
        try:
            # Method 1: Try advanced indentation fixing (no external dependencies)
            corrected_code = self._fix_indentation_advanced(code)
            if corrected_code and corrected_code != code:
                print(f"✅ Advanced indentation correction applied")
                return corrected_code
            
            # Method 2: Try manual indentation fixing
            corrected_code = self._fix_indentation_manually(code)
            if corrected_code and corrected_code != code:
                print(f"✅ Manual indentation correction applied")
                return corrected_code
            
            # Method 3: Try string literal fixing
            corrected_code = self._fix_string_literals(code)
            if corrected_code and corrected_code != code:
                print(f"✅ String literal correction applied")
                return corrected_code
            
            # Method 4: Try basic syntax fixing
            corrected_code = self._fix_basic_syntax(code)
            if corrected_code and corrected_code != code:
                print(f"✅ Basic syntax correction applied")
                return corrected_code
            
            print(f"⚠️ No automatic correction could be applied")
            return code
            
        except Exception as e:
            print(f"❌ Error in syntax correction: {e}")
            return code
    
    def _fix_indentation_advanced(self, code: str) -> str:
        """Advanced indentation fixing without external dependencies"""
        try:
            lines = code.split('\n')
            fixed_lines = []
            indent_level = 0
            in_multiline_string = False
            string_delimiter = None
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Skip empty lines and comments
                if not stripped or stripped.startswith('#'):
                    fixed_lines.append(line)
                    continue
                
                # Handle multiline strings
                if not in_multiline_string:
                    # Check for start of multiline string
                    if '"""' in stripped or "'''" in stripped:
                        in_multiline_string = True
                        string_delimiter = '"""' if '"""' in stripped else "'''"
                        # If string starts and ends on same line, it's not multiline
                        if stripped.count(string_delimiter) >= 2:
                            in_multiline_string = False
                            string_delimiter = None
                else:
                    # Check for end of multiline string
                    if string_delimiter in stripped:
                        in_multiline_string = False
                        string_delimiter = None
                
                # Don't fix indentation inside multiline strings
                if in_multiline_string:
                    fixed_lines.append(line)
                    continue
                
                # Check if this line should be indented based on previous line
                if i > 0:
                    prev_line = lines[i-1].rstrip()
                    
                    # If previous line ends with colon, this line should be indented
                    if prev_line.endswith(':'):
                        indent_level += 1
                    
                    # Check for dedentation keywords
                    elif stripped.startswith(('else:', 'elif ', 'except', 'finally:')):
                        indent_level = max(0, indent_level - 1)
                
                # Apply indentation
                indent_str = '    ' * indent_level
                fixed_lines.append(indent_str + stripped)
            
            fixed_code = '\n'.join(fixed_lines)
            
            # Validate the fixed code
            try:
                ast.parse(fixed_code)
                return fixed_code
            except SyntaxError as e:
                print(f"⚠️ Advanced correction still has syntax error: {e}")
                return code  # Return original if our fix didn't work
                
        except Exception as e:
            print(f"⚠️ Advanced indentation correction failed: {e}")
            return code
    
    def _calculate_expected_indent(self, lines: list, current_index: int, indent_stack: list) -> int:
        """Calculate expected indentation level for a line"""
        if current_index == 0:
            return 0  # First line should not be indented
        
        prev_line = lines[current_index - 1].rstrip()
        current_line = lines[current_index].strip()
        
        # If previous line ends with colon, we need to indent
        if prev_line.endswith(':'):
            return len(indent_stack) + 1
        
        # Check for dedentation keywords
        dedent_keywords = ['else:', 'elif ', 'except', 'finally:', 'except ']
        if any(current_line.startswith(keyword) for keyword in dedent_keywords):
            return max(0, len(indent_stack) - 1)
        
        # Check for same-level keywords
        same_level_keywords = ['return', 'break', 'continue', 'pass', 'raise']
        if any(current_line.startswith(keyword) for keyword in same_level_keywords):
            return len(indent_stack)
        
        # Default: same indentation as previous line
        return len(indent_stack)
    
    def _fix_indentation_manually(self, code: str) -> str:
        """Manually fix indentation issues with comprehensive logic"""
        try:
            lines = code.split('\n')
            fixed_lines = []
            indent_level = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Skip empty lines and comments
                if not stripped or stripped.startswith('#'):
                    fixed_lines.append(line)
                    continue
                
                # Determine if this line needs indentation
                needs_indent = False
                
                # Check if previous line ends with colon
                if i > 0:
                    prev_line = lines[i-1].rstrip()
                    if prev_line.endswith(':'):
                        needs_indent = True
                        indent_level += 1
                
                # Check for dedentation keywords (else, elif, except, finally)
                dedent_keywords = ['else:', 'elif ', 'except', 'finally:', 'except ']
                if any(stripped.startswith(keyword) for keyword in dedent_keywords):
                    indent_level = max(0, indent_level - 1)
                    needs_indent = True
                
                # Apply indentation
                if needs_indent or not line.startswith(' ') and not line.startswith('\t'):
                    indent_str = '    ' * indent_level
                    fixed_lines.append(indent_str + stripped)
                else:
                    fixed_lines.append(line)
            
            fixed_code = '\n'.join(fixed_lines)
            
            # Validate the fixed code
            try:
                ast.parse(fixed_code)
                return fixed_code
            except SyntaxError as e:
                print(f"⚠️ Manual correction still has syntax error: {e}")
                return code
                
        except Exception as e:
            print(f"⚠️ Manual indentation correction failed: {e}")
            return code
    
    def _fix_basic_syntax(self, code: str) -> str:
        """Fix basic syntax issues"""
        lines = code.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Fix: Missing indentation after try/except/if/else/for/while/def/class
            if i > 0:
                prev_line = lines[i-1].rstrip()
                
                # Check if previous line ends with colon and current line needs indentation
                if (prev_line.endswith(':') and 
                    line.strip() and 
                    not line.startswith(' ') and 
                    not line.startswith('\t') and
                    not line.strip().startswith('#') and
                    not line.strip().startswith('"""') and
                    not line.strip().startswith("'''")):
                    
                    # Add proper indentation (4 spaces)
                    fixed_lines.append('    ' + line)
                    i += 1
                    continue
            
            # Fix: Missing indentation for continuation lines
            if (line.strip() and 
                not line.startswith(' ') and 
                not line.startswith('\t') and
                not line.strip().startswith('#') and
                not line.strip().startswith('import') and
                not line.strip().startswith('from') and
                not line.strip().startswith('def') and
                not line.strip().startswith('class') and
                not line.strip().startswith('if') and
                not line.strip().startswith('else') and
                not line.strip().startswith('elif') and
                not line.strip().startswith('for') and
                not line.strip().startswith('while') and
                not line.strip().startswith('try') and
                not line.strip().startswith('except') and
                not line.strip().startswith('finally') and
                not line.strip().startswith('with') and
                not line.strip().startswith('"""') and
                not line.strip().startswith("'''") and
                i > 0 and
                any(lines[i-1].rstrip().endswith(x) for x in [':', '\\', '(', '[', '{'])):
                
                # Add indentation for continuation
                fixed_lines.append('    ' + line)
                i += 1
                continue
            
            fixed_lines.append(line)
            i += 1
        
        return '\n'.join(fixed_lines)
    
    def _fix_string_literals(self, code: str) -> str:
        """Fix unterminated string literals"""
        try:
            lines = code.split('\n')
            fixed_lines = []
            in_string = False
            string_delimiter = None
            
            for i, line in enumerate(lines):
                if not in_string:
                    # Check for string start
                    if '"""' in line:
                        string_delimiter = '"""'
                        if line.count('"""') % 2 == 1:  # Odd count means unterminated
                            in_string = True
                    elif "'''" in line:
                        string_delimiter = "'''"
                        if line.count("'''") % 2 == 1:  # Odd count means unterminated
                            in_string = True
                    elif '"' in line and '"""' not in line:
                        string_delimiter = '"'
                        if line.count('"') % 2 == 1:  # Odd count means unterminated
                            in_string = True
                    elif "'" in line and "'''" not in line:
                        string_delimiter = "'"
                        if line.count("'") % 2 == 1:  # Odd count means unterminated
                            in_string = True
                    
                    fixed_lines.append(line)
                else:
                    # We're inside a string, look for the end
                    if string_delimiter in line:
                        in_string = False
                        string_delimiter = None
                    
                    fixed_lines.append(line)
            
            # If we're still in a string at the end, close it
            if in_string:
                fixed_lines.append(string_delimiter)
            
            fixed_code = '\n'.join(fixed_lines)
            
            # Validate the fixed code
            try:
                ast.parse(fixed_code)
                return fixed_code
            except SyntaxError:
                return code  # Return original if our fix didn't work
                
        except Exception as e:
            print(f"⚠️ String literal correction failed: {e}")
            return code
    
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
    
    def _get_dataset_code(self, session_id: Optional[int]) -> str:
        """Get dataset loading code for the sandbox"""
        if not session_id:
            return ""
        
        try:
            from analytics.models import AnalysisSession, Dataset
            
            # Get the analysis session
            session = AnalysisSession.objects.get(id=session_id)
            dataset = session.primary_dataset
            
            if not dataset:
                return ""
            
            # Get the dataset file path
            dataset_path = dataset.parquet_path
            if not dataset_path:
                return ""
            
            # Construct full path
            from django.conf import settings
            full_dataset_path = os.path.join(settings.MEDIA_ROOT, dataset_path)
            if not os.path.exists(full_dataset_path):
                return ""
            
            # Generate dataset loading code (escape backslashes for Windows paths)
            escaped_path = full_dataset_path.replace('\\', '\\\\')
            dataset_code = f'''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import os

# Load the dataset
dataset_path = r"{full_dataset_path}"
if os.path.exists(dataset_path):
    df = pd.read_parquet(dataset_path)
    print(f"Dataset loaded: {{df.shape[0]}} rows, {{df.shape[1]}} columns")
    print(f"Columns: {{list(df.columns)}}")
else:
    print("Dataset file not found")
    df = None
'''
            return dataset_code
            
        except Exception as e:
            logger.error(f"Error getting dataset code: {str(e)}")
            return ""
    
    def _execute_python_code(self, code: str, execution, timeout: int, memory_limit: int) -> Dict[str, Any]:
        """Execute Python code in isolated sandbox environment"""
        try:
            # Apply syntax correction to user code
            corrected_code = self._fix_common_syntax_errors(code)
            
            # Fix common file reading patterns
            corrected_code = self._fix_file_reading_patterns(corrected_code)
            
            # Modify code to handle matplotlib plots properly
            # Add non-interactive backend and image saving
            modified_code = self._modify_matplotlib_code(corrected_code)
            
            # Load dataset if session_id is provided
            dataset_code = self._get_dataset_code(execution.session_id)
            
            # Combine matplotlib setup, dataset loading code, and user's code
            # Order is important: matplotlib setup first, then dataset, then user code
            matplotlib_setup = self._get_matplotlib_setup()
            full_code = matplotlib_setup + '\n' + dataset_code + '\n' + modified_code
            
            # Create temporary file with UTF-8 encoding
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(full_code)
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
    
    def _get_matplotlib_setup(self) -> str:
        """Get the matplotlib setup code with image capture overrides"""
        return '''
import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import os
import base64
import io

# Store original functions
original_show = plt.show
original_savefig = plt.savefig

# Override plt.show to save the figure
def custom_show(*args, **kwargs):
    print("=== CUSTOM_SHOW DEBUG ===")
    print("custom_show called")
    # Save the figure
    import matplotlib.pyplot as plt  # Import here to ensure it's available
    import os
    import uuid
    import time
    fig = plt.gcf()
    print(f"Figure has axes: {fig.get_axes()}")
    print(f"Number of axes: {len(fig.get_axes())}")
    if fig.get_axes():  # Only save if there are axes
        print("Saving figure to buffer and file...")
        
        # Create unique filename
        timestamp = int(time.time() * 1000)  # milliseconds
        unique_id = str(uuid.uuid4())[:8]
        filename = f"sandbox_chart_{timestamp}_{unique_id}.png"
        
        # Ensure sandbox directory exists
        sandbox_dir = "/tmp/sandbox"  # Will be mapped to media/sandbox
        os.makedirs(sandbox_dir, exist_ok=True)
        file_path = os.path.join(sandbox_dir, filename)
        
        # Save to bytes buffer for base64
        import io  # Import here to ensure it's available
        buffer = io.BytesIO()
        plt.tight_layout()
        # Use the original savefig to avoid recursion
        original_savefig(buffer, format='png', dpi=150, bbox_inches="tight")
        buffer.seek(0)
        
        # Also save to file
        original_savefig(file_path, format='png', dpi=150, bbox_inches="tight")
        print(f"Image saved to file: {file_path}")
        
        # Convert to base64
        import base64  # Import here to ensure it's available
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        print(f"Image base64 length: {len(image_base64)}")
        print(f"__SANDBOX_IMAGE_BASE64__data:image/png;base64,{image_base64}")
        print(f"__SANDBOX_IMAGE_FILE__{file_path}")
        print("=== IMAGE SAVED ===")
    else:
        print("No axes found, skipping image save")
    print("Calling original show...")
    original_show(*args, **kwargs)
    print("=== CUSTOM_SHOW COMPLETE ===")

# Override plt.savefig to capture images
def custom_savefig(*args, **kwargs):
    print("=== CUSTOM_SAVEFIG DEBUG ===")
    print(f"custom_savefig called with args: {args}")
    print(f"custom_savefig called with kwargs: {kwargs}")
    # Save the figure to bytes buffer
    import matplotlib.pyplot as plt  # Import here to ensure it's available
    import io  # Import here to ensure it's available
    import os
    import uuid
    import time
    
    # Create unique filename
    timestamp = int(time.time() * 1000)  # milliseconds
    unique_id = str(uuid.uuid4())[:8]
    filename = f"sandbox_chart_{timestamp}_{unique_id}.png"
    
    # Ensure sandbox directory exists
    sandbox_dir = "/tmp/sandbox"  # Will be mapped to media/sandbox
    os.makedirs(sandbox_dir, exist_ok=True)
    file_path = os.path.join(sandbox_dir, filename)
    
    buffer = io.BytesIO()
    plt.tight_layout()
    # Use the original savefig to avoid recursion
    original_savefig(buffer, format='png', dpi=150, bbox_inches="tight")
    buffer.seek(0)
    
    # Also save to file
    original_savefig(file_path, format='png', dpi=150, bbox_inches="tight")
    print(f"Image saved to file: {file_path}")
    
    # Convert to base64
    import base64  # Import here to ensure it's available
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    print(f"Image base64 length: {len(image_base64)}")
    print(f"__SANDBOX_IMAGE_BASE64__data:image/png;base64,{image_base64}")
    print(f"__SANDBOX_IMAGE_FILE__{file_path}")
    print("=== IMAGE SAVED VIA SAVEFIG ===")
    
    # Also call the original savefig if a filename was provided (for compatibility)
    if args and isinstance(args[0], str):
        print(f"Also saving to user-specified file: {args[0]}")
        original_savefig(*args, **kwargs)
    print("=== CUSTOM_SAVEFIG COMPLETE ===")

plt.show = custom_show
plt.savefig = custom_savefig
'''

    def _modify_matplotlib_code(self, code: str) -> str:
        """Modify code to handle matplotlib plots properly"""
        # The matplotlib setup is now handled separately in _get_matplotlib_setup()
        # This method just returns the code as-is since setup is done at the beginning
        return code
    
    def _fix_file_reading_patterns(self, code: str) -> str:
        """Fix common file reading patterns that might cause errors"""
        try:
            # Check if code contains file reading operations
            file_reading_patterns = [
                'pd.read_csv(',
                'pd.read_excel(',
                'pd.read_json(',
                'pd.read_parquet(',
                'pd.read_table(',
                'pd.read_html(',
                'pd.read_xml(',
                'pd.read_feather(',
                'pd.read_pickle(',
                'pd.read_sql(',
                'pd.read_sql_table(',
                'pd.read_sql_query(',
            ]
            
            # Check if any file reading patterns are present
            has_file_reading = any(pattern in code for pattern in file_reading_patterns)
            
            if has_file_reading:
                # Add helpful comment at the beginning
                helpful_comment = '''
# NOTE: File reading operations detected in your code.
# Files are not available in the sandbox environment.
# The dataset has been automatically loaded as 'df' from your analysis session.
# You can use 'df' directly for your analysis.
# If you need to read a specific file, please upload it to your dataset first.

'''
                
                # Process lines to handle try-except blocks properly
                lines = code.split('\n')
                modified_lines = []
                i = 0
                
                while i < len(lines):
                    line = lines[i]
                    
                    # Check if line contains file reading
                    if any(pattern in line for pattern in file_reading_patterns):
                        # Check if this line is inside a try block
                        try_indent = self._get_indentation_level(line)
                        
                        # Look backwards to see if we're in a try block
                        in_try_block = False
                        for j in range(i-1, -1, -1):
                            prev_line = lines[j].strip()
                            if not prev_line or prev_line.startswith('#'):
                                continue
                            prev_indent = self._get_indentation_level(lines[j])
                            
                            if prev_indent < try_indent and prev_line.endswith(':'):
                                if prev_line.startswith('try') or prev_line.startswith('except') or prev_line.startswith('finally'):
                                    in_try_block = True
                                    break
                                elif prev_line.startswith('if') or prev_line.startswith('for') or prev_line.startswith('while') or prev_line.startswith('def') or prev_line.startswith('class'):
                                    break
                        
                        if in_try_block:
                            # Replace with a pass statement to maintain try block structure
                            indent = ' ' * try_indent
                            modified_lines.append(f"{indent}pass  # File reading replaced with pass - using pre-loaded 'df' instead")
                        else:
                            # Comment out the line normally
                            modified_lines.append(f"# {line}  # File not available in sandbox - using pre-loaded 'df' instead")
                    else:
                        modified_lines.append(line)
                    
                    i += 1
                
                modified_code = helpful_comment + '\n'.join(modified_lines)
                return modified_code
            
            return code
            
        except Exception as e:
            logger.error(f"Error fixing file reading patterns: {str(e)}")
            return code
    
    def _get_indentation_level(self, line: str) -> int:
        """Get the indentation level of a line"""
        return len(line) - len(line.lstrip())
    
    def _execute_r_code(self, code: str, execution, timeout: int) -> Dict[str, Any]:
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
    
    def _execute_javascript_code(self, code: str, execution, timeout: int) -> Dict[str, Any]:
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
            # Start process with UTF-8 encoding to handle Unicode characters
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'  # Force Python to use UTF-8 for I/O
            
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace problematic characters instead of failing
                cwd=str(self.sandbox_dir),
                env=env
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
    
    def get_execution_result(self, execution_id: int, user) -> Optional[Any]:
        """Get execution result by ID"""
        try:
            from analytics.models import SandboxExecution
            return SandboxExecution.objects.get(id=execution_id, user=user)
        except:
            return None
    
    def list_user_executions(self, user, limit: int = 50) -> List[Any]:
        """List executions for a user"""
        from analytics.models import SandboxExecution
        return list(SandboxExecution.objects.filter(user=user).order_by('-created_at')[:limit])
    
    def cleanup_old_executions(self, days: int = 7) -> int:
        """Clean up old execution records"""
        try:
            from analytics.models import SandboxExecution
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