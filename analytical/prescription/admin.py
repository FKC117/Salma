"""
Django Admin Configuration for Prescription Management System

This module provides comprehensive admin interface configuration for all prescription models,
including custom admin classes, search functionality, and detailed field configurations.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Patient, PatientProfile, Prescription, Observation, 
    Drug, PrescriptionTemplate, DrugInteraction, PrescriptionAuditTrail
)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Admin configuration for Patient model."""
    list_display = [
        'uid', 'name', 'age', 'gender', 'phone', 'email', 
        'get_prescriptions_count', 'get_last_visit', 'created_at'
    ]
    list_filter = ['gender', 'created_at', 'updated_at']
    search_fields = ['uid', 'name', 'phone', 'email']
    readonly_fields = ['uid', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('uid', 'name', 'age', 'gender')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('System Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_prescriptions_count(self, obj):
        """Display the number of prescriptions for this patient."""
        count = obj.get_prescriptions_count()
        if count > 0:
            url = reverse('admin:prescription_prescription_changelist') + f'?patient__uid={obj.uid}'
            return format_html('<a href="{}">{} prescriptions</a>', url, count)
        return '0 prescriptions'
    get_prescriptions_count.short_description = 'Prescriptions'
    
    def get_last_visit(self, obj):
        """Display the date of the last visit."""
        last_visit = obj.get_last_visit()
        return last_visit.strftime('%Y-%m-%d') if last_visit else 'No visits'
    get_last_visit.short_description = 'Last Visit'
    
    def save_model(self, request, obj, form, change):
        """Set the created_by and updated_by fields."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    """Admin configuration for PatientProfile model."""
    list_display = ['patient', 'has_allergies', 'has_current_medications', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['patient__name', 'patient__uid']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Medical Information', {
            'fields': ('medical_history', 'allergies', 'current_medications')
        }),
        ('Clinical Data', {
            'fields': ('vital_signs', 'lab_results')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('System Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_allergies(self, obj):
        """Display if patient has allergies."""
        return 'Yes' if obj.has_allergies() else 'No'
    has_allergies.short_description = 'Has Allergies'
    has_allergies.boolean = True
    
    def has_current_medications(self, obj):
        """Display if patient has current medications."""
        return 'Yes' if obj.has_current_medications() else 'No'
    has_current_medications.short_description = 'Current Medications'
    has_current_medications.boolean = True
    
    def save_model(self, request, obj, form, change):
        """Set the created_by and updated_by fields."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """Admin configuration for Prescription model."""
    list_display = [
        'id', 'patient', 'diagnosis', 'get_medications_count', 
        'status', 'prescription_date', 'created_by'
    ]
    list_filter = ['status', 'prescription_date', 'created_at']
    search_fields = ['patient__name', 'patient__uid', 'diagnosis']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Prescription Information', {
            'fields': ('id', 'patient', 'prescription_date', 'status')
        }),
        ('Medical Information', {
            'fields': ('diagnosis', 'symptoms')
        }),
        ('Medications', {
            'fields': ('medications',)
        }),
        ('Instructions', {
            'fields': ('instructions', 'follow_up_date')
        }),
        ('System Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_medications_count(self, obj):
        """Display the number of medications in the prescription."""
        return obj.get_medications_count()
    get_medications_count.short_description = 'Medications'
    
    def save_model(self, request, obj, form, change):
        """Set the created_by and updated_by fields."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    """Admin configuration for Observation model."""
    list_display = [
        'id', 'patient', 'observation_type', 'observation_date', 
        'get_type_display_name', 'created_by'
    ]
    list_filter = ['observation_type', 'observation_date', 'created_at']
    search_fields = ['patient__name', 'patient__uid', 'symptoms']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Observation Information', {
            'fields': ('id', 'patient', 'observation_date', 'observation_type')
        }),
        ('Clinical Findings', {
            'fields': ('symptoms', 'examination_findings')
        }),
        ('Recommendations', {
            'fields': ('recommendations', 'next_appointment')
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set the created_by field."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    """Admin configuration for Drug model."""
    list_display = [
        'name', 'generic_name', 'dosage_form', 'strength', 
        'category', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'dosage_form', 'is_active', 'created_at']
    search_fields = ['name', 'generic_name', 'category']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Drug Information', {
            'fields': ('name', 'generic_name', 'dosage_form', 'strength', 'category')
        }),
        ('Medical Information', {
            'fields': ('indications', 'contraindications', 'side_effects')
        }),
        ('Interactions', {
            'fields': ('interactions',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PrescriptionTemplate)
class PrescriptionTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for PrescriptionTemplate model."""
    list_display = [
        'name', 'diagnosis', 'get_medications_count', 
        'is_active', 'created_by', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'diagnosis']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Medical Information', {
            'fields': ('diagnosis',)
        }),
        ('Template Content', {
            'fields': ('medications', 'instructions')
        }),
        ('System Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_medications_count(self, obj):
        """Display the number of medications in the template."""
        return obj.get_medications_count()
    get_medications_count.short_description = 'Medications'
    
    def save_model(self, request, obj, form, change):
        """Set the created_by and updated_by fields."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    """Admin configuration for DrugInteraction model."""
    list_display = [
        'drug1', 'drug2', 'interaction_type', 'severity', 
        'get_severity_color', 'created_at'
    ]
    list_filter = ['interaction_type', 'severity', 'created_at']
    search_fields = ['drug1__name', 'drug2__name', 'description']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Drugs', {
            'fields': ('drug1', 'drug2')
        }),
        ('Interaction Details', {
            'fields': ('interaction_type', 'severity', 'description')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_severity_color(self, obj):
        """Display severity with color coding."""
        color = obj.get_severity_color()
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_severity_display()
        )
    get_severity_color.short_description = 'Severity'


@admin.register(PrescriptionAuditTrail)
class PrescriptionAuditTrailAdmin(admin.ModelAdmin):
    """Admin configuration for PrescriptionAuditTrail model."""
    list_display = [
        'table_name', 'record_id', 'action', 'changed_by', 
        'changed_at', 'ip_address'
    ]
    list_filter = ['table_name', 'action', 'changed_at', 'changed_by']
    search_fields = ['table_name', 'record_id', 'changed_by__username']
    readonly_fields = ['changed_at']
    fieldsets = (
        ('Audit Information', {
            'fields': ('table_name', 'record_id', 'action')
        }),
        ('Changes', {
            'fields': ('old_values', 'new_values')
        }),
        ('System Information', {
            'fields': ('changed_by', 'changed_at', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable adding new audit trail records."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing audit trail records."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting audit trail records."""
        return False


# Customize admin site
admin.site.site_header = "Prescription Management System"
admin.site.site_title = "Prescription Admin"
admin.site.index_title = "Welcome to Prescription Management Administration"