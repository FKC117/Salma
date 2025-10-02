"""
Serializers for prescription management system

This module contains all serializers for the prescription management system,
providing JSON serialization for API endpoints.
"""

from rest_framework import serializers
from .models import (
    Patient, PatientProfile, Prescription, Observation,
    Drug, PrescriptionTemplate, DrugInteraction, PrescriptionAuditTrail
)


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient model."""
    prescriptions_count = serializers.SerializerMethodField()
    last_visit = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'uid', 'name', 'age', 'gender', 'phone', 'email', 'address',
            'emergency_contact', 'emergency_phone', 'created_at', 'updated_at',
            'prescriptions_count', 'last_visit'
        ]
        read_only_fields = ['uid', 'created_at', 'updated_at']
    
    def get_prescriptions_count(self, obj):
        """Get the number of prescriptions for this patient."""
        return obj.get_prescriptions_count()
    
    def get_last_visit(self, obj):
        """Get the date of the last visit."""
        last_visit = obj.get_last_visit()
        return last_visit.strftime('%Y-%m-%d') if last_visit else None


class PatientProfileSerializer(serializers.ModelSerializer):
    """Serializer for PatientProfile model."""
    allergies_list = serializers.SerializerMethodField()
    current_medications_list = serializers.SerializerMethodField()
    has_allergies = serializers.SerializerMethodField()
    has_current_medications = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientProfile
        fields = [
            'medical_history', 'allergies', 'current_medications',
            'vital_signs', 'lab_results', 'notes', 'created_at', 'updated_at',
            'allergies_list', 'current_medications_list', 'has_allergies', 'has_current_medications'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_allergies_list(self, obj):
        """Get a list of allergies."""
        return obj.get_allergies_list()
    
    def get_current_medications_list(self, obj):
        """Get a list of current medications."""
        return obj.get_current_medications_list()
    
    def get_has_allergies(self, obj):
        """Check if patient has any allergies."""
        return obj.has_allergies()
    
    def get_has_current_medications(self, obj):
        """Check if patient is currently taking medications."""
        return obj.has_current_medications()


class DrugSerializer(serializers.ModelSerializer):
    """Serializer for Drug model."""
    full_name = serializers.SerializerMethodField()
    interactions_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Drug
        fields = [
            'id', 'name', 'generic_name', 'dosage_form', 'strength',
            'indications', 'contraindications', 'side_effects', 'interactions',
            'category', 'is_active', 'created_at', 'updated_at',
            'full_name', 'interactions_list'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_full_name(self, obj):
        """Get the full drug name with generic name if available."""
        return obj.get_full_name()
    
    def get_interactions_list(self, obj):
        """Get a list of drug interactions."""
        return obj.get_interactions_list()


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for Prescription model."""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_uid = serializers.CharField(source='patient.uid', read_only=True)
    medications_list = serializers.SerializerMethodField()
    medications_count = serializers.SerializerMethodField()
    drug_names = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'patient_name', 'patient_uid', 'prescription_date',
            'diagnosis', 'symptoms', 'medications', 'instructions', 'follow_up_date',
            'status', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'medications_list', 'medications_count', 'drug_names', 'is_active', 'is_expired'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_medications_list(self, obj):
        """Get a list of medications."""
        return obj.get_medications_list()
    
    def get_medications_count(self, obj):
        """Get the number of medications in the prescription."""
        return obj.get_medications_count()
    
    def get_drug_names(self, obj):
        """Get a list of drug names in the prescription."""
        return obj.get_drug_names()
    
    def get_is_active(self, obj):
        """Check if the prescription is active."""
        return obj.is_active()
    
    def get_is_expired(self, obj):
        """Check if the prescription is expired."""
        return obj.is_expired()


class ObservationSerializer(serializers.ModelSerializer):
    """Serializer for Observation model."""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_uid = serializers.CharField(source='patient.uid', read_only=True)
    type_display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Observation
        fields = [
            'id', 'patient', 'patient_name', 'patient_uid', 'observation_date',
            'observation_type', 'symptoms', 'examination_findings', 'recommendations',
            'next_appointment', 'created_at', 'created_by', 'type_display_name'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_type_display_name(self, obj):
        """Get the display name for the observation type."""
        return obj.get_type_display_name()


class PrescriptionTemplateSerializer(serializers.ModelSerializer):
    """Serializer for PrescriptionTemplate model."""
    medications_list = serializers.SerializerMethodField()
    medications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PrescriptionTemplate
        fields = [
            'id', 'name', 'description', 'diagnosis', 'medications', 'instructions',
            'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'medications_list', 'medications_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_medications_list(self, obj):
        """Get a list of template medications."""
        return obj.get_medications_list()
    
    def get_medications_count(self, obj):
        """Get the number of medications in the template."""
        return obj.get_medications_count()


class DrugInteractionSerializer(serializers.ModelSerializer):
    """Serializer for DrugInteraction model."""
    drug1_name = serializers.CharField(source='drug1.name', read_only=True)
    drug2_name = serializers.CharField(source='drug2.name', read_only=True)
    severity_color = serializers.SerializerMethodField()
    
    class Meta:
        model = DrugInteraction
        fields = [
            'id', 'drug1', 'drug2', 'drug1_name', 'drug2_name',
            'interaction_type', 'description', 'severity', 'created_at',
            'severity_color'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_severity_color(self, obj):
        """Get the color code for the severity level."""
        return obj.get_severity_color()


class PrescriptionAuditTrailSerializer(serializers.ModelSerializer):
    """Serializer for PrescriptionAuditTrail model."""
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    action_display_name = serializers.SerializerMethodField()
    changes_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = PrescriptionAuditTrail
        fields = [
            'id', 'table_name', 'record_id', 'action', 'old_values', 'new_values',
            'changed_by', 'changed_by_username', 'changed_at', 'ip_address', 'user_agent',
            'action_display_name', 'changes_summary'
        ]
        read_only_fields = ['id', 'changed_at']
    
    def get_action_display_name(self, obj):
        """Get the display name for the action."""
        return obj.get_action_display_name()
    
    def get_changes_summary(self, obj):
        """Get a summary of the changes made."""
        return obj.get_changes_summary()
