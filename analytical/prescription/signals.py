"""
Signals for prescription management system

This module contains Django signals for automatic audit trail logging
and other automated tasks in the prescription management system.
"""

import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Patient, PatientProfile, Prescription, Observation,
    Drug, PrescriptionTemplate, DrugInteraction, PrescriptionAuditTrail
)

User = get_user_model()
logger = logging.getLogger('prescription')

# Store original values for audit trail
_original_values = {}


@receiver(pre_save)
def store_original_values(sender, **kwargs):
    """Store original values before saving for audit trail."""
    instance = kwargs['instance']
    if sender in [Patient, PatientProfile, Prescription, Observation, Drug, PrescriptionTemplate, DrugInteraction]:
        try:
            if instance.pk:
                original = sender.objects.get(pk=instance.pk)
                _original_values[instance.pk] = {
                    'model': sender.__name__,
                    'values': {
                        field.name: getattr(original, field.name)
                        for field in original._meta.fields
                    }
                }
        except sender.DoesNotExist:
            pass


@receiver(post_save)
def log_model_changes(sender, **kwargs):
    """Log model changes to audit trail."""
    instance = kwargs['instance']
    created = kwargs['created']
    
    if sender in [Patient, PatientProfile, Prescription, Observation, Drug, PrescriptionTemplate, DrugInteraction]:
        action = 'INSERT' if created else 'UPDATE'
        
        # Get the user who made the change (if available)
        user = getattr(instance, 'created_by', None) or getattr(instance, 'updated_by', None)
        if not user and hasattr(instance, '_request_user'):
            user = instance._request_user
        
        # Get old values for updates
        old_values = None
        if not created and instance.pk in _original_values:
            old_values = _original_values[instance.pk]['values']
            # Convert datetime objects to strings for JSON serialization
            for key, value in old_values.items():
                if hasattr(value, 'isoformat'):
                    old_values[key] = value.isoformat()
            del _original_values[instance.pk]
        
        # Get new values
        new_values = {}
        for field in instance._meta.fields:
            value = getattr(instance, field.name)
            # Convert datetime objects to strings for JSON serialization
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            new_values[field.name] = value
        
        # Create audit trail entry
        try:
            PrescriptionAuditTrail.objects.create(
                table_name=sender.__name__.lower(),
                record_id=str(instance.pk),
                action=action,
                old_values=old_values,
                new_values=new_values,
                changed_by=user,
                changed_at=timezone.now()
            )
            
            logger.info(f"Audit trail created: {action} on {sender.__name__}.{instance.pk}")
            
        except Exception as e:
            logger.error(f"Failed to create audit trail: {str(e)}")


@receiver(post_delete)
def log_model_deletions(sender, **kwargs):
    """Log model deletions to audit trail."""
    instance = kwargs['instance']
    
    if sender in [Patient, PatientProfile, Prescription, Observation, Drug, PrescriptionTemplate, DrugInteraction]:
        # Get the user who made the change (if available)
        user = getattr(instance, 'created_by', None) or getattr(instance, 'updated_by', None)
        if not user and hasattr(instance, '_request_user'):
            user = instance._request_user
        
        # Get old values
        old_values = {}
        for field in instance._meta.fields:
            value = getattr(instance, field.name)
            # Convert datetime objects to strings for JSON serialization
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            old_values[field.name] = value
        
        # Create audit trail entry
        try:
            PrescriptionAuditTrail.objects.create(
                table_name=sender.__name__.lower(),
                record_id=str(instance.pk),
                action='DELETE',
                old_values=old_values,
                new_values=None,
                changed_by=user,
                changed_at=timezone.now()
            )
            
            logger.info(f"Audit trail created: DELETE on {sender.__name__}.{instance.pk}")
            
        except Exception as e:
            logger.error(f"Failed to create audit trail: {str(e)}")


@receiver(post_save, sender=Patient)
def create_patient_profile(sender, instance, created, **kwargs):
    """Automatically create a patient profile when a patient is created."""
    if created:
        try:
            PatientProfile.objects.create(
                patient=instance,
                created_by=getattr(instance, 'created_by', None)
            )
            logger.info(f"Patient profile created for patient {instance.uid}")
        except Exception as e:
            logger.error(f"Failed to create patient profile for {instance.uid}: {str(e)}")


@receiver(post_save, sender=Prescription)
def log_prescription_creation(sender, instance, created, **kwargs):
    """Log prescription creation with additional details."""
    if created:
        logger.info(f"New prescription created: ID {instance.id} for patient {instance.patient.uid}")
        
        # Log medication details
        medications = instance.get_medications_list()
        if medications:
            medication_names = [med.get('name', 'Unknown') for med in medications if isinstance(med, dict)]
            logger.info(f"Prescription {instance.id} contains medications: {', '.join(medication_names)}")


@receiver(post_save, sender=DrugInteraction)
def log_drug_interaction_creation(sender, instance, created, **kwargs):
    """Log drug interaction creation."""
    if created:
        logger.warning(f"Drug interaction created: {instance.drug1.name} + {instance.drug2.name} ({instance.interaction_type})")


# Custom signal for prescription validation
from django.dispatch import Signal

prescription_validated = Signal()

@receiver(prescription_validated)
def log_prescription_validation(sender, prescription, valid, errors, warnings, **kwargs):
    """Log prescription validation results."""
    if valid:
        logger.info(f"Prescription {prescription.id} validation passed")
    else:
        logger.warning(f"Prescription {prescription.id} validation failed: {errors}")
    
    if warnings:
        logger.warning(f"Prescription {prescription.id} validation warnings: {warnings}")


# Signal for drug interaction checking
drug_interaction_checked = Signal()

@receiver(drug_interaction_checked)
def log_drug_interaction_check(sender, medications, interactions, **kwargs):
    """Log drug interaction checking results."""
    if interactions:
        interaction_count = len(interactions)
        logger.warning(f"Drug interaction check found {interaction_count} interactions")
        
        for interaction in interactions:
            logger.warning(f"Interaction: {interaction.get('drug1')} + {interaction.get('drug2')} - {interaction.get('type')}")
    else:
        logger.info("Drug interaction check completed - no interactions found")
