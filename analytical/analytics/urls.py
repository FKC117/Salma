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
    path('api/', include(router.urls)),
]
