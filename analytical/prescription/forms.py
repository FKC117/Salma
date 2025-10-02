"""
Forms for prescription management system

This module contains all Django forms for the prescription management system,
including patient forms, prescription forms, and validation forms.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import Patient, PatientProfile, Prescription, Observation, Drug

User = get_user_model()


class PatientForm(forms.ModelForm):
    """Form for creating and editing patients."""
    
    class Meta:
        model = Patient
        fields = [
            'uid', 'name', 'age', 'gender', 'phone', 'email', 'address',
            'emergency_contact', 'emergency_phone'
        ]
        widgets = {
            'uid': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unique patient ID (e.g., P001)'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '150'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter emergency contact name'
            }),
            'emergency_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter emergency contact phone'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['uid'].required = True
        self.fields['name'].required = True
        self.fields['age'].required = True
        self.fields['gender'].required = True
        self.fields['phone'].required = True


class PatientProfileForm(forms.ModelForm):
    """Form for editing patient medical profiles."""
    
    class Meta:
        model = PatientProfile
        fields = [
            'medical_history', 'allergies', 'current_medications',
            'vital_signs', 'lab_results', 'notes'
        ]
        widgets = {
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter medical history'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter allergies (comma-separated)'
            }),
            'current_medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter current medications (comma-separated)'
            }),
            'vital_signs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter vital signs (JSON format)'
            }),
            'lab_results': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter lab results (JSON format)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter additional notes'
            }),
        }


class PrescriptionForm(forms.ModelForm):
    """Form for creating and editing prescriptions."""
    
    class Meta:
        model = Prescription
        fields = [
            'patient', 'diagnosis', 'symptoms', 'instructions', 'follow_up_date'
        ]
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-control'
            }),
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter diagnosis'
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter symptoms'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter prescription instructions'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].required = True
        self.fields['diagnosis'].required = True
        self.fields['instructions'].required = True


class ObservationForm(forms.ModelForm):
    """Form for creating and editing observations."""
    
    class Meta:
        model = Observation
        fields = [
            'patient', 'observation_type', 'symptoms', 'examination_findings',
            'recommendations', 'next_appointment'
        ]
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-control'
            }),
            'observation_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter symptoms'
            }),
            'examination_findings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter examination findings'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter recommendations'
            }),
            'next_appointment': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].required = True
        self.fields['observation_type'].required = True


class DrugForm(forms.ModelForm):
    """Form for creating and editing drugs."""
    
    class Meta:
        model = Drug
        fields = [
            'name', 'generic_name', 'dosage_form', 'strength', 'indications',
            'contraindications', 'side_effects', 'category'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter drug name'
            }),
            'generic_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter generic name'
            }),
            'dosage_form': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter dosage form (e.g., Tablet, Injection)'
            }),
            'strength': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter strength (e.g., 20mg)'
            }),
            'indications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter indications'
            }),
            'contraindications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter contraindications'
            }),
            'side_effects': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter side effects'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter drug category'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['dosage_form'].required = True
        self.fields['strength'].required = True


class MedicationForm(forms.Form):
    """Form for adding medications to prescriptions."""
    
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Medication name'
        })
    )
    dosage = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dosage (e.g., 20mg)'
        })
    )
    frequency = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Frequency (e.g., daily, twice daily)'
        })
    )
    duration = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Duration (e.g., 5 years, 30 days)'
        })
    )
