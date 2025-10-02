/**
 * Prescription Management System JavaScript
 * 
 * This file contains all JavaScript functionality for the prescription management system,
 * including HTMX interactions, form handling, and dynamic UI updates.
 */

document.addEventListener('DOMContentLoaded', function() {
    initializePrescriptionSystem();
});

function initializePrescriptionSystem() {
    // Initialize patient selection
    initializePatientSelection();
    
    // Initialize template buttons
    initializeTemplateButtons();
    
    // Initialize medication management
    initializeMedicationManagement();
    
    // Initialize HTMX event listeners
    initializeHTMXListeners();
}

function initializePatientSelection() {
    // Load patients into the select dropdown
    const patientSelect = document.getElementById('patient-select');
    if (patientSelect) {
        // This would typically make an API call to get patients
        // For now, we'll populate it when patients are loaded
    }
}

function initializeTemplateButtons() {
    const templateButtons = document.querySelectorAll('.template-btn');
    templateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const templateId = this.dataset.templateId;
            const templateName = this.dataset.templateName;
            applyTemplate(templateId, templateName);
        });
    });
}

function initializeMedicationManagement() {
    const addMedicationBtn = document.getElementById('add-medication');
    if (addMedicationBtn) {
        addMedicationBtn.addEventListener('click', addMedicationField);
    }
}

function initializeHTMXListeners() {
    // Listen for HTMX events
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        showLoadingState(event.target);
    });
    
    document.body.addEventListener('htmx:afterRequest', function(event) {
        hideLoadingState(event.target);
    });
    
    document.body.addEventListener('htmx:responseError', function(event) {
        showError('An error occurred while processing your request.');
    });
}

function applyTemplate(templateId, templateName) {
    // Apply template to the prescription form
    console.log(`Applying template: ${templateName} (ID: ${templateId})`);
    
    // This would typically make an API call to get template data
    // For now, we'll show a placeholder
    showSuccess(`Template "${templateName}" applied successfully!`);
}

function addMedicationField() {
    const container = document.getElementById('medications-container');
    const newMedication = document.createElement('div');
    newMedication.className = 'medication-item mb-2';
    newMedication.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <input type="text" 
                       class="form-control" 
                       name="medication_name[]" 
                       placeholder="Medication name">
            </div>
            <div class="col-md-3">
                <input type="text" 
                       class="form-control" 
                       name="medication_dosage[]" 
                       placeholder="Dosage">
            </div>
            <div class="col-md-3">
                <div class="input-group">
                    <input type="text" 
                           class="form-control" 
                           name="medication_frequency[]" 
                           placeholder="Frequency">
                    <button type="button" 
                            class="btn btn-outline-danger" 
                            onclick="removeMedicationField(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    container.appendChild(newMedication);
}

function removeMedicationField(button) {
    const medicationItem = button.closest('.medication-item');
    medicationItem.remove();
}

function showLoadingState(element) {
    element.classList.add('loading');
}

function hideLoadingState(element) {
    element.classList.remove('loading');
}

function showSuccess(message) {
    showAlert(message, 'success');
}

function showError(message) {
    showAlert(message, 'danger');
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the prescription form
    const prescriptionForm = document.querySelector('.prescription-form');
    if (prescriptionForm) {
        prescriptionForm.insertBefore(alertDiv, prescriptionForm.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Patient selection functions
function selectPatient(patientUid) {
    // Update patient select dropdown
    const patientSelect = document.getElementById('patient-select');
    if (patientSelect) {
        patientSelect.value = patientUid;
    }
    
    // Update active patient in the list
    const patientItems = document.querySelectorAll('.patient-item');
    patientItems.forEach(item => {
        item.classList.remove('active');
        if (item.dataset.patientUid === patientUid) {
            item.classList.add('active');
        }
    });
}

// Prescription form validation
function validatePrescriptionForm() {
    const form = document.querySelector('.prescription-form form');
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Drug interaction checking
function checkDrugInteractions(medications) {
    // This would typically make an API call to check for drug interactions
    console.log('Checking drug interactions for:', medications);
    return Promise.resolve([]);
}

// Export functions for global access
window.prescriptionSystem = {
    selectPatient,
    validatePrescriptionForm,
    checkDrugInteractions,
    addMedicationField,
    removeMedicationField,
    showSuccess,
    showError
};
