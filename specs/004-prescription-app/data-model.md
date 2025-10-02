# Data Model: Prescription Management System

## Overview

This document defines the complete data model for the Prescription Management System, including all database tables, relationships, constraints, and business rules. The model is designed to support comprehensive patient management, prescription tracking, and medical history maintenance.

## Database Schema

### Core Tables

#### Patients Table
```sql
CREATE TABLE patients (
    uid VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 0 AND age <= 150),
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('M', 'F', 'Other')),
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    emergency_contact VARCHAR(100),
    emergency_phone VARCHAR(15),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id),
    updated_by_id INTEGER REFERENCES auth_user(id)
);

-- Indexes for performance
CREATE INDEX idx_patients_name ON patients(name);
CREATE INDEX idx_patients_phone ON patients(phone);
CREATE INDEX idx_patients_email ON patients(email);
CREATE INDEX idx_patients_created_at ON patients(created_at);
CREATE INDEX idx_patients_search ON patients(name, phone, uid);
```

#### Patient Profiles Table
```sql
CREATE TABLE patient_profiles (
    id SERIAL PRIMARY KEY,
    patient_uid VARCHAR(20) REFERENCES patients(uid) ON DELETE CASCADE,
    medical_history TEXT,
    allergies TEXT,
    current_medications TEXT,
    vital_signs JSONB DEFAULT '{}',
    lab_results JSONB DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id),
    updated_by_id INTEGER REFERENCES auth_user(id),
    UNIQUE(patient_uid)
);

-- Indexes
CREATE INDEX idx_patient_profiles_patient ON patient_profiles(patient_uid);
CREATE INDEX idx_patient_profiles_vital_signs ON patient_profiles USING GIN(vital_signs);
CREATE INDEX idx_patient_profiles_lab_results ON patient_profiles USING GIN(lab_results);
```

#### Prescriptions Table
```sql
CREATE TABLE prescriptions (
    id SERIAL PRIMARY KEY,
    patient_uid VARCHAR(20) REFERENCES patients(uid) ON DELETE CASCADE,
    prescription_date DATE NOT NULL DEFAULT CURRENT_DATE,
    diagnosis TEXT NOT NULL,
    symptoms TEXT,
    medications JSONB NOT NULL DEFAULT '[]',
    instructions TEXT NOT NULL,
    follow_up_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled', 'expired')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id),
    updated_by_id INTEGER REFERENCES auth_user(id)
);

-- Indexes
CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_uid);
CREATE INDEX idx_prescriptions_date ON prescriptions(prescription_date);
CREATE INDEX idx_prescriptions_status ON prescriptions(status);
CREATE INDEX idx_prescriptions_created_by ON prescriptions(created_by_id);
CREATE INDEX idx_prescriptions_medications ON prescriptions USING GIN(medications);
CREATE INDEX idx_prescriptions_history ON prescriptions(patient_uid, prescription_date DESC);
```

#### Observations Table
```sql
CREATE TABLE observations (
    id SERIAL PRIMARY KEY,
    patient_uid VARCHAR(20) REFERENCES patients(uid) ON DELETE CASCADE,
    observation_date DATE NOT NULL DEFAULT CURRENT_DATE,
    observation_type VARCHAR(50) NOT NULL CHECK (observation_type IN ('consultation', 'follow_up', 'emergency', 'routine', 'surgery')),
    symptoms TEXT,
    examination_findings TEXT,
    recommendations TEXT,
    next_appointment DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id)
);

-- Indexes
CREATE INDEX idx_observations_patient ON observations(patient_uid);
CREATE INDEX idx_observations_date ON observations(observation_date);
CREATE INDEX idx_observations_type ON observations(observation_type);
CREATE INDEX idx_observations_created_by ON observations(created_by_id);
CREATE INDEX idx_observations_timeline ON observations(patient_uid, observation_date DESC);
```

#### Drugs Table
```sql
CREATE TABLE drugs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    dosage_form VARCHAR(50) NOT NULL,
    strength VARCHAR(50) NOT NULL,
    indications TEXT,
    contraindications TEXT,
    side_effects TEXT,
    interactions JSONB DEFAULT '[]',
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_drugs_name ON drugs(name);
CREATE INDEX idx_drugs_generic_name ON drugs(generic_name);
CREATE INDEX idx_drugs_category ON drugs(category);
CREATE INDEX idx_drugs_active ON drugs(is_active);
CREATE INDEX idx_drugs_interactions ON drugs USING GIN(interactions);
CREATE INDEX idx_drugs_search ON drugs(name, generic_name);
```

#### Prescription Templates Table
```sql
CREATE TABLE prescription_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    diagnosis TEXT NOT NULL,
    medications JSONB NOT NULL DEFAULT '[]',
    instructions TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id),
    updated_by_id INTEGER REFERENCES auth_user(id)
);

-- Indexes
CREATE INDEX idx_templates_name ON prescription_templates(name);
CREATE INDEX idx_templates_active ON prescription_templates(is_active);
CREATE INDEX idx_templates_created_by ON prescription_templates(created_by_id);
CREATE INDEX idx_templates_medications ON prescription_templates USING GIN(medications);
```

#### Drug Interactions Table
```sql
CREATE TABLE drug_interactions (
    id SERIAL PRIMARY KEY,
    drug1_id INTEGER REFERENCES drugs(id) ON DELETE CASCADE,
    drug2_id INTEGER REFERENCES drugs(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL CHECK (interaction_type IN ('contraindicated', 'major', 'moderate', 'minor')),
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(drug1_id, drug2_id)
);

-- Indexes
CREATE INDEX idx_interactions_drug1 ON drug_interactions(drug1_id);
CREATE INDEX idx_interactions_drug2 ON drug_interactions(drug2_id);
CREATE INDEX idx_interactions_type ON drug_interactions(interaction_type);
CREATE INDEX idx_interactions_severity ON drug_interactions(severity);
```

#### Audit Trail Table
```sql
CREATE TABLE prescription_audit_trail (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    changed_by_id INTEGER REFERENCES auth_user(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Indexes
CREATE INDEX idx_audit_table ON prescription_audit_trail(table_name);
CREATE INDEX idx_audit_record ON prescription_audit_trail(record_id);
CREATE INDEX idx_audit_action ON prescription_audit_trail(action);
CREATE INDEX idx_audit_changed_by ON prescription_audit_trail(changed_by_id);
CREATE INDEX idx_audit_changed_at ON prescription_audit_trail(changed_at);
```

## Django Models

### Patient Models
```python
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('Other', 'Other'),
    ]
    
    uid = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(150)]
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_patients')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_patients')
    
    class Meta:
        db_table = 'patients'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.uid} - {self.name}"
    
    def get_full_name(self):
        return self.name
    
    def get_age_group(self):
        if self.age < 18:
            return 'Pediatric'
        elif self.age < 65:
            return 'Adult'
        else:
            return 'Geriatric'

class PatientProfile(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='profile')
    medical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    vital_signs = models.JSONField(default=dict)
    lab_results = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_profiles')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_profiles')
    
    class Meta:
        db_table = 'patient_profiles'
    
    def __str__(self):
        return f"Profile for {self.patient.name}"
    
    def get_allergies_list(self):
        if self.allergies:
            return [allergy.strip() for allergy in self.allergies.split(',')]
        return []
    
    def get_current_medications_list(self):
        if self.current_medications:
            return [med.strip() for med in self.current_medications.split(',')]
        return []
```

### Prescription Models
```python
class Prescription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    prescription_date = models.DateField()
    diagnosis = models.TextField()
    symptoms = models.TextField(blank=True)
    medications = models.JSONField(default=list)
    instructions = models.TextField()
    follow_up_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_prescriptions')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_prescriptions')
    
    class Meta:
        db_table = 'prescriptions'
        indexes = [
            models.Index(fields=['patient', 'prescription_date']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
        ]
        ordering = ['-prescription_date']
    
    def __str__(self):
        return f"Prescription {self.id} for {self.patient.name}"
    
    def get_medications_list(self):
        return self.medications if isinstance(self.medications, list) else []
    
    def add_medication(self, medication):
        medications = self.get_medications_list()
        medications.append(medication)
        self.medications = medications
        self.save()
    
    def is_active(self):
        return self.status == 'active'
    
    def is_expired(self):
        if self.follow_up_date:
            from django.utils import timezone
            return timezone.now().date() > self.follow_up_date
        return False

class Observation(models.Model):
    TYPE_CHOICES = [
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('routine', 'Routine'),
        ('surgery', 'Surgery'),
    ]
    
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='observations')
    observation_date = models.DateField()
    observation_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    symptoms = models.TextField(blank=True)
    examination_findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    next_appointment = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_observations')
    
    class Meta:
        db_table = 'observations'
        indexes = [
            models.Index(fields=['patient', 'observation_date']),
            models.Index(fields=['observation_type']),
            models.Index(fields=['created_by']),
        ]
        ordering = ['-observation_date']
    
    def __str__(self):
        return f"Observation {self.id} for {self.patient.name}"
```

### Drug Models
```python
class Drug(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    dosage_form = models.CharField(max_length=50)
    strength = models.CharField(max_length=50)
    indications = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    interactions = models.JSONField(default=list)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drugs'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.strength})"
    
    def get_interactions_list(self):
        return self.interactions if isinstance(self.interactions, list) else []
    
    def add_interaction(self, drug_id, interaction_type, description):
        interactions = self.get_interactions_list()
        interactions.append({
            'drug_id': drug_id,
            'type': interaction_type,
            'description': description
        })
        self.interactions = interactions
        self.save()

class PrescriptionTemplate(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    diagnosis = models.TextField()
    medications = models.JSONField(default=list)
    instructions = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_templates')
    
    class Meta:
        db_table = 'prescription_templates'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_medications_list(self):
        return self.medications if isinstance(self.medications, list) else []
    
    def apply_to_patient(self, patient_uid):
        """Apply template to create a new prescription for a patient"""
        prescription_data = {
            'patient_uid': patient_uid,
            'diagnosis': self.diagnosis,
            'medications': self.get_medications_list(),
            'instructions': self.instructions
        }
        return prescription_data

class DrugInteraction(models.Model):
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
    
    id = models.AutoField(primary_key=True)
    drug1 = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_drug1')
    drug2 = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_drug2')
    interaction_type = models.CharField(max_length=50, choices=INTERACTION_TYPES)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'drug_interactions'
        unique_together = ['drug1', 'drug2']
        indexes = [
            models.Index(fields=['drug1']),
            models.Index(fields=['drug2']),
            models.Index(fields=['interaction_type']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        return f"{self.drug1.name} + {self.drug2.name} ({self.interaction_type})"
```

### Audit Trail Model
```python
class PrescriptionAuditTrail(models.Model):
    ACTION_CHOICES = [
        ('INSERT', 'Insert'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]
    
    id = models.AutoField(primary_key=True)
    table_name = models.CharField(max_length=50)
    record_id = models.CharField(max_length=50)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_changes')
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'prescription_audit_trail'
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
```

## Business Rules and Constraints

### Patient Management Rules
1. **UID Uniqueness**: Each patient must have a unique UID
2. **Required Fields**: Name, age, gender, and phone are required
3. **Age Validation**: Age must be between 0 and 150
4. **Phone Format**: Phone numbers must be valid format
5. **Email Validation**: Email addresses must be valid format
6. **Emergency Contact**: Emergency contact information is recommended

### Prescription Rules
1. **Patient Association**: Each prescription must be associated with a patient
2. **Required Fields**: Diagnosis and instructions are required
3. **Medication Format**: Medications must be in valid JSON format
4. **Status Validation**: Status must be one of the defined choices
5. **Date Validation**: Prescription date cannot be in the future
6. **Follow-up Date**: Follow-up date must be after prescription date

### Drug Interaction Rules
1. **Unique Interactions**: Each drug pair can only have one interaction record
2. **Severity Levels**: Severity must be high, medium, or low
3. **Interaction Types**: Must be contraindicated, major, moderate, or minor
4. **Active Drugs**: Only active drugs can have interactions

### Audit Trail Rules
1. **Complete Logging**: All data changes must be logged
2. **User Tracking**: All changes must be tracked to a user
3. **Timestamp**: All changes must have accurate timestamps
4. **IP Tracking**: IP addresses should be logged for security
5. **Data Integrity**: Audit trail data must be immutable

## Data Relationships

### Primary Relationships
- **Patient → PatientProfile**: One-to-One relationship
- **Patient → Prescriptions**: One-to-Many relationship
- **Patient → Observations**: One-to-Many relationship
- **User → Patients**: One-to-Many (created_by/updated_by)
- **User → Prescriptions**: One-to-Many (created_by/updated_by)
- **User → Observations**: One-to-Many (created_by)
- **User → Templates**: One-to-Many (created_by/updated_by)

### Secondary Relationships
- **Drug → DrugInteraction**: One-to-Many (drug1 and drug2)
- **Prescription → Medications**: JSON field containing drug references
- **Template → Medications**: JSON field containing drug references
- **Profile → Vital Signs**: JSON field for flexible vital signs storage
- **Profile → Lab Results**: JSON field for flexible lab results storage

## Performance Considerations

### Indexing Strategy
1. **Primary Keys**: All tables have primary key indexes
2. **Foreign Keys**: All foreign keys have indexes
3. **Search Fields**: Name, phone, email fields have indexes
4. **Date Fields**: Date fields have indexes for sorting
5. **JSON Fields**: GIN indexes on JSON fields for efficient querying
6. **Composite Indexes**: Multi-column indexes for common query patterns

### Query Optimization
1. **Select Related**: Use select_related for foreign key relationships
2. **Prefetch Related**: Use prefetch_related for reverse foreign key relationships
3. **Database Views**: Consider views for complex queries
4. **Materialized Views**: Consider materialized views for expensive aggregations
5. **Partitioning**: Consider table partitioning for large datasets

### Caching Strategy
1. **Patient Data**: Cache frequently accessed patient data
2. **Drug Information**: Cache drug database information
3. **Templates**: Cache prescription templates
4. **Interactions**: Cache drug interaction data
5. **Session Data**: Cache user session data

## Security Considerations

### Data Protection
1. **Encryption**: Sensitive data encrypted at rest
2. **Access Control**: Role-based access control
3. **Audit Logging**: Complete audit trail for all changes
4. **Data Validation**: Comprehensive input validation
5. **SQL Injection**: Parameterized queries and ORM usage

### Privacy Protection
1. **HIPAA Compliance**: Follow HIPAA guidelines
2. **Data Minimization**: Store only necessary data
3. **Retention Policies**: Implement data retention policies
4. **Access Logging**: Log all data access
5. **Encryption**: Encrypt sensitive data in transit and at rest

## Conclusion

This data model provides a comprehensive foundation for the Prescription Management System, supporting all required functionality while maintaining data integrity, performance, and security. The model is designed to be scalable, maintainable, and compliant with medical software standards.

Key features of the model include:

1. **Comprehensive Patient Management**: Complete patient information and medical history
2. **Flexible Prescription System**: Support for various prescription types and templates
3. **Drug Interaction Management**: Comprehensive drug interaction tracking
4. **Audit Trail**: Complete audit trail for compliance and security
5. **Performance Optimization**: Strategic indexing and query optimization
6. **Security**: Built-in security features and data protection
7. **Scalability**: Design supports future growth and expansion

The model follows Django best practices and PostgreSQL optimization techniques to ensure optimal performance and maintainability.
