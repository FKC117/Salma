"""
URL configuration for analytics app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()

# Register API viewsets
router.register(r'upload', views.UploadViewSet, basename='upload')
router.register(r'sessions', views.SessionViewSet, basename='sessions')
router.register(r'analysis', views.AnalysisViewSet, basename='analysis')
router.register(r'rag', views.RAGViewSet, basename='rag')
router.register(r'chat', views.ChatViewSet, basename='chat')
router.register(r'tools', views.ToolsViewSet, basename='tools')
router.register(r'agent', views.AgentViewSet, basename='agent')
router.register(r'audit', views.AuditViewSet, basename='audit')

urlpatterns = [
    # Template views
    path('', views.dashboard_view, name='dashboard'),
    path('upload-form/', views.upload_form_view, name='upload_form'),
    
    # CSRF token endpoint
    path('api/csrf-token/', views.get_csrf_token, name='csrf_token'),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Named URL patterns for HTMX
    path('upload/', views.UploadViewSet.as_view({'post': 'upload'}), name='upload_file'),
    path('sessions/create/', views.SessionViewSet.as_view({'post': 'create_session'}), name='create_session'),
    path('analysis/execute/', views.AnalysisViewSet.as_view({'post': 'execute'}), name='analysis_execute'),
    path('rag/upsert/', views.RAGViewSet.as_view({'post': 'upsert'}), name='rag_upsert'),
    path('rag/search/', views.RAGViewSet.as_view({'get': 'search'}), name='rag_search'),
    path('rag/clear/', views.RAGViewSet.as_view({'delete': 'clear'}), name='rag_clear'),
    path('chat/messages/', views.ChatViewSet.as_view({'post': 'messages'}), name='chat_messages'),
    path('tools/list/', views.ToolsViewSet.as_view({'get': 'list_tools'}), name='tools_refresh'),
    path('agent/run/', views.AgentViewSet.as_view({'post': 'run'}), name='agent_run'),
    path('audit/trail/', views.AuditViewSet.as_view({'get': 'trail'}), name='audit_trail'),
]
