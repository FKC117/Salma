"""
API Views for Analytics System
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import get_user_model

from analytics.models import Dataset, DatasetColumn, AuditTrail
from analytics.services.file_processing import FileProcessingService
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.session_manager import SessionManager
from analytics.services.analysis_executor import AnalysisExecutor
from analytics.services.rag_service import RAGService
from analytics.services.llm_processor import LLMProcessor
from analytics.services.agentic_ai_controller import AgenticAIController
from analytics.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)
User = get_user_model()


class UploadViewSet(viewsets.ViewSet):
    """
    File upload endpoint for dataset processing
    """
    parser_classes = [MultiPartParser, FormParser]
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload and process dataset file
        """
        try:
            # Validate request
            if 'file' not in request.FILES:
                return Response({
                    'success': False,
                    'error': 'No file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            # Make dataset name optional - will default to filename in service
            dataset_name = request.data.get('name', '') or None
            
            # Get authenticated user
            if not request.user.is_authenticated:
                return Response({
                    'success': False,
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            
            # Process file
            try:
                file_service = FileProcessingService()
                result = file_service.process_file(
                    uploaded_file=file,
                    user=user,
                    dataset_name=dataset_name
                )
                
                # Check if processing was successful
                if not result.get('success', False):
                    return Response({
                        'success': False,
                        'error': result.get('error', 'File processing failed')
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"File processing error: {str(e)}")
                return Response({
                    'success': False,
                    'error': f'File processing failed: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If we get here, processing was successful
            # Log audit trail
            audit_manager = AuditTrailManager()
            actual_dataset_name = result.get('dataset_name', dataset_name or file.name)
            audit_manager.log_user_action(
                user_id=user.id,
                action_type='file_upload',
                resource_type='dataset',
                resource_id=result['dataset_id'],
                resource_name=actual_dataset_name,
                action_description=f"Uploaded dataset: {actual_dataset_name}",
                success=True
            )
            
            # Get the dataset object to include more details
            try:
                dataset = Dataset.objects.get(id=result['dataset_id'])
                dataset_info = {
                    'id': dataset.id,
                    'name': dataset.name,
                    'row_count': dataset.row_count,
                    'column_count': dataset.column_count,
                    'file_size_bytes': dataset.file_size_bytes,
                    'created_at': dataset.created_at.strftime('%Y-%m-%d %H:%M'),
                }
            except Dataset.DoesNotExist:
                dataset_info = {}
            
            return Response({
                'success': True,
                'dataset_id': result['dataset_id'],
                'session_id': result.get('session_id'),
                'dataset_info': dataset_info,
                'message': f'Dataset "{actual_dataset_name}" uploaded successfully',
                'columns': result.get('columns', [])
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Upload endpoint error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SessionViewSet(viewsets.ViewSet):
    """
    Analysis session management
    """
    
    @action(detail=False, methods=['post'])
    def create_session(self, request):
        """
        Create new analysis session
        """
        try:
            # Validate request
            dataset_id = request.data.get('dataset_id')
            if not dataset_id:
                return Response({
                    'success': False,
                    'error': 'Dataset ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user
            try:
                user = User.objects.first()
                if not user:
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            except Exception as e:
                logger.error(f"User creation failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get dataset
            try:
                dataset = Dataset.objects.get(id=dataset_id)
            except Dataset.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Dataset not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Create session
            session_manager = SessionManager()
            session = session_manager.create_session(
                user=user,
                dataset=dataset,
                session_name=request.data.get('session_name', f'Session {timezone.now().strftime("%Y-%m-%d %H:%M")}')
            )
            
            return Response({
                'success': True,
                'session_id': session.id,
                'message': 'Analysis session created successfully'
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Session creation error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalysisViewSet(viewsets.ViewSet):
    """
    Analysis execution endpoints
    """
    
    @action(detail=False, methods=['post'])
    def execute(self, request):
        """
        Execute analysis tool
        """
        try:
            # Validate request
            required_fields = ['session_id', 'tool_name', 'parameters']
            for field in required_fields:
                if field not in request.data:
                    return Response({
                        'success': False,
                        'error': f'{field} is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user
            try:
                user = User.objects.first()
                if not user:
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            except Exception as e:
                logger.error(f"User creation failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get session
            from analytics.models import AnalysisSession
            try:
                session = AnalysisSession.objects.get(id=request.data['session_id'])
            except AnalysisSession.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Session not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Execute analysis
            executor = AnalysisExecutor()
            result = executor.execute_analysis(
                tool_name=request.data['tool_name'],
                parameters=request.data['parameters'],
                session=session,
                user=user
            )
            
            return Response({
                'success': True,
                'result_id': result['analysis_id'],
                'message': 'Analysis executed successfully',
                'output': result.get('result_data', {}),
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Analysis execution error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RAGViewSet(viewsets.ViewSet):
    """
    RAG (Retrieval-Augmented Generation) endpoints
    """
    
    @action(detail=False, methods=['post'])
    def upsert(self, request):
        """
        Upsert content to RAG system
        """
        try:
            # Validate request
            required_fields = ['content', 'metadata']
            for field in required_fields:
                if field not in request.data:
                    return Response({
                        'success': False,
                        'error': f'{field} is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user
            try:
                user = User.objects.first()
                if not user:
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            except Exception as e:
                logger.error(f"User creation failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Upsert to RAG
            rag_service = RAGService()
            # Use the correct method name
            vector_note = rag_service.create_vector_note(
                title=request.data.get('title', 'Untitled'),
                text=request.data['content'],
                scope=request.data.get('scope', 'global'),
                content_type=request.data.get('content_type', 'user_content'),
                user=user,
                metadata=request.data['metadata']
            )
            
            if vector_note:
                return Response({
                    'success': True,
                    'vector_id': vector_note.id,
                    'message': 'Content upserted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'RAG upsert failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"RAG upsert error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search RAG system
        """
        try:
            query = request.query_params.get('query')
            if not query:
                return Response({
                    'success': False,
                    'error': 'Query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user
            try:
                user = User.objects.first()
                if not user:
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            except Exception as e:
                logger.error(f"User creation failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Search RAG
            rag_service = RAGService()
            # Use the correct method name
            results = rag_service.search_vectors_by_text(
                query=query,
                user=user,
                top_k=int(request.query_params.get('limit', 10))
            )
            
            return Response({
                'success': True,
                'results': results,
                'message': f'Found {len(results)} results'
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"RAG search error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """
        Clear RAG system for user
        """
        try:
            # Get user
            try:
                user = User.objects.first()
                if not user:
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            except Exception as e:
                logger.error(f"User creation failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Clear RAG
            rag_service = RAGService()
            # Use the correct method name
            result = rag_service.clear_user_data(user)
            
            if result:
                return Response({
                    'success': True,
                    'message': 'RAG content cleared successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'RAG clear failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"RAG clear error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatViewSet(viewsets.ViewSet):
    """
    Chat message endpoints
    """
    
    def _format_message_content(self, content):
        """
        Format message content with professional styling
        """
        import re
        
        # Convert markdown-style formatting to HTML
        # Bold text
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        # Italic text
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        # Code blocks
        content = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)
        # Inline code
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        # Line breaks
        content = content.replace('\n', '<br>')
        
        return content
    
    @action(detail=False, methods=['post'])
    def messages(self, request):
        """
        Send chat message and get LLM response
        """
        try:
            # Validate request
            if 'message' not in request.data:
                return Response({
                    'success': False,
                    'error': 'Message is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user
            try:
                user = User.objects.first()
                if not user:
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            except Exception as e:
                logger.error(f"User creation failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Process message
            llm_processor = LLMProcessor()
            # Use the correct method name
            result = llm_processor.process_message(
                user=user,
                message=request.data['message'],
                session_id=request.data.get('session_id'),
                context=request.data.get('context', {})
            )
            
            if result['success']:
                # Return formatted HTML response for HTMX
                from django.template.loader import render_to_string
                from django.utils import timezone
                from django.http import HttpResponse
                
                # Format the response content
                formatted_content = self._format_message_content(result['response'])
                
                # Render the chat message partial
                html_response = render_to_string('analytics/partials/chat_message.html', {
                    'message_type': 'assistant',
                    'message_content': formatted_content,
                    'timestamp': timezone.now().strftime('%H:%M'),
                    'message_metadata': True,
                    'token_count': result.get('total_tokens', 0),
                    'cost': result.get('cost', 0.0)
                })
                
                return HttpResponse(html_response, content_type='text/html')
            else:
                # Return error as HTML
                from django.utils import timezone
                from django.http import HttpResponse
                
                error_html = f'''
                <div class="chat-message slide-in">
                    <div class="message-content assistant error">
                        <div class="message-body">
                            <i class="bi bi-exclamation-triangle text-warning"></i>
                            <strong>Error:</strong> {result.get('error', 'Message processing failed')}
                        </div>
                    </div>
                    <div class="message-time">{timezone.now().strftime('%H:%M')}</div>
                </div>
                '''
                return HttpResponse(error_html, content_type='text/html')
                
        except Exception as e:
            logger.error(f"Chat message error: {str(e)}", exc_info=True)
            from django.utils import timezone
            from django.http import HttpResponse
            
            error_html = f'''
            <div class="chat-message slide-in">
                <div class="message-content assistant error">
                    <div class="message-body">
                        <i class="bi bi-exclamation-triangle text-danger"></i>
                        <strong>System Error:</strong> Internal server error. Please try again.
                    </div>
                </div>
                <div class="message-time">{timezone.now().strftime('%H:%M')}</div>
            </div>
            '''
            return HttpResponse(error_html, content_type='text/html', status=500)


class ToolsViewSet(viewsets.ViewSet):
    """
    Tools registry endpoints
    """
    
    @action(detail=False, methods=['get'])
    def list_tools(self, request):
        """
        List available analysis tools
        """
        try:
            tool_registry = ToolRegistry()
            tools = tool_registry.get_all_tools()
            
            return Response({
                'success': True,
                'tools': [{
                    'name': tool.name,
                    'display_name': tool.display_name,
                    'description': tool.description,
                    'category': tool.category
                } for tool in tools],
                'message': f'Found {len(tools)} tools'
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Tools list error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentViewSet(viewsets.ViewSet):
    """
    Agentic AI endpoints
    """
    
    @action(detail=False, methods=['post'])
    def run(self, request):
        """
        Run agentic AI analysis
        """
        try:
            # Validate request
            if 'session_id' not in request.data:
                return Response({
                    'success': False,
                    'error': 'Session ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user
            try:
                user = User.objects.first()
                if not user:
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            except Exception as e:
                logger.error(f"User creation failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get session
            from analytics.models import AnalysisSession
            try:
                session = AnalysisSession.objects.get(id=request.data['session_id'])
            except AnalysisSession.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Session not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Run agent
            agent_controller = AgenticAIController()
            # Use the correct method name
            agent_run = agent_controller.start_agent_run(
                user=user,
                dataset=session.primary_dataset,
                goal=request.data.get('objective', 'Analyze the dataset'),
                constraints={
                    'max_steps': int(request.data.get('max_steps', 10))
                }
            )
            
            if agent_run:
                return Response({
                    'success': True,
                    'agent_run_id': agent_run.id,
                    'message': 'Agent run started successfully',
                    'status': agent_run.status
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Agent run failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Agent run error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuditViewSet(viewsets.ViewSet):
    """
    Audit trail endpoints
    """
    
    @action(detail=False, methods=['get'])
    def trail(self, request):
        """
        Get audit trail for user
        """
        try:
            # Get user
            try:
                user = User.objects.first()
                if not user:
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            except Exception as e:
                logger.error(f"User creation failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get audit trail
            audit_manager = AuditTrailManager()
            # Use the correct method name
            audit_entries = audit_manager.get_audit_trail(
                user_id=user.id,
                limit=int(request.query_params.get('limit', 50)),
                action_type=request.query_params.get('action_type'),
                resource_type=request.query_params.get('resource_type')
            )
            
            formatted_entries = []
            for entry in audit_entries:
                formatted_entries.append({
                    'id': entry.id,
                    'action_type': entry.action_type,
                    'action_category': entry.action_category,
                    'resource_type': entry.resource_type,
                    'resource_name': entry.resource_name,
                    'action_description': entry.action_description,
                    'success': entry.success,
                    'created_at': entry.created_at
                })
            
            return Response({
                'success': True,
                'audit_entries': formatted_entries,
                'message': f'Found {len(formatted_entries)} audit entries'
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Audit trail error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Template Views for Frontend
from django.shortcuts import render, redirect
from django.contrib.auth import login

def dashboard_view(request):
    """Main dashboard view with three-panel layout"""
    # Require authentication - redirect to login if not authenticated
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    return render(request, 'analytics/dashboard.html')


def upload_form_view(request):
    """Upload form modal content"""
    # Require authentication - redirect to login if not authenticated
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    return render(request, 'analytics/upload_form.html')


def csrf_failure(request, reason=""):
    """Custom CSRF failure handler (T108)
    
    Provides user-friendly error messages for CSRF failures
    and logs security events for monitoring.
    """
    from analytics.middleware.audit_logging import get_security_logger
    
    # Log security event
    security_logger = get_security_logger()
    security_logger.log_suspicious_activity(request, 'csrf_failure', {
        'reason': reason,
        'path': request.path,
        'method': request.method,
        'referer': request.META.get('HTTP_REFERER', ''),
    })
    
    # Return appropriate response based on request type
    if request.content_type == 'application/json' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'CSRF verification failed',
            'message': 'CSRF token missing or incorrect. Please refresh the page and try again.',
            'code': 'csrf_failure',
            'reason': reason
        }, status=403)
    else:
        # For web requests, return HTML error page
        from django.template.response import TemplateResponse
        return TemplateResponse(request, 'analytics/csrf_failure.html', {
            'reason': reason,
            'referer': request.META.get('HTTP_REFERER', ''),
        }, status=403)


def get_csrf_token(request):
    """
    API endpoint to get CSRF token for JavaScript applications
    """
    from django.middleware.csrf import get_token
    
    return JsonResponse({
        'csrf_token': get_token(request),
        'cookie_name': 'analytical_csrftoken',
        'header_name': 'X-CSRFToken',
    })


# Dataset listing view
from django.core.paginator import Paginator
from django.db.models import Q

def list_datasets_view(request):
    """List user's datasets with pagination"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    # Get user's datasets
    datasets = Dataset.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(datasets, 10)  # Show 10 datasets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Format dataset data
    dataset_list = []
    for dataset in page_obj:
        dataset_list.append({
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'original_filename': dataset.original_filename,
            'file_size_bytes': dataset.file_size_bytes,
            'row_count': dataset.row_count,
            'column_count': dataset.column_count,
            'created_at': dataset.created_at.strftime('%Y-%m-%d %H:%M'),
            'processing_status': dataset.processing_status,
        })
    
    return JsonResponse({
        'success': True,
        'datasets': dataset_list,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
    })


def my_datasets_view(request):
    """Render the My Datasets template"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    # Get user's datasets
    datasets = Dataset.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'analytics/my_datasets.html', {'datasets': datasets})


# Custom Registration View
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
