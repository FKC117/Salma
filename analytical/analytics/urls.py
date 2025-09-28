"""
URL configuration for analytics app
"""
from django.urls import path, include
from django.shortcuts import redirect
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
    # Template views (must come first to avoid API router conflicts)
    path('', lambda request: redirect('login'), name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('upload-form/', views.upload_form_view, name='upload_form'),
    path('register/', views.register_view, name='register'),
    path('my-datasets/', views.my_datasets_view, name='my_datasets'),
    path('api/datasets/', views.list_datasets_view, name='list_datasets'),
    
    # CSRF token endpoint
    path('api/csrf-token/', views.get_csrf_token, name='csrf_token'),
    
    # Named URL patterns for HTMX (before API router)
    path('upload/', views.UploadViewSet.as_view({'post': 'upload'}), name='upload_file'),
    path('api/datasets/', views.api_datasets_list, name='api_datasets_list'),
    path('api/sessions/create/', views.api_create_session, name='api_create_session'),
    path('api/sessions/current/', views.api_current_session, name='api_current_session'),
    path('analysis/execute/', views.AnalysisViewSet.as_view({'post': 'execute'}), name='analysis_execute'),
    path('rag/upsert/', views.RAGViewSet.as_view({'post': 'upsert'}), name='rag_upsert'),
    path('rag/search/', views.RAGViewSet.as_view({'get': 'search'}), name='rag_search'),
    path('rag/clear/', views.RAGViewSet.as_view({'delete': 'clear'}), name='rag_clear'),
    path('chat/messages/', views.ChatViewSet.as_view({'post': 'messages'}), name='chat_messages'),
    path('tools/list/', views.ToolsViewSet.as_view({'get': 'list_tools'}), name='tools_refresh'),
    path('agent/run/', views.AgentViewSet.as_view({'post': 'run'}), name='agent_run'),
    path('audit/trail/', views.AuditViewSet.as_view({'get': 'trail'}), name='audit_trail'),
    path('api/ai/interpret-analysis/', views.interpret_analysis_result, name='interpret_analysis'),
    path('api/ai/interpretations/<int:analysis_result_id>/', views.get_ai_interpretations, name='get_ai_interpretations'),
    path('api/ai/interpretation/<int:interpretation_id>/', views.get_interpretation_detail, name='get_interpretation_detail'),
    path('api/ai/interpretation/<int:interpretation_id>/feedback/', views.update_interpretation_feedback, name='update_interpretation_feedback'),
    path('api/sessions/<int:session_id>/history/', views.get_analysis_history, name='get_analysis_history'),
    path('api/tools/list/', views.list_analysis_tools, name='list_analysis_tools'),
    path('api/tools/configure/<str:tool_id>/', views.get_tool_configuration, name='get_tool_configuration'),
    path('api/tools/execute/', views.execute_analysis_tool, name='execute_analysis_tool'),
    
    # API endpoints (must come last to avoid conflicts)
    path('api/', include(router.urls)),
]