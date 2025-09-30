"""
API Views for Analytics System
"""
import logging
import re
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods

from analytics.models import Dataset, DatasetColumn, AuditTrail, AnalysisSession, ChatSession, AnalysisSuggestion
from analytics.services.file_processing import FileProcessingService
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.session_manager import SessionManager
from analytics.services.analysis_executor import AnalysisExecutor
from analytics.services.rag_service import RAGService
from analytics.services.llm_processor import LLMProcessor
from analytics.services.agentic_ai_controller import AgenticAIController
from analytics.services.ai_interpretation_service import ai_interpretation_service
from analytics.services.chat_service import ChatService
from analytics.services.analysis_suggestion_service import AnalysisSuggestionService
from analytics.tools.tool_registry import ToolRegistry


logger = logging.getLogger(__name__)
User = get_user_model()


class UploadViewSet(viewsets.ViewSet):
    """
    File upload endpoint for dataset processing
    """
    permission_classes = [AllowAny]
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
            
            # Get user - use authenticated user if available, otherwise fallback
            try:
                if request.user.is_authenticated:
                    user = request.user
                else:
                    # Fallback for development/testing - use first user
                    user = User.objects.first()
                    if not user:
                        # Create a default user if none exists
                        user = User.objects.create(
                            username='default_user',
                            email='user@example.com'
                        )
            except Exception as e:
                logger.error(f"User retrieval failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
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

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def list_datasets(self, request):
        """
        List all datasets for the current user
        """
        try:
            # Get the authenticated user
            if request.user.is_authenticated:
                user = request.user
            else:
                # Fallback for development/testing - use first user
                user = User.objects.first()
                if not user:
                    # Create a default user if none exists
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            
            # Get all datasets for the user
            datasets = Dataset.objects.filter(user=user).order_by('-created_at')
            logger.info(f"DEBUG: Found {datasets.count()} datasets for user {user.id}")
            
            datasets_list = []
            for dataset in datasets:
                datasets_list.append({
                    'id': dataset.id,
                    'name': dataset.name,
                    'description': dataset.description or '',
                    'row_count': dataset.row_count,
                    'column_count': dataset.column_count,
                    'file_size_bytes': dataset.file_size_bytes,
                    'processing_status': dataset.processing_status,
                    'data_quality_score': dataset.data_quality_score,
                    'created_at': dataset.created_at.isoformat(),
                    'original_filename': dataset.original_filename
                })
            
            return Response({
                'success': True,
                'datasets': datasets_list,
                'count': len(datasets_list),
                'message': 'Datasets retrieved successfully'
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"List datasets error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SessionViewSet(viewsets.ViewSet):
    """
    Analysis session management
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
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
            
            # Get user - use authenticated user if available, otherwise fallback
            try:
                if request.user.is_authenticated:
                    user = request.user
                else:
                    # Fallback for development/testing - use first user
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
            
            # Store session ID in request session
            request.session['current_session_id'] = session.id
            request.session.save()
            
            logger.info(f"DEBUG: Created session {session.id} and stored in request session")
            
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
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def current(self, request):
        """
        Get current active session info
        """
        try:
            # Get user - use authenticated user if available, otherwise fallback
            try:
                if request.user.is_authenticated:
                    user = request.user
                else:
                    # Fallback for development/testing - use first user
                    user = User.objects.first()
                    if not user:
                        # Create a default user if none exists
                        user = User.objects.create(
                            username='default_user',
                            email='user@example.com'
                        )
            except Exception as e:
                logger.error(f"User retrieval failed: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'User authentication failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get current active session
            try:
                session = AnalysisSession.objects.filter(
                    user=user, 
                    is_active=True
                ).order_by('-last_accessed').first()
                
                if not session:
                    return Response({
                        'success': True,
                        'session': None,
                        'dataset': None,
                        'message': 'No active session'
                    }, status=status.HTTP_200_OK)
                
                # Get dataset info
                dataset_info = {
                    'id': session.primary_dataset.id,
                    'name': session.primary_dataset.name,
                    'description': session.primary_dataset.description or '',
                    'row_count': session.primary_dataset.row_count,
                    'column_count': session.primary_dataset.column_count,
                    'file_size_bytes': session.primary_dataset.file_size_bytes,
                    'processing_status': session.primary_dataset.processing_status,
                    'data_quality_score': session.primary_dataset.data_quality_score,
                    'created_at': session.primary_dataset.created_at.isoformat()
                }
                
                return Response({
                    'success': True,
                    'session': {
                        'id': session.id,
                        'name': session.name,
                        'description': session.description,
                        'created_at': session.created_at.isoformat(),
                        'last_accessed': session.last_accessed.isoformat()
                    },
                    'dataset': dataset_info,
                    'message': 'Current session retrieved successfully'
                }, status=status.HTTP_200_OK)
                
            except AnalysisSession.DoesNotExist:
                return Response({
                    'success': True,
                    'session': None,
                    'dataset': None,
                    'message': 'No active session'
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Current session error: {str(e)}", exc_info=True)
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
        Format message content with professional styling including table detection
        """
        # First, detect and format tables
        content = self._format_tables(content)
        
        # Convert markdown-style formatting to HTML
        # Bold text
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        # Italic text
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        # Code blocks
        content = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)
        # Inline code
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        # Line breaks (but not for table content)
        if not self._contains_table(content):
            content = content.replace('\n', '<br>')
        
        return content
    
    def _contains_table(self, content):
        """
        Check if content contains a table
        """
        lines = content.split('\n')
        table_lines = [line for line in lines if '|' in line and len(line.strip()) > 5]
        return len(table_lines) >= 2
    
    def _format_tables(self, content):
        """
        Format markdown tables to HTML
        """
        # Split content into lines
        lines = content.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a table
            if '|' in line and len(line.strip()) > 5:
                # Collect table lines
                table_lines = []
                j = i
                while j < len(lines) and '|' in lines[j] and len(lines[j].strip()) > 5:
                    table_lines.append(lines[j])
                    j += 1
                
                # If we have at least 2 table lines, format as table
                if len(table_lines) >= 2:
                    table_html = self._create_table_html(table_lines)
                    result_lines.append(table_html)
                    i = j  # Skip the table lines
                else:
                    result_lines.append(line)
                    i += 1
            else:
                result_lines.append(line)
                i += 1
        
        return '\n'.join(result_lines)
    
    def _create_table_html(self, table_lines):
        """
        Create HTML table from markdown table lines
        """
        # Filter out separator lines (like |---|---|---|)
        data_lines = []
        for line in table_lines:
            if not re.match(r'^\s*\|[\s\-\|:]+\|\s*$', line):
                data_lines.append(line)
        
        if len(data_lines) < 2:
            return '\n'.join(table_lines)  # Return original if not enough data
        
        # Extract headers from first line
        headers = [cell.strip() for cell in data_lines[0].split('|') if cell.strip()]
        
        # Extract data rows
        rows = []
        for i in range(1, len(data_lines)):
            cells = [cell.strip() for cell in data_lines[i].split('|') if cell.strip()]
            if len(cells) >= 2:  # At least 2 columns
                rows.append(cells)
        
        if not headers or not rows:
            return '\n'.join(table_lines)  # Return original if no valid data
        
        # Create HTML table
        table_id = f'table_{hash(str(table_lines)) % 10000}'
        
        html = f'''
        <div class="table-container">
            <div class="table-header">
                <div class="table-title">
                    <h6><i class="bi bi-table"></i> Data Table</h6>
                    <span class="table-meta">{len(rows)} rows × {len(headers)} columns</span>
                </div>
                <div class="table-actions">
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-secondary" onclick="exportTable(this, 'csv')">
                            <i class="bi bi-file-earmark-spreadsheet"></i> CSV
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="exportTable(this, 'json')">
                            <i class="bi bi-file-earmark-code"></i> JSON
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="fullscreenTable(this)">
                            <i class="bi bi-arrows-fullscreen"></i> Fullscreen
                        </button>
                    </div>
                </div>
            </div>
            <div class="table-content">
                <div class="table-responsive">
                    <table class="table table-striped table-hover table-sm">
                        <thead class="table-dark">
                            <tr>
        '''
        
        for header in headers:
            html += f'<th scope="col">{header}</th>'
        
        html += '''
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for row in rows:
            html += '<tr>'
            for cell in row:
                html += f'<td>{cell}</td>'
            html += '</tr>'
        
        html += '''
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="table-footer">
                <div class="pagination-info">
                    Showing 1 to ''' + str(len(rows)) + ''' of ''' + str(len(rows)) + ''' entries
                </div>
            </div>
        </div>
        '''
        
        return html
    
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
            
            # Get selected AI model (default to ollama)
            selected_model = request.data.get('ai_model', 'ollama')
            
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
            
            # Process message with selected model
            llm_processor = LLMProcessor(model_name=selected_model)
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


class EnhancedChatViewSet(viewsets.ViewSet):
    """
    Enhanced Chat endpoints with analysis suggestions and context management
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_service = ChatService()
        self.suggestion_service = AnalysisSuggestionService()
    
    def _format_message_content(self, content):
        """
        Format message content with professional styling including table detection
        """
        # First, detect and format tables
        content = self._format_tables(content)
        
        # Convert markdown-style formatting to HTML
        # Bold text
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        # Italic text
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        # Code blocks
        content = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)
        # Inline code
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        # Line breaks (but not for table content)
        if not self._contains_table(content):
            content = content.replace('\n', '<br>')
        
        return content
    
    def _contains_table(self, content):
        """
        Check if content contains a table
        """
        lines = content.split('\n')
        table_lines = [line for line in lines if '|' in line and len(line.strip()) > 5]
        return len(table_lines) >= 2
    
    def _format_tables(self, content):
        """
        Format markdown tables to HTML
        """
        # Split content into lines
        lines = content.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a table
            if '|' in line and len(line.strip()) > 5:
                # Collect table lines
                table_lines = []
                j = i
                while j < len(lines) and '|' in lines[j] and len(lines[j].strip()) > 5:
                    table_lines.append(lines[j])
                    j += 1
                
                # If we have at least 2 table lines, format as table
                if len(table_lines) >= 2:
                    table_html = self._create_table_html(table_lines)
                    result_lines.append(table_html)
                    i = j  # Skip the table lines
                else:
                    result_lines.append(line)
                    i += 1
            else:
                result_lines.append(line)
                i += 1
        
        return '\n'.join(result_lines)
    
    def _create_table_html(self, table_lines):
        """
        Create HTML table from markdown table lines
        """
        # Filter out separator lines (like |---|---|---|)
        data_lines = []
        for line in table_lines:
            if not re.match(r'^\s*\|[\s\-\|:]+\|\s*$', line):
                data_lines.append(line)
        
        if len(data_lines) < 2:
            return '\n'.join(table_lines)  # Return original if not enough data
        
        # Extract headers from first line
        headers = [cell.strip() for cell in data_lines[0].split('|') if cell.strip()]
        
        # Extract data rows
        rows = []
        for i in range(1, len(data_lines)):
            cells = [cell.strip() for cell in data_lines[i].split('|') if cell.strip()]
            if len(cells) >= 2:  # At least 2 columns
                rows.append(cells)
        
        if not headers or not rows:
            return '\n'.join(table_lines)  # Return original if no valid data
        
        # Create HTML table
        table_id = f'table_{hash(str(table_lines)) % 10000}'
        
        html = f'''
        <div class="table-container">
            <div class="table-header">
                <div class="table-title">
                    <h6><i class="bi bi-table"></i> Data Table</h6>
                    <span class="table-meta">{len(rows)} rows × {len(headers)} columns</span>
                </div>
                <div class="table-actions">
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-secondary" onclick="exportTable(this, 'csv')">
                            <i class="bi bi-file-earmark-spreadsheet"></i> CSV
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="exportTable(this, 'json')">
                            <i class="bi bi-file-earmark-code"></i> JSON
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="fullscreenTable(this)">
                            <i class="bi bi-arrows-fullscreen"></i> Fullscreen
                        </button>
                    </div>
                </div>
            </div>
            <div class="table-content">
                <div class="table-responsive">
                    <table class="table table-striped table-hover table-sm">
                        <thead class="table-dark">
                            <tr>
        '''
        
        for header in headers:
            html += f'<th scope="col">{header}</th>'
        
        html += '''
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for row in rows:
            html += '<tr>'
            for cell in row:
                html += f'<td>{cell}</td>'
            html += '</tr>'
        
        html += '''
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="table-footer">
                <div class="pagination-info">
                    Showing 1 to ''' + str(len(rows)) + ''' of ''' + str(len(rows)) + ''' entries
                </div>
            </div>
        </div>
        '''
        
        return html
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """
        Send chat message and get AI response with analysis suggestions
        """
        try:
            # Get the authenticated user
            if request.user.is_authenticated:
                user = request.user
            else:
                # Fallback for development/testing - use first user
                user = User.objects.first()
                if not user:
                    user = User.objects.create(
                        username='default_user',
                        email='user@example.com'
                    )
            
            # Validate request data
            message = request.data.get('message', '').strip()
            if not message:
                return Response({
                    'success': False,
                    'error': 'Message is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(message) > 4000:
                return Response({
                    'success': False,
                    'error': 'Message too long (max 4000 characters)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get selected AI model (default to ollama)
            selected_model = request.data.get('ai_model', 'ollama')
            
            # Process message with selected model
            llm_processor = LLMProcessor(model_name=selected_model)
            result = llm_processor.process_message(
                user=user,
                message=message,
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
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get chat history for current session
        """
        try:
            # Get the authenticated user
            if request.user.is_authenticated:
                user = request.user
            else:
                user = User.objects.first()
                if not user:
                    return Response({
                        'success': False,
                        'error': 'User authentication required'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get query parameters
            session_id = request.GET.get('session_id')
            limit = min(int(request.GET.get('limit', 50)), 100)
            offset = int(request.GET.get('offset', 0))
            
            result = self.chat_service.get_chat_history(
                user=user,
                session_id=session_id,
                limit=limit,
                offset=offset
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Chat history error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to get chat history',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def execute_suggestion(self, request):
        """
        Execute an analysis suggestion
        """
        try:
            # Get the authenticated user
            if request.user.is_authenticated:
                user = request.user
            else:
                user = User.objects.first()
                if not user:
                    return Response({
                        'success': False,
                        'error': 'User authentication required'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Validate request data
            suggestion_id = request.data.get('suggestion_id')
            if not suggestion_id:
                return Response({
                    'success': False,
                    'error': 'Suggestion ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Execute suggestion
            parameters = request.data.get('parameters')
            result = self.suggestion_service.execute_suggestion(
                suggestion_id=suggestion_id,
                user=user,
                parameters=parameters
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Suggestion execution error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to execute suggestion',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def context(self, request):
        """
        Get current chat context including dataset and session info
        """
        try:
            # Get the authenticated user
            if request.user.is_authenticated:
                user = request.user
            else:
                user = User.objects.first()
                if not user:
                    return Response({
                        'success': False,
                        'error': 'User authentication required'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get context
            session_id = request.GET.get('session_id')
            result = self.chat_service.get_chat_context(
                user=user,
                session_id=session_id
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Chat context error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to get chat context',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['put'])
    def update_session(self, request):
        """
        Update chat session context or state
        """
        try:
            # Get the authenticated user
            if request.user.is_authenticated:
                user = request.user
            else:
                user = User.objects.first()
                if not user:
                    return Response({
                        'success': False,
                        'error': 'User authentication required'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Validate request data
            session_id = request.data.get('session_id')
            if not session_id:
                return Response({
                    'success': False,
                    'error': 'Session ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update session
            context_summary = request.data.get('context_summary', '').strip()
            is_active = request.data.get('is_active')
            
            try:
                chat_session = ChatSession.objects.get(
                    id=session_id,
                    user=user
                )
                
                if context_summary:
                    if len(context_summary) > 1000:
                        return Response({
                            'success': False,
                            'error': 'Context summary too long (max 1000 characters)'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    chat_session.context_summary = context_summary
                
                if is_active is not None:
                    chat_session.is_active = bool(is_active)
                
                chat_session.save()
                
                return Response({
                    'success': True,
                    'session': {
                        'id': chat_session.id,
                        'user_id': chat_session.user.id,
                        'analysis_session_id': chat_session.analysis_session.id,
                        'is_active': chat_session.is_active,
                        'context_summary': chat_session.context_summary,
                        'last_activity': chat_session.last_activity.isoformat(),
                        'created_at': chat_session.created_at.isoformat(),
                        'updated_at': chat_session.updated_at.isoformat()
                    }
                })
                
            except ChatSession.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Chat session not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Chat session update error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to update chat session',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def sandbox_executions(self, request):
        """
        Get sandbox execution history for the authenticated user
        """
        try:
            user = request.user
            if not user.is_authenticated:
                return Response({
                    'success': False,
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get pagination parameters
            limit = int(request.GET.get('limit', 20))
            offset = int(request.GET.get('offset', 0))
            
            # Get sandbox executions
            result = self.suggestion_service.get_user_sandbox_executions(
                user=user,
                limit=limit,
                offset=offset
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Enhanced chat sandbox executions error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to get sandbox executions',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HealthViewSet(viewsets.ViewSet):
    """
    Health check endpoints
    """
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """
        Simple health check endpoint
        """
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'analytics'
        })


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


# Simple API endpoints for dataset switching
@csrf_exempt
@require_http_methods(["GET"])
def api_current_session(request):
    """Get current active session info"""
    try:
        # Get the authenticated user
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback for development/testing - use first user
            user = User.objects.first()
            if not user:
                # Create a default user if none exists
                user = User.objects.create(
                    username='default_user',
                    email='user@example.com'
                )
        
        # Get current active session
        session = AnalysisSession.objects.filter(
            user=user, 
            is_active=True
        ).order_by('-last_accessed').first()
        
        if not session:
            return JsonResponse({
                'success': True,
                'session': None,
                'dataset': None,
                'message': 'No active session'
            })
        
        # Get dataset info
        dataset_info = {
            'id': session.primary_dataset.id,
            'name': session.primary_dataset.name,
            'description': session.primary_dataset.description or '',
            'row_count': session.primary_dataset.row_count,
            'column_count': session.primary_dataset.column_count,
            'file_size_bytes': session.primary_dataset.file_size_bytes,
            'processing_status': session.primary_dataset.processing_status,
            'data_quality_score': session.primary_dataset.data_quality_score,
            'created_at': session.primary_dataset.created_at.isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'session': {
                'id': session.id,
                'name': session.name,
                'description': session.description,
                'created_at': session.created_at.isoformat(),
                'last_accessed': session.last_accessed.isoformat()
            },
            'dataset': dataset_info,
            'message': 'Current session retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Current session error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_datasets_list(request):
    """List all datasets for the current user"""
    try:
        # Get the authenticated user
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback for development/testing - use first user
            user = User.objects.first()
            if not user:
                # Create a default user if none exists
                user = User.objects.create(
                    username='default_user',
                    email='user@example.com'
                )
        
        # Get all datasets for the user
        datasets = Dataset.objects.filter(user=user).order_by('-created_at')
        logger.info(f"DEBUG: Found {datasets.count()} datasets for user {user.id}")
        
        datasets_list = []
        for dataset in datasets:
            datasets_list.append({
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description or '',
                'row_count': dataset.row_count,
                'column_count': dataset.column_count,
                'file_size_bytes': dataset.file_size_bytes,
                'processing_status': dataset.processing_status,
                'data_quality_score': dataset.data_quality_score,
                'created_at': dataset.created_at.isoformat(),
                'original_filename': dataset.original_filename
            })
        
        return JsonResponse({
            'success': True,
            'datasets': datasets_list,
            'count': len(datasets_list),
            'message': 'Datasets retrieved successfully'
        })
            
    except Exception as e:
        logger.error(f"List datasets error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_current_session(request):
    """Update current session ID"""
    try:
        import json
        data = json.loads(request.body)
        
        session_id = data.get('session_id')
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'Session ID is required'
            }, status=400)
        
        # Update session ID in request session
        request.session['current_session_id'] = session_id
        request.session.save()
        
        logger.info(f"DEBUG: Updated current session ID to: {session_id}")
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'message': 'Current session updated successfully'
        })
            
    except Exception as e:
        logger.error(f"Update current session error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_create_session(request):
    """Create new analysis session"""
    try:
        import json
        data = json.loads(request.body)
        
        # Validate request
        dataset_id = data.get('dataset_id')
        if not dataset_id:
            return JsonResponse({
                'success': False,
                'error': 'Dataset ID is required'
            }, status=400)
        
        # Get user - use authenticated user if available, otherwise fallback
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback for development/testing - use first user
            user = User.objects.first()
            if not user:
                user = User.objects.create(
                    username='default_user',
                    email='user@example.com'
                )
        
        # Get dataset
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Dataset not found'
            }, status=404)
        
        # Create session
        session_manager = SessionManager()
        session = session_manager.create_session(
            user=user,
            dataset=dataset,
            session_name=data.get('session_name', f'Session {timezone.now().strftime("%Y-%m-%d %H:%M")}')
        )
        
        # Store session ID in request session
        request.session['current_session_id'] = session.id
        request.session.save()
        
        logger.info(f"DEBUG: Created session {session.id} and stored in request session")
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'message': 'Analysis session created successfully'
        })
            
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def interpret_analysis(request):
    """
    AI interpretation endpoint for analysis results
    """
    try:
        data = request.data
        analysis_type = data.get('type', 'text')
        analysis_data = {
            'title': data.get('title', 'Untitled Analysis'),
            'content': data.get('content', ''),
            'timestamp': data.get('timestamp', '')
        }
        
        # Get AI interpretation
        from analytics.services.ai_interpretation_service import ai_interpretation_service
        result = ai_interpretation_service.interpret_analysis_result(
            analysis_data, analysis_type
        )
        
        if result['success']:
            return Response({
                'success': True,
                'interpretation': result['interpretation'],
                'confidence': result.get('confidence', 0.8),
                'analysis_type': analysis_type
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Failed to generate interpretation')
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in interpret_analysis: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_analysis_tools(request):
    """
    List all available analysis tools organized by category
    """
    try:
        from analytics.services.tool_registry import tool_registry
        logger.info("DEBUG: Loading analysis tools")
        logger.info(f"DEBUG: Tool registry initialized: {tool_registry is not None}")
        logger.info(f"DEBUG: Tool registry tools count: {len(tool_registry.tools)}")
        logger.info(f"DEBUG: Tool registry categories: {list(tool_registry.categories.keys())}")
        
        tools = tool_registry.get_tool_categories()
        logger.info(f"DEBUG: Found {len(tools)} tool categories")
        
        for category, tool_list in tools.items():
            logger.info(f"DEBUG: Category {category}: {len(tool_list)} tools")
            for tool in tool_list:
                logger.info(f"DEBUG: Tool {tool['id']}: {tool['name']}")
        
        return Response({
            'success': True,
            'tools': tools
        })
        
    except Exception as e:
        logger.error(f"DEBUG: Error listing analysis tools: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to load analysis tools'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_tool_configuration(request, tool_id):
    """
    Get configuration details for a specific tool with dataset column information
    """
    try:
        from analytics.services.tool_registry import tool_registry
        from analytics.models import AnalysisSession
        
        logger.info(f"DEBUG: Getting tool configuration for tool_id: {tool_id}")
        logger.info(f"DEBUG: User: {request.user}")
        logger.info(f"DEBUG: Session keys: {list(request.session.keys())}")
        logger.info(f"DEBUG: Tool registry initialized: {tool_registry is not None}")
        logger.info(f"DEBUG: Tool registry tools count: {len(tool_registry.tools)}")
        logger.info(f"DEBUG: Available tool IDs: {list(tool_registry.tools.keys())}")
        
        tool = tool_registry.get_tool(tool_id)
        logger.info(f"DEBUG: Tool found: {tool is not None}")
        if tool:
            logger.info(f"DEBUG: Tool name: {tool.name}")
            logger.info(f"DEBUG: Tool parameters count: {len(tool.parameters)}")
            for i, param in enumerate(tool.parameters):
                logger.info(f"DEBUG: Parameter {i}: {param.name} ({param.type})")
        else:
            logger.error(f"DEBUG: Tool not found for ID: {tool_id}")
            logger.info(f"DEBUG: Available tools: {list(tool_registry.tools.keys())}")
        
        if not tool:
            return Response({
                'success': False,
                'error': 'Tool not found'
            }, status=404)
        
        # Get the authenticated user
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback for development/testing - use first user
            user = User.objects.first()
            if not user:
                user = User.objects.create(
                    username='default_user',
                    email='user@example.com'
                )
        
        # Get current session and dataset information
        session_id = request.session.get('current_session_id')
        logger.info(f"DEBUG: Session ID from request: {session_id}")
        logger.info(f"DEBUG: All session data: {dict(request.session)}")
        
        dataset_info = None
        columns_info = []
        
        # Try to get session by ID first, then fall back to latest session for user
        session = None
        if session_id:
            try:
                print(f"DEBUG: Looking for session with ID: {session_id}")
                logger.info(f"DEBUG: Looking for session with ID: {session_id}")
                session = AnalysisSession.objects.get(id=session_id, user=user)
                print(f"DEBUG: Session found by ID: {session}")
                logger.info(f"DEBUG: Session found by ID: {session}")
            except AnalysisSession.DoesNotExist:
                print(f"DEBUG: Session {session_id} not found for user {user}, trying latest session")
                logger.warning(f"DEBUG: Session {session_id} not found for user {user}, trying latest session")
                session = None
        
        # If no session found by ID, get the latest session for the user
        if not session:
            try:
                session = AnalysisSession.objects.filter(user=user).order_by('-created_at').first()
                print(f"DEBUG: Latest session for user: {session}")
                logger.info(f"DEBUG: Latest session for user: {session}")
                if session:
                    # Update the session ID in request session
                    request.session['current_session_id'] = session.id
                    request.session.save()
                    print(f"DEBUG: Updated session ID in request session to: {session.id}")
                    logger.info(f"DEBUG: Updated session ID in request session to: {session.id}")
            except Exception as e:
                print(f"DEBUG: Error getting latest session: {str(e)}")
                logger.error(f"DEBUG: Error getting latest session: {str(e)}")
        
        if session:
            try:
                print(f"DEBUG: Session found: {session}")
                logger.info(f"DEBUG: Session found: {session}")
                print(f"DEBUG: Session primary_dataset: {session.primary_dataset}")
                logger.info(f"DEBUG: Session primary_dataset: {session.primary_dataset}")
                
                dataset = session.get_dataset()
                print(f"DEBUG: Dataset loaded: {dataset is not None}")
                logger.info(f"DEBUG: Dataset loaded: {dataset is not None}")
                if dataset is not None:
                    print(f"DEBUG: Dataset shape: {dataset.shape}")
                    logger.info(f"DEBUG: Dataset shape: {dataset.shape}")
                    print(f"DEBUG: Dataset columns: {list(dataset.columns)}")
                    logger.info(f"DEBUG: Dataset columns: {list(dataset.columns)}")
                    print(f"DEBUG: Dataset empty: {dataset.empty}")
                    logger.info(f"DEBUG: Dataset empty: {dataset.empty}")
                    print(f"DEBUG: Dataset dtypes: {dataset.dtypes.to_dict()}")
                    logger.info(f"DEBUG: Dataset dtypes: {dataset.dtypes.to_dict()}")
                else:
                    print("DEBUG: Dataset is None")
                    logger.warning("DEBUG: Dataset is None")
                
                if dataset is not None and not dataset.empty:
                    print("DEBUG: Processing dataset columns")
                    # Get column information with types
                    columns_info = []
                    for column in dataset.columns:
                        col_type = 'numeric' if dataset[column].dtype in ['int64', 'float64', 'int32', 'float32'] else \
                                  'datetime' if dataset[column].dtype.name.startswith('datetime') else \
                                  'categorical'
                        
                        sample_values = dataset[column].dropna().head(3).tolist() if not dataset[column].dropna().empty else []
                        
                        column_info = {
                            'name': column,
                            'type': col_type,
                            'dtype': str(dataset[column].dtype),
                            'sample_values': sample_values
                        }
                        columns_info.append(column_info)
                        print(f"DEBUG: Column {column}: {column_info}")
                        logger.info(f"DEBUG: Column {column}: {column_info}")
                        print(f"DEBUG: Column {column} dtype: {dataset[column].dtype}, type: {col_type}")
                        logger.info(f"DEBUG: Column {column} dtype: {dataset[column].dtype}, type: {col_type}")
                    
                    dataset_info = {
                        'name': session.primary_dataset.name if session.primary_dataset else 'Current Dataset',
                        'rows': len(dataset),
                        'columns': len(dataset.columns),
                        'columns_info': columns_info
                    }
                    print(f"DEBUG: Dataset info: {dataset_info}")
                    logger.info(f"DEBUG: Dataset info: {dataset_info}")
                else:
                    print("DEBUG: Dataset is None or empty")
                    logger.warning("DEBUG: Dataset is None or empty")
            except Exception as e:
                print(f"DEBUG: Error getting session/dataset: {str(e)}")
                logger.error(f"DEBUG: Error getting session/dataset: {str(e)}")
        else:
            print("DEBUG: No session found for user")
            logger.warning("DEBUG: No session found for user")
        
        # Enhance parameters with column information
        enhanced_parameters = []
        for param in tool.parameters:
            param_info = {
                'name': param.name,
                'type': param.type.value,
                'label': param.label,
                'description': param.description,
                'required': param.required,
                'default_value': param.default_value,
                'options': param.options,
                'min_value': param.min_value,
                'max_value': param.max_value
            }
            
            # Add column options for column-type parameters
            if param.type.value in ['column', 'multicolumn']:
                logger.info(f"DEBUG: Adding column options for parameter {param.name}")
                
                # Filter columns based on tool requirements
                filtered_columns = [
                    col for col in columns_info 
                    if not tool.required_column_types or col['type'] in tool.required_column_types
                ]
                
                # Use filtered columns for the parameter options
                param_info['column_options'] = filtered_columns
                param_info['filtered_columns'] = filtered_columns
                
                logger.info(f"DEBUG: Column options added: {len(param_info['column_options'])} columns")
                logger.info(f"DEBUG: Filtered columns: {len(param_info['filtered_columns'])} columns")
                logger.info(f"DEBUG: Tool required column types: {tool.required_column_types}")
                logger.info(f"DEBUG: Available column types: {[col['type'] for col in columns_info]}")
            
            enhanced_parameters.append(param_info)
        
        response_data = {
            'success': True,
            'tool': {
                'id': tool.id,
                'name': tool.name,
                'description': tool.description,
                'category': tool.category.value,
                'parameters': enhanced_parameters,
                'result_type': tool.result_type,
                'icon': tool.icon,
                'tags': tool.tags or []
            },
            'dataset_info': dataset_info,
            'session_id': session.id if session else None
        }
        
        print(f"DEBUG: Final response data: {response_data}")
        logger.info(f"DEBUG: Final response data: {response_data}")
        print(f"DEBUG: Enhanced parameters count: {len(enhanced_parameters)}")
        logger.info(f"DEBUG: Enhanced parameters count: {len(enhanced_parameters)}")
        for i, param in enumerate(enhanced_parameters):
            print(f"DEBUG: Enhanced parameter {i}: {param['name']} - column_options: {param.get('column_options', 'None')}")
            logger.info(f"DEBUG: Enhanced parameter {i}: {param['name']} - column_options: {param.get('column_options', 'None')}")
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting tool configuration: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to load tool configuration'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def execute_analysis_tool(request):
    """
    Execute an analysis tool with given parameters
    """
    try:
        data = request.data
        tool_id = data.get('tool_id')
        parameters = data.get('parameters', {})
        
        if not tool_id:
            return Response({
                'success': False,
                'error': 'Tool ID is required'
            }, status=400)
        
        # Get the authenticated user
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback for development/testing - use first user
            user = User.objects.first()
            if not user:
                user = User.objects.create(
                    username='default_user',
                    email='user@example.com'
                )
        
        # Get current session and dataset
        session_id = request.session.get('current_session_id')
        if not session_id:
            return Response({
                'success': False,
                'error': 'No active analysis session'
            }, status=400)
        
        logger.info(f"DEBUG: Executing tool with session_id: {session_id}")
        
        # Get dataset
        from analytics.models import AnalysisSession
        try:
            logger.info(f"DEBUG: Looking for session {session_id} for user {user.id}")
            session = AnalysisSession.objects.get(id=session_id, user=user)
            logger.info(f"DEBUG: Found session: {session}")
            dataset = session.get_dataset()
            logger.info(f"DEBUG: Dataset loaded: {dataset is not None}")
        except AnalysisSession.DoesNotExist:
            logger.error(f"DEBUG: Session {session_id} not found for user {user.id}")
            # Try to find any session for this user
            user_sessions = AnalysisSession.objects.filter(user=user)
            logger.info(f"DEBUG: User has {user_sessions.count()} sessions: {list(user_sessions.values_list('id', flat=True))}")
            return Response({
                'success': False,
                'error': 'Analysis session not found'
            }, status=404)
        
        if dataset is None or dataset.empty:
            return Response({
                'success': False,
                'error': 'No dataset available for analysis'
            }, status=400)
        
        # Execute tool
        from analytics.services.tool_executor import tool_executor
        execution_result = tool_executor.execute_tool(tool_id, parameters, dataset, session_id)
        
        if execution_result.success:
            # Generate analysis result template
            from analytics.services.analysis_result_manager import analysis_result_manager
            from analytics.models import AnalysisResult
            analysis_id = f"analysis_{execution_result.execution_id}"
            
            # Extract the specific parameters we need and remove them from the data
            result_data = execution_result.result_data.copy()
            result_type = result_data.pop('type', 'text')
            title = result_data.pop('title', 'Analysis Result')
            description = result_data.pop('description', '')
            
            result_html = analysis_result_manager.create_analysis_result(
                result_type=result_type,
                analysis_id=analysis_id,
                title=title,
                description=description,
                **result_data
            )
            
            # Save analysis result to database
            try:
                logger.info(f"DEBUG: Attempting to save analysis result for tool_id: {tool_id}")
                
                # Get the tool from registry (tool_id is actually the tool name)
                from analytics.services.tool_registry import tool_registry
                tool_info = tool_registry.get_tool(tool_id)
                
                if not tool_info:
                    logger.error(f"Tool {tool_id} not found in registry")
                    # Continue without saving to database
                else:
                    logger.info(f"DEBUG: Found tool info: {tool_info.name}")
                    # Try to get or create the AnalysisTool in database
                    from analytics.models import AnalysisTool
                    logger.info(f"DEBUG: Creating/updating AnalysisTool for {tool_id}")
                    
                    tool, created = AnalysisTool.objects.get_or_create(
                        name=tool_id,
                        defaults={
                            'display_name': tool_info.name,
                            'description': tool_info.description,
                            'category': 'statistical',  # Default category
                            'langchain_tool_name': tool_id,
                            'tool_class': 'analytics.services.tool_executor',
                            'tool_function': tool_info.execution_function,
                            'is_active': True,
                            'is_premium': False,
                            'parameters_schema': {},
                            'required_parameters': [],
                            'optional_parameters': [],
                            'required_column_types': tool_info.required_column_types or [],
                            'min_columns': tool_info.min_columns or 1,
                            'max_columns': tool_info.max_columns,
                            'min_rows': 1,
                            'execution_timeout': 300,
                            'memory_limit_mb': 512,
                            'output_types': [tool_info.result_type],
                            'generates_images': tool_info.result_type == 'chart',
                            'generates_tables': tool_info.result_type == 'table',
                            'generates_text': tool_info.result_type == 'text',
                            'version': '1.0.0',
                            'tags': tool_info.tags or []
                        }
                    )
                    logger.info(f"DEBUG: AnalysisTool {'created' if created else 'found'}: {tool.id}")
                    
                    # Get the dataset from session
                    dataset = session.primary_dataset
                    logger.info(f"DEBUG: Dataset: {dataset}")
                    
                    # Generate cache key
                    import hashlib
                    cache_key = hashlib.md5(f"{tool_id}_{session_id}_{str(parameters)}".encode()).hexdigest()
                    logger.info(f"DEBUG: Cache key: {cache_key}")
                    
                    logger.info(f"DEBUG: Creating AnalysisResult with:")
                    logger.info(f"  - name: {title}")
                    logger.info(f"  - tool_used: {tool.id}")
                    logger.info(f"  - session: {session.id}")
                    logger.info(f"  - dataset: {dataset.id}")
                    logger.info(f"  - user: {user.id}")
                    
                    analysis_result = AnalysisResult.objects.create(
                        name=title,
                        description=description,
                        tool_used=tool,
                        session=session,
                        dataset=dataset,
                        result_data=execution_result.result_data,
                        parameters_used=parameters,
                        output_type=result_type,
                        cache_key=cache_key,
                        confidence_score=0.8,  # Default confidence
                        quality_score=0.8,    # Default quality
                        user=user
                    )
                    logger.info(f"DEBUG: Successfully saved analysis result {analysis_result.id} to database")
            except Exception as e:
                logger.error(f"Failed to save analysis result to database: {str(e)}")
                logger.error(f"Error details: {str(e)}", exc_info=True)
                # Continue even if database save fails
            
            return Response({
                'success': True,
                'execution_id': execution_result.execution_id,
                'result': {
                    'analysis_id': analysis_id,
                    'type': execution_result.result_data.get('type', 'text'),
                    'title': execution_result.result_data.get('title', 'Analysis Result'),
                    'description': execution_result.result_data.get('description', ''),
                    'html': result_html
                }
            })
        else:
            return Response({
                'success': False,
                'error': execution_result.error_message
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error executing analysis tool: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to execute analysis tool'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def interpret_analysis_result(request):
    """
    AI interpretation endpoint for analysis results
    """
    try:
        data = request.data
        analysis_result_id = data.get('analysis_result_id')
        analysis_data = data.get('analysis_data', {})
        analysis_type = data.get('analysis_type', 'text')
        context = data.get('context', {})
        
        if not analysis_data and not analysis_result_id:
            return Response({
                'success': False,
                'error': 'Analysis data or analysis result ID is required'
            }, status=400)
        
        # Get the authenticated user
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback for development/testing - use first user
            user = User.objects.first()
            if not user:
                user = User.objects.create(
                    username='default_user',
                    email='user@example.com'
                )
        
        # Get session ID from request
        session_id = request.session.get('current_session_id')
        
        # Generate AI interpretation
        from analytics.services.ai_interpretation_service import ai_interpretation_service
        interpretation_result = ai_interpretation_service.interpret_analysis_result(
            analysis_data=analysis_data,
            analysis_type=analysis_type,
            context=context,
            user=user,
            analysis_result_id=analysis_result_id,
            session_id=session_id
        )
        
        if interpretation_result['success']:
            return Response({
                'success': True,
                'interpretation': interpretation_result['interpretation'],
                'confidence': interpretation_result.get('confidence', 0.5),
                'analysis_type': analysis_type,
                'is_fallback': interpretation_result.get('is_fallback', False)
            })
        else:
            return Response({
                'success': False,
                'error': interpretation_result.get('error', 'Failed to generate interpretation')
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in AI interpretation: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to generate AI interpretation'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_analysis_history(request, session_id):
    """
    Get analysis history for a session including AI interpretations
    Enhanced to filter by authenticated user and provide dataset-specific results
    """
    try:
        from analytics.models import AnalysisResult, AIInterpretation, AnalysisSession
        from analytics.services.ai_interpretation_service import ai_interpretation_service
        
        # Get the authenticated user
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback for development/testing - use first user
            user = User.objects.first()
            if not user:
                user = User.objects.create(
                    username='default_user',
                    email='user@example.com'
                )
        
        # Verify the session belongs to the user
        try:
            session = AnalysisSession.objects.get(id=session_id, user=user)
        except AnalysisSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Session not found or access denied'
            }, status=404)
        
        # Get analysis results for the session
        analysis_results = AnalysisResult.objects.filter(
            session_id=session_id,
            user=user
        ).order_by('-created_at')[:50]
        
        logger.info(f"DEBUG: Found {analysis_results.count()} analysis results for session {session_id} (user: {user.username})")
        
        # Get AI interpretations for the session
        interpretations = AIInterpretation.objects.filter(
            session_id=session_id,
            user=user
        ).order_by('-created_at')[:100]
        
        # Format analysis results with interpretations and dataset info
        history = []
        for result in analysis_results:
            result_data = {
                'id': result.id,
                'name': result.name,
                'description': result.description,
                'result_type': result.output_type,
                'tool_name': result.tool_used.name if result.tool_used else 'Unknown Tool',
                'tool_display_name': result.tool_used.display_name if result.tool_used else 'Unknown Tool',
                'dataset_name': result.dataset.name,
                'dataset_id': result.dataset.id,
                'execution_time_ms': result.execution_time_ms,
                'status': 'completed',  # Default status
                'created_at': result.created_at.isoformat(),
                'parameters': result.parameters_used,
                'result_data': result.result_data,
                'confidence_score': result.confidence_score,
                'quality_score': result.quality_score,
                'ai_interpretations': [
                    {
                        'id': interp.id,
                        'title': interp.title,
                        'content': interp.content,
                        'analysis_type': interp.analysis_type,
                        'confidence_score': interp.confidence_score,
                        'is_fallback': interp.is_fallback,
                        'created_at': interp.created_at.isoformat()
                    }
                    for interp in interpretations 
                    if interp.analysis_result_id == result.id
                ]
            }
            history.append(result_data)
        
        # Get session info
        session_info = {
            'id': session.id,
            'name': session.name,
            'description': session.description,
            'dataset_name': session.primary_dataset.name,
            'dataset_id': session.primary_dataset.id,
            'analysis_count': session.analysis_count,
            'last_analysis_at': session.last_analysis_at.isoformat() if session.last_analysis_at else None,
            'created_at': session.created_at.isoformat(),
            'last_accessed': session.last_accessed.isoformat()
        }
        
        return Response({
            'success': True,
            'session_info': session_info,
            'history': history,
            'total_count': len(history),
            'interpretations_count': len(interpretations),
            'message': f'Found {len(history)} analysis results for session {session_id}'
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve analysis history'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_dataset_analysis_history(request, dataset_id):
    """
    Get analysis history for a specific dataset across all sessions for the authenticated user
    """
    try:
        from analytics.models import AnalysisResult, AIInterpretation, Dataset
        
        # Get the authenticated user
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback for development/testing - use first user
            user = User.objects.first()
            if not user:
                user = User.objects.create(
                    username='default_user',
                    email='user@example.com'
                )
        
        # Verify the dataset belongs to the user
        try:
            dataset = Dataset.objects.get(id=dataset_id, user=user)
        except Dataset.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Dataset not found or access denied'
            }, status=404)
        
        # Get analysis results for the dataset across all sessions
        analysis_results = AnalysisResult.objects.filter(
            dataset_id=dataset_id,
            user=user
        ).order_by('-created_at')[:100]
        
        logger.info(f"DEBUG: Found {analysis_results.count()} analysis results for dataset {dataset_id} (user: {user.username})")
        
        # Get AI interpretations for the dataset
        interpretations = AIInterpretation.objects.filter(
            analysis_result__dataset_id=dataset_id,
            user=user
        ).order_by('-created_at')[:200]
        
        # Format analysis results with interpretations and session info
        history = []
        for result in analysis_results:
            result_data = {
                'id': result.id,
                'name': result.name,
                'description': result.description,
                'result_type': result.output_type,
                'tool_name': result.tool_used.name if result.tool_used else 'Unknown Tool',
                'tool_display_name': result.tool_used.display_name if result.tool_used else 'Unknown Tool',
                'session_id': result.session.id,
                'session_name': result.session.name,
                'execution_time_ms': result.execution_time_ms,
                'status': 'completed',  # Default status
                'created_at': result.created_at.isoformat(),
                'parameters': result.parameters_used,
                'result_data': result.result_data,
                'confidence_score': result.confidence_score,
                'quality_score': result.quality_score,
                'ai_interpretations': [
                    {
                        'id': interp.id,
                        'title': interp.title,
                        'content': interp.content,
                        'analysis_type': interp.analysis_type,
                        'confidence_score': interp.confidence_score,
                        'is_fallback': interp.is_fallback,
                        'created_at': interp.created_at.isoformat()
                    }
                    for interp in interpretations 
                    if interp.analysis_result_id == result.id
                ]
            }
            history.append(result_data)
        
        # Get dataset info
        dataset_info = {
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'row_count': dataset.row_count,
            'column_count': dataset.column_count,
            'file_size_bytes': dataset.file_size_bytes,
            'processing_status': dataset.processing_status,
            'data_quality_score': dataset.data_quality_score,
            'created_at': dataset.created_at.isoformat(),
            'original_filename': dataset.original_filename
        }
        
        return Response({
            'success': True,
            'dataset_info': dataset_info,
            'history': history,
            'total_count': len(history),
            'interpretations_count': len(interpretations),
            'message': f'Found {len(history)} analysis results for dataset {dataset.name}'
        })
        
    except Exception as e:
        logger.error(f"Error getting dataset analysis history: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve dataset analysis history'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_interpretations(request, analysis_result_id):
    """
    Get AI interpretations for a specific analysis result
    """
    try:
        from analytics.services.ai_interpretation_service import ai_interpretation_service
        
        interpretations = ai_interpretation_service.get_interpretations_for_analysis(
            analysis_result_id=analysis_result_id,
            user=request.user
        )
        
        return Response({
            'success': True,
            'interpretations': interpretations,
            'count': len(interpretations)
        })
        
    except Exception as e:
        logger.error(f"Error getting AI interpretations: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve AI interpretations'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_interpretation_detail(request, interpretation_id):
    """
    Get detailed information about a specific AI interpretation
    """
    try:
        from analytics.services.ai_interpretation_service import ai_interpretation_service
        
        interpretation = ai_interpretation_service.get_interpretation_by_id(
            interpretation_id=interpretation_id,
            user=request.user
        )
        
        if interpretation:
            return Response({
                'success': True,
                'interpretation': interpretation
            })
        else:
            return Response({
                'success': False,
                'error': 'Interpretation not found'
            }, status=404)
        
    except Exception as e:
        logger.error(f"Error getting interpretation detail: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve interpretation'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_interpretation_feedback(request, interpretation_id):
    """
    Update user feedback for an AI interpretation
    """
    try:
        from analytics.services.ai_interpretation_service import ai_interpretation_service
        
        data = request.data
        is_helpful = data.get('is_helpful', None)
        
        if is_helpful is None:
            return Response({
                'success': False,
                'error': 'is_helpful field is required'
            }, status=400)
        
        success = ai_interpretation_service.update_interpretation_feedback(
            interpretation_id=interpretation_id,
            user=request.user,
            is_helpful=is_helpful
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Feedback updated successfully'
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to update feedback'
            }, status=500)
        
    except Exception as e:
        logger.error(f"Error updating interpretation feedback: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update feedback'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_sandbox_code(request):
    """
    Execute Python code in secure sandbox environment
    """
    try:
        from analytics.services.sandbox_executor import SandboxExecutor
        from analytics.models import User, AnalysisSession
        import json
        
        data = request.data
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return Response({
                'success': False,
                'error': 'No code provided'
            }, status=400)
        
        # Get user (fallback to first user for development)
        user = request.user
        if not user.is_authenticated:
            user = User.objects.first()
            if not user:
                user = User.objects.create(
                    username='default_user',
                    email='user@example.com'
                )
        
        # Debug: Log user information
        logger.info(f"DEBUG: Sandbox execution - User ID: {user.id}, Username: {user.username}")
        
        # Get current session
        session = None
        try:
            # Try to get the latest session for the user
            session = AnalysisSession.objects.filter(user=user).order_by('-created_at').first()
            if session:
                logger.info(f"DEBUG: Sandbox execution - Session ID: {session.id}, Session Name: {session.name}")
            else:
                logger.info("DEBUG: Sandbox execution - No session found for user")
        except AnalysisSession.DoesNotExist:
            logger.info("DEBUG: Sandbox execution - Session does not exist")
            pass
        
        # Debug: Log code information
        logger.info(f"DEBUG: Sandbox execution - Code length: {len(code)} characters")
        logger.info(f"DEBUG: Sandbox execution - Language: {language}")
        
        # Initialize sandbox executor
        sandbox_executor = SandboxExecutor()
        
        # Execute code in sandbox
        result = sandbox_executor.execute_code(
            code=code,
            user=user,
            language=language,
            session=session
        )
        
        # Debug: Log execution result
        logger.info(f"DEBUG: Sandbox execution result - Execution ID: {result.id}, Status: {result.status}")
        
        # Format response
        response_data = {
            'success': result.status == 'completed',
            'status': result.status,
            'output': result.output,
            'error': result.error_message,
            'execution_time_ms': result.execution_time_ms,
            'memory_used_mb': result.memory_used_mb,
            'debug': {
                'user_id': user.id,
                'username': user.username,
                'session_id': session.id if session else None,
                'execution_id': result.id
            }
        }
        
        # If successful, try to parse output for plots and tables
        if result.status == 'completed' and result.output:
            try:
                # Attempt to parse output as JSON for structured data
                output_json = json.loads(result.output)
                if isinstance(output_json, dict):
                    if 'plots' in output_json:
                        response_data['plots'] = output_json['plots']
                    if 'tables' in output_json:
                        response_data['tables'] = output_json['tables']
            except json.JSONDecodeError:
                # If not JSON, treat as plain text output
                pass
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Sandbox execution error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
