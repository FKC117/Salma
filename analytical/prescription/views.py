"""
Views for prescription management system

This module contains all views for the prescription management system,
including API viewsets, template views, and HTMX endpoints.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.db.models import Q
from .models import (
    Patient, PatientProfile, Prescription, Observation,
    Drug, PrescriptionTemplate, DrugInteraction, PrescriptionAuditTrail
)
from .serializers import (
    PatientSerializer, PatientProfileSerializer, PrescriptionSerializer,
    ObservationSerializer, DrugSerializer, PrescriptionTemplateSerializer,
    DrugInteractionSerializer, PrescriptionAuditTrailSerializer
)


# Template Views
@login_required
def dashboard_view(request):
    """Main dashboard view for prescription management."""
    # Get basic statistics
    total_patients = Patient.objects.count()
    total_prescriptions = Prescription.objects.count()
    active_prescriptions = Prescription.objects.filter(status='active').count()
    
    context = {
        'title': 'Prescription Management Dashboard',
        'user': request.user,
        'total_patients': total_patients,
        'total_prescriptions': total_prescriptions,
        'active_prescriptions': active_prescriptions,
    }
    return render(request, 'prescription/dashboard_prescription.html', context)


@login_required
def patient_list_view(request):
    """Patient list view."""
    patients = Patient.objects.all().order_by('name')
    context = {
        'title': 'Patient List',
        'patients': patients,
        'user': request.user,
    }
    return render(request, 'prescription/patient_list.html', context)


@login_required
def patient_detail_view(request, uid):
    """Patient detail view."""
    patient = get_object_or_404(Patient, uid=uid)
    prescriptions = patient.prescriptions.all().order_by('-prescription_date')
    observations = patient.observations.all().order_by('-observation_date')
    
    context = {
        'title': f'Patient {patient.name}',
        'patient': patient,
        'prescriptions': prescriptions,
        'observations': observations,
        'user': request.user,
    }
    return render(request, 'prescription/patient_detail.html', context)


@login_required
def prescription_list_view(request):
    """Prescription list view."""
    prescriptions = Prescription.objects.all().order_by('-prescription_date')
    context = {
        'title': 'Prescription List',
        'prescriptions': prescriptions,
        'user': request.user,
    }
    return render(request, 'prescription/prescription_list.html', context)


@login_required
def prescription_detail_view(request, id):
    """Prescription detail view."""
    prescription = get_object_or_404(Prescription, id=id)
    context = {
        'title': f'Prescription {prescription.id}',
        'prescription': prescription,
        'user': request.user,
    }
    return render(request, 'prescription/prescription_detail.html', context)


@login_required
def analytics_view(request):
    """Analytics dashboard view."""
    context = {
        'title': 'Analytics Dashboard',
        'user': request.user,
    }
    return render(request, 'prescription/analytics.html', context)


@login_required
def add_patient_view(request):
    """Add new patient view."""
    if request.method == 'POST':
        # Handle patient creation
        from .forms import PatientForm
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.updated_by = request.user
            patient.save()
            
            # Create patient profile
            PatientProfile.objects.create(
                patient=patient,
                created_by=request.user,
                updated_by=request.user
            )
            
            return redirect('prescription_patient_detail', uid=patient.uid)
    else:
        from .forms import PatientForm
        form = PatientForm()
    
    context = {
        'title': 'Add New Patient',
        'form': form,
        'user': request.user,
    }
    return render(request, 'prescription/add_patient.html', context)


# API Viewsets
class PatientViewSet(viewsets.ModelViewSet):
    """ViewSet for Patient model."""
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on search parameters."""
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
                queryset = queryset.filter(
                    Q(uid__icontains=search) |
                    Q(name__icontains=search) |
                    Q(phone__icontains=search)
                )
        return queryset
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get patient history."""
        patient = self.get_object()
        prescriptions = patient.prescriptions.all()
        observations = patient.observations.all()
        
        return Response({
            'patient': PatientSerializer(patient).data,
            'prescriptions': PrescriptionSerializer(prescriptions, many=True).data,
            'observations': ObservationSerializer(observations, many=True).data,
        })


class PrescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for Prescription model."""
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on patient."""
        queryset = super().get_queryset()
        patient_uid = self.request.query_params.get('patient_uid')
        if patient_uid:
            queryset = queryset.filter(patient__uid=patient_uid)
        return queryset
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Validate prescription data."""
        # This will be implemented when we add validation logic
        return Response({'valid': True, 'errors': [], 'warnings': []})


class DrugViewSet(viewsets.ModelViewSet):
    """ViewSet for Drug model."""
    queryset = Drug.objects.filter(is_active=True)
    serializer_class = DrugSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on search parameters."""
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
                    queryset = queryset.filter(
                        Q(name__icontains=search) |
                        Q(generic_name__icontains=search)
                    )
        return queryset


class PrescriptionTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for PrescriptionTemplate model."""
    queryset = PrescriptionTemplate.objects.filter(is_active=True)
    serializer_class = PrescriptionTemplateSerializer
    permission_classes = [IsAuthenticated]


class ObservationViewSet(viewsets.ModelViewSet):
    """ViewSet for Observation model."""
    queryset = Observation.objects.all()
    serializer_class = ObservationSerializer
    permission_classes = [IsAuthenticated]


class DrugInteractionViewSet(viewsets.ModelViewSet):
    """ViewSet for DrugInteraction model."""
    queryset = DrugInteraction.objects.all()
    serializer_class = DrugInteractionSerializer
    permission_classes = [IsAuthenticated]


class PrescriptionAuditTrailViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for PrescriptionAuditTrail model (read-only)."""
    queryset = PrescriptionAuditTrail.objects.all()
    serializer_class = PrescriptionAuditTrailSerializer
    permission_classes = [IsAuthenticated]


# HTMX Views
@login_required
@require_http_methods(["GET"])
def patient_search_htmx(request):
    """HTMX endpoint for unified patient search."""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'patient')  # 'patient' or 'prescription'
    
    if query:
        # Search patients
        patients = Patient.objects.filter(
            Q(uid__icontains=query) |
            Q(name__icontains=query) |
            Q(phone__icontains=query)
        ).order_by('name')[:10]
        
        # Search prescriptions if type is prescription
        prescriptions = []
        if search_type == 'prescription':
            prescriptions = Prescription.objects.filter(
                Q(patient__uid__icontains=query) |
                Q(patient__name__icontains=query) |
                Q(patient__phone__icontains=query) |
                Q(diagnosis__icontains=query) |
                Q(symptoms__icontains=query)
            ).order_by('-prescription_date')[:10]
    else:
        # Show recent patients when no search query
        patients = Patient.objects.all().order_by('-created_at')[:5]
        prescriptions = []
    
    context = {
        'patients': patients, 
        'prescriptions': prescriptions,
        'query': query,
        'search_type': search_type
    }
    return render(request, 'prescription/partials/unified_search_results.html', context)


@login_required
@require_http_methods(["GET"])
def patient_list_htmx(request):
    """HTMX endpoint for patient list."""
    patients = Patient.objects.all().order_by('name')
    context = {'patients': patients}
    return render(request, 'prescription/partials/patient_list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def prescription_form_htmx(request):
    """HTMX endpoint for prescription form."""
    if request.method == 'POST':
        # Handle prescription creation
        pass
    
    templates = PrescriptionTemplate.objects.filter(is_active=True)
    context = {'templates': templates}
    return render(request, 'prescription/partials/prescription_form.html', context)


@login_required
@require_http_methods(["GET"])
def prescription_form_patient_search_htmx(request):
    """HTMX endpoint for patient search in prescription form."""
    query = request.GET.get('q', '')
    if query:
        patients = Patient.objects.filter(
            Q(uid__icontains=query) |
            Q(name__icontains=query) |
            Q(phone__icontains=query)
        ).order_by('name')[:10]
    else:
        # Show recent patients when no search query
        patients = Patient.objects.all().order_by('-created_at')[:5]
    
    context = {'patients': patients, 'query': query}
    return render(request, 'prescription/partials/patient_search_form_results.html', context)


@login_required
@require_http_methods(["GET"])
def patient_history_htmx(request, uid):
    """HTMX endpoint for patient history modal."""
    patient = get_object_or_404(Patient, uid=uid)
    
    # Get all prescriptions and observations
    prescriptions = patient.prescriptions.all().order_by('-prescription_date')
    observations = patient.observations.all().order_by('-observation_date')
    
    # Create timeline items
    timeline_items = []
    
    # Add prescriptions to timeline
    for prescription in prescriptions:
        timeline_items.append({
            'type': 'prescription',
            'date': prescription.prescription_date,
            'object': prescription,
            'title': f'Prescription #{prescription.id}',
            'description': prescription.diagnosis,
            'details': {
                'symptoms': prescription.symptoms,
                'medications_count': prescription.get_medications_count(),
                'follow_up_date': prescription.follow_up_date,
                'status': prescription.status
            }
        })
    
    # Add observations to timeline
    for observation in observations:
        timeline_items.append({
            'type': 'observation',
            'date': observation.observation_date,
            'object': observation,
            'title': f'{observation.get_type_display_name()} Visit',
            'description': observation.symptoms or observation.examination_findings,
            'details': {
                'examination_findings': observation.examination_findings,
                'recommendations': observation.recommendations,
                'next_appointment': observation.next_appointment
            }
        })
    
    # Sort timeline by date (most recent first)
    timeline_items.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate summary statistics
    total_prescriptions = prescriptions.count()
    total_observations = observations.count()
    first_visit = None
    last_visit = None
    
    if timeline_items:
        first_visit = timeline_items[-1]['date']  # Oldest
        last_visit = timeline_items[0]['date']    # Most recent
    
    # Get unique diagnoses
    diagnoses = prescriptions.values_list('diagnosis', flat=True).distinct()
    
    context = {
        'patient': patient,
        'timeline_items': timeline_items,
        'total_prescriptions': total_prescriptions,
        'total_observations': total_observations,
        'first_visit': first_visit,
        'last_visit': last_visit,
        'diagnoses': diagnoses,
    }
    return render(request, 'prescription/partials/patient_history_content.html', context)


@login_required
@require_http_methods(["GET"])
def patient_timeline_htmx(request, uid):
    """HTMX endpoint for patient timeline."""
    patient = get_object_or_404(Patient, uid=uid)
    prescriptions = patient.prescriptions.all().order_by('-prescription_date')
    observations = patient.observations.all().order_by('-observation_date')
    
    # Combine and sort by date
    timeline_items = []
    for prescription in prescriptions:
        timeline_items.append({
            'type': 'prescription',
            'date': prescription.prescription_date,
            'object': prescription
        })
    for observation in observations:
        timeline_items.append({
            'type': 'observation',
            'date': observation.observation_date,
            'object': observation
        })
    
    timeline_items.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'patient': patient,
        'timeline_items': timeline_items
    }
    return render(request, 'prescription/partials/patient_timeline.html', context)


@login_required
@require_http_methods(["GET"])
def prescription_search_htmx(request):
    """HTMX endpoint for prescription search."""
    query = request.GET.get('q', '')
    patient_uid = request.GET.get('patient_uid', '')
    
    prescriptions = Prescription.objects.all()
    
    if patient_uid:
        prescriptions = prescriptions.filter(patient__uid=patient_uid)
    
    if query:
        prescriptions = prescriptions.filter(
            Q(patient__name__icontains=query) |
            Q(patient__uid__icontains=query) |
            Q(diagnosis__icontains=query) |
            Q(symptoms__icontains=query)
        )
    
    prescriptions = prescriptions.order_by('-prescription_date')[:10]
    
    context = {'prescriptions': prescriptions, 'query': query}
    return render(request, 'prescription/partials/prescription_search_results.html', context)


@login_required
@require_http_methods(["POST"])
def drug_interactions_htmx(request):
    """HTMX endpoint for drug interaction checking."""
    # This will be implemented when we add drug interaction checking
    return JsonResponse({'interactions': []})


# Additional API endpoints
@login_required
@require_http_methods(["GET"])
def patient_search_api(request):
    """API endpoint for patient search."""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 10))
    
    if query:
                patients = Patient.objects.filter(
                    Q(uid__icontains=query) |
                    Q(name__icontains=query) |
                    Q(phone__icontains=query)
                ).order_by('name')[:limit]
    else:
        patients = Patient.objects.none()
    
    serializer = PatientSerializer(patients, many=True)
    return JsonResponse({
        'results': serializer.data,
        'count': len(serializer.data)
    })


@login_required
@require_http_methods(["POST"])
def prescription_validate_api(request):
    """API endpoint for prescription validation."""
    # This will be implemented when we add validation logic
    return JsonResponse({'valid': True, 'errors': [], 'warnings': []})


@login_required
@require_http_methods(["POST"])
def drug_interactions_api(request):
    """API endpoint for drug interaction checking."""
    # This will be implemented when we add drug interaction checking
    return JsonResponse({'interactions': []})


@login_required
@require_http_methods(["GET"])
def patient_history_api(request, uid):
    """API endpoint for patient history."""
    patient = get_object_or_404(Patient, uid=uid)
    prescriptions = patient.prescriptions.all()
    observations = patient.observations.all()
    
    return JsonResponse({
        'patient': PatientSerializer(patient).data,
        'prescriptions': PrescriptionSerializer(prescriptions, many=True).data,
        'observations': ObservationSerializer(observations, many=True).data,
    })


@login_required
@require_http_methods(["GET"])
def patient_timeline_api(request, uid):
    """API endpoint for patient timeline."""
    patient = get_object_or_404(Patient, uid=uid)
    prescriptions = patient.prescriptions.all().order_by('-prescription_date')
    observations = patient.observations.all().order_by('-observation_date')
    
    timeline_items = []
    for prescription in prescriptions:
        timeline_items.append({
            'type': 'prescription',
            'date': prescription.prescription_date,
            'data': PrescriptionSerializer(prescription).data
        })
    for observation in observations:
        timeline_items.append({
            'type': 'observation',
            'date': observation.observation_date,
            'data': ObservationSerializer(observation).data
        })
    
    timeline_items.sort(key=lambda x: x['date'], reverse=True)
    
    return JsonResponse({
        'patient': PatientSerializer(patient).data,
        'timeline': timeline_items
    })


@login_required
@require_http_methods(["GET"])
def dashboard_analytics_api(request):
    """API endpoint for dashboard analytics."""
    # This will be implemented when we add analytics
    return JsonResponse({
        'total_patients': Patient.objects.count(),
        'total_prescriptions': Prescription.objects.count(),
        'active_prescriptions': Prescription.objects.filter(status='active').count(),
    })


@login_required
@require_http_methods(["GET"])
def prescription_analytics_api(request):
    """API endpoint for prescription analytics."""
    # This will be implemented when we add analytics
    return JsonResponse({
        'prescriptions_by_status': {},
        'top_medications': [],
        'daily_trends': [],
    })