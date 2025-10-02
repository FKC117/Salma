"""
Sandbox Views for Code Execution Interface

This module provides views for the dedicated sandbox interface where users can
execute Python code and view results in a clean, focused environment.
"""

import json
import logging
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.utils import timezone

from analytics.models import User, AnalysisSession, SandboxExecution
from analytics.services.sandbox_executor import SandboxExecutor
from analytics.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


class SandboxView(View):
    """
    Main sandbox interface view
    """
    
    @method_decorator(login_required)
    def get(self, request):
        """Render the sandbox interface"""
        try:
            # Get or create analysis session
            session_manager = SessionManager()
            
            # Get user's first dataset or create a default session
            from analytics.models import Dataset
            user_datasets = Dataset.objects.filter(user=request.user)
            
            if user_datasets.exists():
                # Use the first dataset
                primary_dataset = user_datasets.first()
                analysis_session = session_manager.create_session(
                    user=request.user,
                    dataset=primary_dataset,
                    session_name="Sandbox Session"
                )
            else:
                # No datasets available - create a session without dataset
                analysis_session = None
            
            # Get recent executions for this user
            recent_executions = SandboxExecution.objects.filter(
                user=request.user
            ).order_by('-created_at')[:10]
            
            context = {
                'user': request.user,
                'session': analysis_session,
                'recent_executions': recent_executions,
                'page_title': 'Code Sandbox',
                'page_description': 'Execute Python code and view results'
            }
            
            return render(request, 'analytics/sandbox.html', context)
            
        except Exception as e:
            logger.error(f"Error rendering sandbox view: {str(e)}")
            return render(request, 'analytics/sandbox.html', {
                'error': 'Failed to load sandbox interface'
            })


@method_decorator(csrf_exempt, name='dispatch')
class ExecuteCodeView(View):
    """
    API endpoint for executing code in the sandbox
    """
    
    def post(self, request):
        """Execute Python code and return results"""
        try:
            # Parse request data
            data = json.loads(request.body)
            code = data.get('code', '').strip()
            language = data.get('language', 'python')
            
            if not code:
                return JsonResponse({
                    'success': False,
                    'error': 'No code provided'
                }, status=400)
            
            # Get user and session
            user = request.user if request.user.is_authenticated else None
            if not user:
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required'
                }, status=401)
            
            # Get or create analysis session
            session_manager = SessionManager()
            
            # Get user's first dataset or create a default session
            from analytics.models import Dataset
            user_datasets = Dataset.objects.filter(user=user)
            
            if user_datasets.exists():
                # Use the first dataset
                primary_dataset = user_datasets.first()
                analysis_session = session_manager.create_session(
                    user=user,
                    dataset=primary_dataset,
                    session_name="Sandbox Session"
                )
            else:
                # No datasets available - create a session without dataset
                analysis_session = None
            
            # Execute code
            sandbox_executor = SandboxExecutor()
            result = sandbox_executor.execute_code(
                code=code,
                language=language,
                user_id=user.id,
                session_id=analysis_session.id if analysis_session else None,
                timeout=30
            )
            
            # Process the result for display
            processed_result = self._process_execution_result(result)
            
            return JsonResponse({
                'success': True,
                'result': processed_result,
                'execution_id': result.get('execution_id'),
                'timestamp': timezone.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Execution failed: {str(e)}'
            }, status=500)
    
    def _process_execution_result(self, result):
        """
        Process execution result for clean display
        """
        try:
            processed = {
                'success': result.get('success', False),
                'status': result.get('status', 'unknown'),
                'output': '',
                'error': '',
                'execution_time_ms': result.get('execution_time_ms', 0),
                'memory_peak_mb': result.get('memory_peak', 0),
                'images': []
            }
            
            if result.get('success'):
                # Process output for images and clean text
                output = result.get('output', '')
                processed['output'] = self._clean_output(output)
                processed['images'] = self._extract_images(output)
            else:
                processed['error'] = result.get('error', 'Unknown error')
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing execution result: {str(e)}")
            return {
                'success': False,
                'error': f'Result processing failed: {str(e)}',
                'output': '',
                'images': []
            }
    
    def _clean_output(self, output):
        """
        Clean output text by removing image markers and formatting
        """
        try:
            # Remove image markers
            import re
            cleaned = re.sub(r'__SANDBOX_IMAGE_BASE64__[^\n]*', '', output)
            
            # Clean up extra whitespace
            cleaned = cleaned.strip()
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning output: {str(e)}")
            return output
    
    def _extract_images(self, output):
        """
        Extract base64 images from output
        """
        try:
            import re
            image_pattern = r'__SANDBOX_IMAGE_BASE64__(data:image/png;base64,[A-Za-z0-9+/=]+)'
            matches = re.findall(image_pattern, output)
            
            images = []
            for image_data in matches:
                images.append({
                    'data': image_data,
                    'type': 'png'
                })
            
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            return []


class SandboxHistoryView(View):
    """
    View for retrieving sandbox execution history
    """
    
    @method_decorator(login_required)
    def get(self, request):
        """Get execution history for the user"""
        try:
            limit = int(request.GET.get('limit', 20))
            
            executions = SandboxExecution.objects.filter(
                user=request.user
            ).order_by('-created_at')[:limit]
            
            history = []
            for execution in executions:
                history.append({
                    'id': execution.id,
                    'code': execution.code[:200] + '...' if len(execution.code) > 200 else execution.code,
                    'status': execution.status,
                    'created_at': execution.created_at.isoformat(),
                    'execution_time_ms': execution.execution_time_ms,
                    'output_preview': execution.output[:100] + '...' if execution.output and len(execution.output) > 100 else execution.output
                })
            
            return JsonResponse({
                'success': True,
                'history': history
            })
            
        except Exception as e:
            logger.error(f"Error retrieving sandbox history: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

