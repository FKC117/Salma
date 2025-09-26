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

from analytics.models import Dataset, DatasetColumn, User, AuditTrail
from analytics.services.file_processing import FileProcessingService
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.session_manager import SessionManager
from analytics.services.analysis_executor import AnalysisExecutor
from analytics.services.rag_service import RAGService
from analytics.services.llm_processor import LLMProcessor
from analytics.services.agentic_ai_controller import AgenticAIController
from analytics.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


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
            
            if 'name' not in request.data:
                return Response({
                    'success': False,
                    'error': 'Dataset name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            dataset_name = request.data['name']
            
            # Get user (for now, use first user or create one)
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
            
            # Process file
            file_service = FileProcessingService()
            result = file_service.process_uploaded_file(
                file=file,
                filename=file.name,
                dataset_name=dataset_name,
                user=user
            )
            
            if result['success']:
                # Log audit trail
                audit_manager = AuditTrailManager()
                audit_manager.log_user_action(
                    user_id=user.id,
                    action_type='file_upload',
                    resource_type='dataset',
                    resource_id=result['dataset_id'],
                    resource_name=dataset_name,
                    action_description=f"Uploaded dataset: {dataset_name}",
                    success=True
                )
                
                return Response({
                    'success': True,
                    'dataset_id': result['dataset_id'],
                    'message': f'Dataset "{dataset_name}" uploaded successfully',
                    'columns': result['columns']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'File processing failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
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
            
            # Create session
            session_manager = SessionManager()
            result = session_manager.create_session(
                user=user,
                dataset_id=dataset_id,
                session_name=request.data.get('session_name', f'Session {timezone.now().strftime("%Y-%m-%d %H:%M")}')
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'session_id': result['session_id'],
                    'message': 'Analysis session created successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Session creation failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
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
            
            # Execute analysis
            executor = AnalysisExecutor()
            result = executor.execute_analysis(
                user=user,
                session_id=request.data['session_id'],
                tool_name=request.data['tool_name'],
                parameters=request.data['parameters']
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'result_id': result['result_id'],
                    'message': 'Analysis executed successfully',
                    'output': result.get('output', {}),
                    'visualizations': result.get('visualizations', [])
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Analysis execution failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
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
            result = rag_service.upsert_content(
                content=request.data['content'],
                metadata=request.data['metadata'],
                user_id=user.id
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'vector_id': result['vector_id'],
                    'message': 'Content upserted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'RAG upsert failed')
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
            result = rag_service.search_content(
                query=query,
                user_id=user.id,
                limit=int(request.query_params.get('limit', 10))
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'results': result['results'],
                    'message': f'Found {len(result["results"])} results'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'RAG search failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
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
            result = rag_service.clear_user_content(user_id=user.id)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'RAG content cleared successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'RAG clear failed')
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
            result = llm_processor.process_message(
                user=user,
                message=request.data['message'],
                session_id=request.data.get('session_id'),
                context=request.data.get('context', {})
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'response': result['response'],
                    'message_id': result['message_id'],
                    'token_usage': result.get('token_usage', {}),
                    'message': 'Message processed successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Message processing failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Chat message error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                'tools': tools,
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
            
            # Run agent
            agent_controller = AgenticAIController()
            result = agent_controller.run_agent(
                user=user,
                session_id=request.data['session_id'],
                objective=request.data.get('objective', 'Analyze the dataset'),
                max_steps=int(request.data.get('max_steps', 10))
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'agent_run_id': result['agent_run_id'],
                    'message': 'Agent run started successfully',
                    'status': result.get('status', 'running')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Agent run failed')
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
            result = audit_manager.get_user_audit_trail(
                user_id=user.id,
                limit=int(request.query_params.get('limit', 50)),
                action_type=request.query_params.get('action_type'),
                resource_type=request.query_params.get('resource_type')
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'audit_entries': result['audit_entries'],
                    'message': f'Found {len(result["audit_entries"])} audit entries'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Audit trail retrieval failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Audit trail error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
