"""
Management command to load sample data for prescription management system

This command creates sample patients, drugs, and prescription templates
for testing and development purposes.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from prescription.models import (
    Patient, PatientProfile, Drug, PrescriptionTemplate, 
    DrugInteraction, Prescription, Observation, PrescriptionAuditTrail
)
from django.utils import timezone
import random
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Load sample data for prescription management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading sample data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Loading sample data...')
        
        # Create sample users
        self.create_sample_users()
        
        # Create sample drugs
        self.create_sample_drugs()
        
        # Create sample patients
        self.create_sample_patients()
        
        # Create sample prescription templates
        self.create_sample_templates()
        
        # Create sample prescriptions
        self.create_sample_prescriptions()
        
        # Create sample observations
        self.create_sample_observations()
        
        # Create sample drug interactions
        self.create_sample_interactions()

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded sample data!')
        )

    def clear_data(self):
        """Clear existing sample data."""
        PrescriptionAuditTrail.objects.all().delete()
        Observation.objects.all().delete()
        Prescription.objects.all().delete()
        PrescriptionTemplate.objects.all().delete()
        DrugInteraction.objects.all().delete()
        PatientProfile.objects.all().delete()
        Patient.objects.all().delete()
        Drug.objects.all().delete()

    def create_sample_users(self):
        """Create sample users if they don't exist."""
        if not User.objects.filter(username='doctor1').exists():
            User.objects.create_user(
                username='doctor1',
                email='doctor1@example.com',
                password='password123',
                first_name='Dr. Sarah',
                last_name='Johnson'
            )
            self.stdout.write('Created sample user: doctor1')

        if not User.objects.filter(username='doctor2').exists():
            User.objects.create_user(
                username='doctor2',
                email='doctor2@example.com',
                password='password123',
                first_name='Dr. Michael',
                last_name='Smith'
            )
            self.stdout.write('Created sample user: doctor2')

    def create_sample_drugs(self):
        """Create sample drugs."""
        drugs_data = [
            {
                'name': 'Tamoxifen',
                'generic_name': 'Tamoxifen Citrate',
                'dosage_form': 'Tablet',
                'strength': '20mg',
                'indications': 'Treatment of breast cancer',
                'contraindications': 'Pregnancy, history of blood clots',
                'side_effects': 'Hot flashes, nausea, fatigue',
                'category': 'Antineoplastic'
            },
            {
                'name': 'Anastrozole',
                'generic_name': 'Anastrozole',
                'dosage_form': 'Tablet',
                'strength': '1mg',
                'indications': 'Treatment of breast cancer in postmenopausal women',
                'contraindications': 'Pregnancy, breastfeeding',
                'side_effects': 'Hot flashes, joint pain, osteoporosis',
                'category': 'Antineoplastic'
            },
            {
                'name': 'Letrozole',
                'generic_name': 'Letrozole',
                'dosage_form': 'Tablet',
                'strength': '2.5mg',
                'indications': 'Treatment of breast cancer in postmenopausal women',
                'contraindications': 'Pregnancy, breastfeeding',
                'side_effects': 'Hot flashes, bone pain, headache',
                'category': 'Antineoplastic'
            },
            {
                'name': 'Trastuzumab',
                'generic_name': 'Trastuzumab',
                'dosage_form': 'Injection',
                'strength': '440mg',
                'indications': 'Treatment of HER2-positive breast cancer',
                'contraindications': 'Severe heart failure',
                'side_effects': 'Heart problems, infusion reactions',
                'category': 'Monoclonal Antibody'
            },
            {
                'name': 'Pertuzumab',
                'generic_name': 'Pertuzumab',
                'dosage_form': 'Injection',
                'strength': '420mg',
                'indications': 'Treatment of HER2-positive breast cancer',
                'contraindications': 'Severe heart failure',
                'side_effects': 'Heart problems, diarrhea, fatigue',
                'category': 'Monoclonal Antibody'
            }
        ]

        for drug_data in drugs_data:
            drug, created = Drug.objects.get_or_create(
                name=drug_data['name'],
                defaults=drug_data
            )
            if created:
                self.stdout.write(f'Created drug: {drug.name}')

    def create_sample_patients(self):
        """Create sample patients."""
        patients_data = [
            {
                'uid': 'P001',
                'name': 'Sarah Williams',
                'age': 45,
                'gender': 'F',
                'phone': '+1234567890',
                'email': 'sarah.williams@email.com',
                'address': '123 Main St, City, State 12345',
                'emergency_contact': 'John Williams',
                'emergency_phone': '+1234567891'
            },
            {
                'uid': 'P002',
                'name': 'Maria Garcia',
                'age': 52,
                'gender': 'F',
                'phone': '+1234567892',
                'email': 'maria.garcia@email.com',
                'address': '456 Oak Ave, City, State 12345',
                'emergency_contact': 'Carlos Garcia',
                'emergency_phone': '+1234567893'
            },
            {
                'uid': 'P003',
                'name': 'Jennifer Brown',
                'age': 38,
                'gender': 'F',
                'phone': '+1234567894',
                'email': 'jennifer.brown@email.com',
                'address': '789 Pine St, City, State 12345',
                'emergency_contact': 'Robert Brown',
                'emergency_phone': '+1234567895'
            },
            {
                'uid': 'P004',
                'name': 'Lisa Davis',
                'age': 61,
                'gender': 'F',
                'phone': '+1234567896',
                'email': 'lisa.davis@email.com',
                'address': '321 Elm St, City, State 12345',
                'emergency_contact': 'David Davis',
                'emergency_phone': '+1234567897'
            },
            {
                'uid': 'P005',
                'name': 'Amanda Wilson',
                'age': 29,
                'gender': 'F',
                'phone': '+1234567898',
                'email': 'amanda.wilson@email.com',
                'address': '654 Maple Ave, City, State 12345',
                'emergency_contact': 'James Wilson',
                'emergency_phone': '+1234567899'
            }
        ]

        doctor1 = User.objects.get(username='doctor1')
        
        for patient_data in patients_data:
            patient, created = Patient.objects.get_or_create(
                uid=patient_data['uid'],
                defaults={
                    **patient_data,
                    'created_by': doctor1,
                    'updated_by': doctor1
                }
            )
            if created:
                # Save the patient first to ensure it exists in the database
                patient.save()
                
                # Create patient profile
                PatientProfile.objects.create(
                    patient=patient,
                    medical_history='Breast cancer diagnosis',
                    allergies='Penicillin',
                    current_medications='None',
                    created_by=doctor1,
                    updated_by=doctor1
                )
                self.stdout.write(f'Created patient: {patient.name} ({patient.uid})')

    def create_sample_templates(self):
        """Create sample prescription templates."""
        doctor1 = User.objects.get(username='doctor1')
        
        templates_data = [
            {
                'name': 'Tamoxifen Protocol',
                'description': 'Standard tamoxifen treatment protocol',
                'diagnosis': 'Hormone receptor-positive breast cancer',
                'medications': [
                    {
                        'name': 'Tamoxifen',
                        'dosage': '20mg',
                        'frequency': 'daily',
                        'duration': '5 years'
                    }
                ],
                'instructions': 'Take with food. Continue for 5 years as prescribed.'
            },
            {
                'name': 'Aromatase Inhibitor Protocol',
                'description': 'Standard aromatase inhibitor treatment',
                'diagnosis': 'Hormone receptor-positive breast cancer in postmenopausal women',
                'medications': [
                    {
                        'name': 'Anastrozole',
                        'dosage': '1mg',
                        'frequency': 'daily',
                        'duration': '5 years'
                    }
                ],
                'instructions': 'Take at the same time each day. Monitor bone density.'
            },
            {
                'name': 'HER2-Positive Protocol',
                'description': 'HER2-positive breast cancer treatment',
                'diagnosis': 'HER2-positive breast cancer',
                'medications': [
                    {
                        'name': 'Trastuzumab',
                        'dosage': '440mg',
                        'frequency': 'every 3 weeks',
                        'duration': '1 year'
                    },
                    {
                        'name': 'Pertuzumab',
                        'dosage': '420mg',
                        'frequency': 'every 3 weeks',
                        'duration': '1 year'
                    }
                ],
                'instructions': 'Administered by IV infusion. Monitor cardiac function.'
            }
        ]

        for template_data in templates_data:
            template, created = PrescriptionTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    **template_data,
                    'created_by': doctor1,
                    'updated_by': doctor1
                }
            )
            if created:
                self.stdout.write(f'Created template: {template.name}')

    def create_sample_prescriptions(self):
        """Create sample prescriptions."""
        doctor1 = User.objects.get(username='doctor1')
        patients = Patient.objects.all()
        
        if not patients.exists():
            self.stdout.write('No patients found. Please create patients first.')
            return

        for i, patient in enumerate(patients[:3]):  # Create prescriptions for first 3 patients
            prescription = Prescription.objects.create(
                patient=patient,
                prescription_date=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                diagnosis='Breast cancer',
                symptoms='Breast lump, nipple discharge',
                medications=[
                    {
                        'name': 'Tamoxifen',
                        'dosage': '20mg',
                        'frequency': 'daily',
                        'duration': '5 years'
                    }
                ],
                instructions='Take with food. Continue for 5 years as prescribed.',
                follow_up_date=timezone.now().date() + timedelta(days=90),
                status='active',
                created_by=doctor1,
                updated_by=doctor1
            )
            self.stdout.write(f'Created prescription {prescription.id} for {patient.name}')

    def create_sample_observations(self):
        """Create sample observations."""
        doctor1 = User.objects.get(username='doctor1')
        patients = Patient.objects.all()
        
        if not patients.exists():
            return

        for patient in patients[:2]:  # Create observations for first 2 patients
            observation = Observation.objects.create(
                patient=patient,
                observation_date=timezone.now().date() - timedelta(days=random.randint(1, 15)),
                observation_type='consultation',
                symptoms='Breast lump detected during self-examination',
                examination_findings='Palpable mass in upper outer quadrant of left breast',
                recommendations='Schedule mammogram and biopsy',
                next_appointment=timezone.now().date() + timedelta(days=7),
                created_by=doctor1
            )
            self.stdout.write(f'Created observation {observation.id} for {patient.name}')

    def create_sample_interactions(self):
        """Create sample drug interactions."""
        tamoxifen = Drug.objects.get(name='Tamoxifen')
        anastrozole = Drug.objects.get(name='Anastrozole')
        
        interaction, created = DrugInteraction.objects.get_or_create(
            drug1=tamoxifen,
            drug2=anastrozole,
            defaults={
                'interaction_type': 'major',
                'description': 'Concurrent use may reduce effectiveness of both drugs',
                'severity': 'high'
            }
        )
        if created:
            self.stdout.write(f'Created drug interaction: {tamoxifen.name} + {anastrozole.name}')
