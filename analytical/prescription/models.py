"""
Prescription Management System Models

This module contains all the database models for the prescription management system,
including patient management, prescription tracking, drug database, and audit trails.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json

User = get_user_model()


class Patient(models.Model):
    """
    Patient model with unique UID system for comprehensive patient management.
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('Other', 'Other'),
    ]
    
    uid = models.CharField(max_length=20, unique=True, primary_key=True, verbose_name="Patient UID")
    name = models.CharField(max_length=100, verbose_name="Full Name")
    age = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        verbose_name="Age"
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="Gender")
    phone = models.CharField(max_length=15, verbose_name="Phone Number")
    email = models.EmailField(blank=True, verbose_name="Email Address")
    address = models.TextField(blank=True, verbose_name="Address")
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name="Emergency Contact")
    emergency_phone = models.CharField(max_length=15, blank=True, verbose_name="Emergency Phone")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_patients', verbose_name="Created By")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_patients', verbose_name="Updated By")
    
    class Meta:
        db_table = 'prescription_patients'
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['name', 'phone', 'uid']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.uid} - {self.name}"
    
    def get_full_name(self):
        """Return the patient's full name."""
        return self.name
    
    def get_age_group(self):
        """Return the patient's age group."""
        if self.age < 18:
            return 'Pediatric'
        elif self.age < 65:
            return 'Adult'
        else:
            return 'Geriatric'
    
    def get_prescriptions_count(self):
        """Return the number of prescriptions for this patient."""
        return self.prescriptions.count()
    
    def get_last_visit(self):
        """Return the date of the last visit."""
        last_prescription = self.prescriptions.order_by('-prescription_date').first()
        if last_prescription:
            return last_prescription.prescription_date
        return None


class PatientProfile(models.Model):
    """
    Patient medical profile with comprehensive medical history and current status.
    """
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='profile', verbose_name="Patient")
    medical_history = models.TextField(blank=True, verbose_name="Medical History")
    allergies = models.TextField(blank=True, verbose_name="Allergies")
    current_medications = models.TextField(blank=True, verbose_name="Current Medications")
    vital_signs = models.JSONField(default=dict, verbose_name="Vital Signs")
    lab_results = models.JSONField(default=dict, verbose_name="Lab Results")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_profiles', verbose_name="Created By")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_profiles', verbose_name="Updated By")
    
    class Meta:
        db_table = 'prescription_patient_profiles'
        verbose_name = 'Patient Profile'
        verbose_name_plural = 'Patient Profiles'
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['vital_signs'], name='idx_profiles_vital_signs'),
            models.Index(fields=['lab_results'], name='idx_profiles_lab_results'),
        ]
    
    def __str__(self):
        return f"Profile for {self.patient.name}"
    
    def get_allergies_list(self):
        """Return a list of allergies."""
        if self.allergies:
            return [allergy.strip() for allergy in self.allergies.split(',')]
        return []
    
    def get_current_medications_list(self):
        """Return a list of current medications."""
        if self.current_medications:
            return [med.strip() for med in self.current_medications.split(',')]
        return []
    
    def has_allergies(self):
        """Check if patient has any allergies."""
        return bool(self.allergies.strip())
    
    def has_current_medications(self):
        """Check if patient is currently taking medications."""
        return bool(self.current_medications.strip())


class Drug(models.Model):
    """
    Drug database with comprehensive drug information and interaction data.
    """
    name = models.CharField(max_length=200, verbose_name="Drug Name")
    generic_name = models.CharField(max_length=200, blank=True, verbose_name="Generic Name")
    dosage_form = models.CharField(max_length=50, verbose_name="Dosage Form")
    strength = models.CharField(max_length=50, verbose_name="Strength")
    indications = models.TextField(blank=True, verbose_name="Indications")
    contraindications = models.TextField(blank=True, verbose_name="Contraindications")
    side_effects = models.TextField(blank=True, verbose_name="Side Effects")
    interactions = models.JSONField(default=list, verbose_name="Interactions")
    category = models.CharField(max_length=100, blank=True, verbose_name="Category")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        db_table = 'prescription_drugs'
        verbose_name = 'Drug'
        verbose_name_plural = 'Drugs'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['name', 'generic_name']),
            models.Index(fields=['interactions'], name='idx_drugs_interactions'),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.strength})"
    
    def get_interactions_list(self):
        """Return a list of drug interactions."""
        return self.interactions if isinstance(self.interactions, list) else []
    
    def add_interaction(self, drug_id, interaction_type, description):
        """Add a drug interaction."""
        interactions = self.get_interactions_list()
        interactions.append({
            'drug_id': drug_id,
            'type': interaction_type,
            'description': description
        })
        self.interactions = interactions
        self.save()
    
    def get_full_name(self):
        """Return the full drug name with generic name if available."""
        if self.generic_name:
            return f"{self.name} ({self.generic_name})"
        return self.name


class Prescription(models.Model):
    """
    Prescription model for tracking patient prescriptions and medications.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    id = models.AutoField(primary_key=True, verbose_name="Prescription ID")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions', verbose_name="Patient")
    prescription_date = models.DateField(default=timezone.now, verbose_name="Prescription Date")
    diagnosis = models.TextField(verbose_name="Diagnosis")
    symptoms = models.TextField(blank=True, verbose_name="Symptoms")
    medications = models.JSONField(default=list, verbose_name="Medications")
    instructions = models.TextField(verbose_name="Instructions")
    follow_up_date = models.DateField(null=True, blank=True, verbose_name="Follow-up Date")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_prescriptions', verbose_name="Created By")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_prescriptions', verbose_name="Updated By")
    
    class Meta:
        db_table = 'prescription_prescriptions'
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'
        indexes = [
            models.Index(fields=['patient', 'prescription_date']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
            models.Index(fields=['prescription_date']),
            models.Index(fields=['medications'], name='idx_prescriptions_medications'),
            models.Index(fields=['patient', 'prescription_date'], name='idx_prescriptions_history'),
        ]
        ordering = ['-prescription_date']
    
    def __str__(self):
        return f"Prescription {self.id} for {self.patient.name}"
    
    def get_medications_list(self):
        """Return a list of medications."""
        return self.medications if isinstance(self.medications, list) else []
    
    def add_medication(self, medication):
        """Add a medication to the prescription."""
        medications = self.get_medications_list()
        medications.append(medication)
        self.medications = medications
        self.save()
    
    def is_active(self):
        """Check if the prescription is active."""
        return self.status == 'active'
    
    def is_expired(self):
        """Check if the prescription is expired."""
        if self.follow_up_date:
            return timezone.now().date() > self.follow_up_date
        return False
    
    def get_medications_count(self):
        """Return the number of medications in the prescription."""
        return len(self.get_medications_list())
    
    def get_drug_names(self):
        """Return a list of drug names in the prescription."""
        medications = self.get_medications_list()
        return [med.get('name', '') for med in medications if isinstance(med, dict)]


class Observation(models.Model):
    """
    Observation model for tracking medical observations and notes.
    """
    TYPE_CHOICES = [
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('routine', 'Routine'),
        ('surgery', 'Surgery'),
    ]
    
    id = models.AutoField(primary_key=True, verbose_name="Observation ID")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='observations', verbose_name="Patient")
    observation_date = models.DateField(default=timezone.now, verbose_name="Observation Date")
    observation_type = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="Observation Type")
    symptoms = models.TextField(blank=True, verbose_name="Symptoms")
    examination_findings = models.TextField(blank=True, verbose_name="Examination Findings")
    recommendations = models.TextField(blank=True, verbose_name="Recommendations")
    next_appointment = models.DateField(null=True, blank=True, verbose_name="Next Appointment")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_observations', verbose_name="Created By")
    
    class Meta:
        db_table = 'prescription_observations'
        verbose_name = 'Observation'
        verbose_name_plural = 'Observations'
        indexes = [
            models.Index(fields=['patient', 'observation_date']),
            models.Index(fields=['observation_type']),
            models.Index(fields=['created_by']),
            models.Index(fields=['observation_date']),
            models.Index(fields=['patient', 'observation_date'], name='idx_observations_timeline'),
        ]
        ordering = ['-observation_date']
    
    def __str__(self):
        return f"Observation {self.id} for {self.patient.name}"
    
    def get_type_display_name(self):
        """Return the display name for the observation type."""
        return dict(self.TYPE_CHOICES).get(self.observation_type, self.observation_type)


class PrescriptionTemplate(models.Model):
    """
    Prescription template model for common prescription protocols.
    """
    name = models.CharField(max_length=200, verbose_name="Template Name")
    description = models.TextField(blank=True, verbose_name="Description")
    diagnosis = models.TextField(verbose_name="Associated Diagnosis")
    medications = models.JSONField(default=list, verbose_name="Template Medications")
    instructions = models.TextField(verbose_name="Template Instructions")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates', verbose_name="Created By")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_templates', verbose_name="Updated By")
    
    class Meta:
        db_table = 'prescription_templates'
        verbose_name = 'Prescription Template'
        verbose_name_plural = 'Prescription Templates'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_by']),
            models.Index(fields=['medications'], name='idx_templates_medications'),
        ]
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_medications_list(self):
        """Return a list of template medications."""
        return self.medications if isinstance(self.medications, list) else []
    
    def apply_to_patient(self, patient_uid):
        """Apply template to create a new prescription for a patient."""
        prescription_data = {
            'patient_uid': patient_uid,
            'diagnosis': self.diagnosis,
            'medications': self.get_medications_list(),
            'instructions': self.instructions
        }
        return prescription_data
    
    def get_medications_count(self):
        """Return the number of medications in the template."""
        return len(self.get_medications_list())


class DrugInteraction(models.Model):
    """
    Drug interaction model for tracking drug-drug interactions.
    """
    INTERACTION_TYPES = [
        ('contraindicated', 'Contraindicated'),
        ('major', 'Major'),
        ('moderate', 'Moderate'),
        ('minor', 'Minor'),
    ]
    
    SEVERITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    id = models.AutoField(primary_key=True, verbose_name="Interaction ID")
    drug1 = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_drug1', verbose_name="First Drug")
    drug2 = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_drug2', verbose_name="Second Drug")
    interaction_type = models.CharField(max_length=50, choices=INTERACTION_TYPES, verbose_name="Interaction Type")
    description = models.TextField(verbose_name="Interaction Description")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name="Severity")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        db_table = 'prescription_drug_interactions'
        verbose_name = 'Drug Interaction'
        verbose_name_plural = 'Drug Interactions'
        unique_together = ['drug1', 'drug2']
        indexes = [
            models.Index(fields=['drug1']),
            models.Index(fields=['drug2']),
            models.Index(fields=['interaction_type']),
            models.Index(fields=['severity']),
        ]
        ordering = ['drug1__name', 'drug2__name']
    
    def __str__(self):
        return f"{self.drug1.name} + {self.drug2.name} ({self.interaction_type})"
    
    def get_severity_color(self):
        """Return a color code for the severity level."""
        colors = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'info'
        }
        return colors.get(self.severity, 'secondary')


class PrescriptionAuditTrail(models.Model):
    """
    Audit trail model for tracking all changes to prescription data.
    """
    ACTION_CHOICES = [
        ('INSERT', 'Insert'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]
    
    id = models.AutoField(primary_key=True, verbose_name="Audit ID")
    table_name = models.CharField(max_length=50, verbose_name="Table Name")
    record_id = models.CharField(max_length=50, verbose_name="Record ID")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action")
    old_values = models.JSONField(null=True, blank=True, verbose_name="Old Values")
    new_values = models.JSONField(null=True, blank=True, verbose_name="New Values")
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_changes', verbose_name="Changed By")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Changed At")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    
    class Meta:
        db_table = 'prescription_audit_trail'
        verbose_name = 'Audit Trail'
        verbose_name_plural = 'Audit Trails'
        indexes = [
            models.Index(fields=['table_name']),
            models.Index(fields=['record_id']),
            models.Index(fields=['action']),
            models.Index(fields=['changed_by']),
            models.Index(fields=['changed_at']),
        ]
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.action} on {self.table_name}.{self.record_id} by {self.changed_by.username}"
    
    def get_action_display_name(self):
        """Return the display name for the action."""
        return dict(self.ACTION_CHOICES).get(self.action, self.action)
    
    def get_changes_summary(self):
        """Return a summary of the changes made."""
        if self.action == 'INSERT':
            return f"Created new {self.table_name} record"
        elif self.action == 'UPDATE':
            return f"Updated {self.table_name} record"
        elif self.action == 'DELETE':
            return f"Deleted {self.table_name} record"
        return f"Modified {self.table_name} record"