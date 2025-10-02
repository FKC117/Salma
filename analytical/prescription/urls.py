"""
URL configuration for prescription app

This module defines all URL patterns for the prescription management system,
including API endpoints, template views, and HTMX endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()

# Register API viewsets
router.register(r'patients', views.PatientViewSet, basename='patient')
router.register(r'prescriptions', views.PrescriptionViewSet, basename='prescription')
router.register(r'drugs', views.DrugViewSet, basename='drug')
router.register(r'templates', views.PrescriptionTemplateViewSet, basename='template')
router.register(r'observations', views.ObservationViewSet, basename='observation')
router.register(r'interactions', views.DrugInteractionViewSet, basename='interaction')
router.register(r'audit', views.PrescriptionAuditTrailViewSet, basename='audit')

urlpatterns = [
    # Template views (must come first to avoid API router conflicts)
    path('', views.dashboard_view, name='prescription_dashboard'),
    path('dashboard/', views.dashboard_view, name='prescription_dashboard'),
    path('patients/', views.patient_list_view, name='prescription_patient_list'),
    path('patients/add/', views.add_patient_view, name='prescription_add_patient'),
    path('patients/<str:uid>/', views.patient_detail_view, name='prescription_patient_detail'),
    path('prescriptions/', views.prescription_list_view, name='prescription_prescription_list'),
    path('prescriptions/<int:id>/', views.prescription_detail_view, name='prescription_prescription_detail'),
    path('analytics/', views.analytics_view, name='prescription_analytics'),
    
    # HTMX endpoints
    path('htmx/patient-search/', views.patient_search_htmx, name='prescription_patient_search_htmx'),
    path('htmx/patient-list/', views.patient_list_htmx, name='prescription_patient_list_htmx'),
    path('htmx/prescription-search/', views.prescription_search_htmx, name='prescription_prescription_search_htmx'),
    path('htmx/prescription-form/', views.prescription_form_htmx, name='prescription_form_htmx'),
    path('htmx/prescription-form-patient-search/', views.prescription_form_patient_search_htmx, name='prescription_form_patient_search_htmx'),
    path('htmx/patient-history/<str:uid>/', views.patient_history_htmx, name='prescription_patient_history_htmx'),
    path('htmx/patient-timeline/<str:uid>/', views.patient_timeline_htmx, name='prescription_patient_timeline_htmx'),
    path('htmx/drug-interactions/', views.drug_interactions_htmx, name='prescription_drug_interactions_htmx'),
    
    # API endpoints (must come last to avoid conflicts)
    path('api/', include(router.urls)),
    
    # Additional API endpoints
    path('api/patients/search/', views.patient_search_api, name='prescription_patient_search_api'),
    path('api/prescriptions/validate/', views.prescription_validate_api, name='prescription_validate_api'),
    path('api/drugs/interactions/', views.drug_interactions_api, name='prescription_drug_interactions_api'),
    path('api/patients/<str:uid>/history/', views.patient_history_api, name='prescription_patient_history_api'),
    path('api/patients/<str:uid>/timeline/', views.patient_timeline_api, name='prescription_patient_timeline_api'),
    path('api/analytics/dashboard/', views.dashboard_analytics_api, name='prescription_dashboard_analytics_api'),
    path('api/analytics/prescriptions/', views.prescription_analytics_api, name='prescription_analytics_api'),
]
