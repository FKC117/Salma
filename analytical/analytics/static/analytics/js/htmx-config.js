// HTMX Configuration and Error Prevention (T009)
// This file configures HTMX for optimal performance and error handling

document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX defaults
    htmx.config.defaultSwapStyle = 'innerHTML';
    htmx.config.defaultSwapDelay = 0;
    htmx.config.defaultSettleDelay = 100;
    htmx.config.includeIndicatorStyles = true;
    htmx.config.indicatorClass = 'htmx-indicator';
    htmx.config.requestClass = 'htmx-request';
    htmx.config.settlingClass = 'htmx-settling';
    htmx.config.swappingClass = 'htmx-swapping';
    
    // Global error handling
    document.body.addEventListener('htmx:responseError', function(evt) {
        console.error('HTMX Response Error:', evt.detail);
        showNotification('An error occurred while processing your request. Please try again.', 'error');
    });
    
    document.body.addEventListener('htmx:sendError', function(evt) {
        console.error('HTMX Send Error:', evt.detail);
        showNotification('Failed to send request. Please check your connection.', 'error');
    });
    
    document.body.addEventListener('htmx:timeout', function(evt) {
        console.error('HTMX Timeout:', evt.detail);
        showNotification('Request timed out. Please try again.', 'warning');
    });
    
    // Target error prevention
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        const target = evt.target.getAttribute('hx-target');
        if (target && target !== 'this') {
            const targetElement = document.querySelector(target);
            if (!targetElement) {
                console.warn('HTMX Target not found:', target);
                evt.preventDefault();
                showNotification('Target element not found. Please refresh the page.', 'error');
                return;
            }
        }
    });
    
    // Loading states
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        // Show loading indicator
        const indicator = evt.target.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
        
        // Disable form elements during request
        const formElements = evt.target.querySelectorAll('input, button, select, textarea');
        formElements.forEach(element => {
            element.disabled = true;
        });
    });
    
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        // Hide loading indicator
        const indicator = evt.target.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
        
        // Re-enable form elements
        const formElements = evt.target.querySelectorAll('input, button, select, textarea');
        formElements.forEach(element => {
            element.disabled = false;
        });
    });
    
    // Success handling
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        if (evt.detail.xhr.status >= 200 && evt.detail.xhr.status < 300) {
            // Check for success messages in response
            const response = evt.detail.xhr.responseText;
            if (response.includes('success') || response.includes('Success')) {
                showNotification('Operation completed successfully!', 'success');
            }
        }
    });
    
    // CSRF token handling
    document.body.addEventListener('htmx:configRequest', function(evt) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            evt.detail.headers['X-CSRFToken'] = csrfToken.value;
        }
    });
    
    // File upload progress
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        if (evt.target.hasAttribute('hx-post') && evt.target.querySelector('input[type="file"]')) {
            showNotification('Uploading file...', 'info');
        }
    });
    
    // Prevent multiple submissions
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        if (evt.target.classList.contains('htmx-request')) {
            evt.preventDefault();
            return;
        }
    });
});

// Notification system for HTMX errors
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 1050;
        min-width: 300px;
        max-width: 500px;
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${getIconForType(type)} me-2"></i>
            <span>${message}</span>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 150);
        }
    }, 5000);
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// HTMX validation helpers
function validateHTMXTarget(target) {
    if (!target) return true;
    const element = document.querySelector(target);
    return element !== null;
}

function validateHTMXSwap(swap) {
    const validSwaps = ['innerHTML', 'outerHTML', 'beforebegin', 'afterbegin', 'beforeend', 'afterend'];
    return validSwaps.includes(swap);
}

// Export for global use
window.htmxConfig = {
    showNotification,
    validateHTMXTarget,
    validateHTMXSwap
};
