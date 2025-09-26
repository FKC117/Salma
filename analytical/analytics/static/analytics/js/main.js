// Main JavaScript for Data Analysis System
// Note: This system uses HTMX for interactivity, minimal JS only for essential functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize HTMX indicators
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        // Show loading indicator
        const indicator = evt.target.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    });

    document.body.addEventListener('htmx:afterRequest', function(evt) {
        // Hide loading indicator
        const indicator = evt.target.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
        
        // Handle specific responses
        handleHTMXResponse(evt);
    });

    // Handle HTMX errors
    document.body.addEventListener('htmx:responseError', function(evt) {
        console.error('HTMX Error:', evt.detail);
        showNotification('An error occurred. Please try again.', 'error');
    });

    // Initialize dashboard functionality
    initializeDashboard();
});

// Handle HTMX responses
function handleHTMXResponse(evt) {
    const target = evt.detail.target;
    const response = evt.detail.xhr.response;
    
    try {
        const data = JSON.parse(response);
        
        // Handle upload success
        if (target.id === 'upload-status' && data.success) {
            updateDatasetInfo(data.data);
            showNotification('Dataset uploaded successfully!', 'success');
        }
        
        // Handle analysis results
        if (target.id === 'analysis-results' && data.success) {
            showNotification('Analysis completed!', 'success');
        }
        
        // Handle chat messages
        if (target.id === 'chat-messages') {
            scrollChatToBottom();
        }
        
        // Handle agent run
        if (target.id === 'agent-status' && data.agent_run_id) {
            startAgentProgressPolling(data.agent_run_id);
        }
        
    } catch (e) {
        // Handle non-JSON responses
        if (target.id === 'chat-messages') {
            scrollChatToBottom();
        }
    }
}

// Initialize dashboard functionality
function initializeDashboard() {
    // Panel resizing functionality
    initializePanelResizing();
    
    // File upload drag and drop
    initializeFileUpload();
    
    // Chat auto-scroll
    initializeChatScroll();
    
    // Tool interactions
    initializeToolInteractions();
}

// Panel Resizing Functionality
function initializePanelResizing() {
    const resizeHandles = document.querySelectorAll('.resize-handle');
    
    resizeHandles.forEach(handle => {
        let isResizing = false;
        
        handle.addEventListener('mousedown', function(e) {
            isResizing = true;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            
            const container = document.querySelector('.dashboard-container');
            const startX = e.clientX;
            const startWidths = Array.from(container.children)
                .filter(child => child.classList.contains('panel'))
                .map(panel => panel.offsetWidth);
            
            function handleMouseMove(e) {
                if (!isResizing) return;
                
                const deltaX = e.clientX - startX;
                const newWidths = [...startWidths];
                
                // Adjust panel widths based on resize handle
                const handleIndex = Array.from(container.children).indexOf(handle);
                if (handleIndex === 1) { // Between tools and dashboard
                    newWidths[0] = Math.max(200, Math.min(500, startWidths[0] + deltaX));
                    newWidths[1] = Math.max(300, startWidths[1] - deltaX);
                } else if (handleIndex === 3) { // Between dashboard and chat
                    newWidths[1] = Math.max(300, startWidths[1] + deltaX);
                    newWidths[2] = Math.max(250, Math.min(500, startWidths[2] - deltaX));
                }
                
                // Apply new widths
                const panels = Array.from(container.children)
                    .filter(child => child.classList.contains('panel'));
                
                panels.forEach((panel, index) => {
                    panel.style.width = newWidths[index] + 'px';
                });
            }
            
            function handleMouseUp() {
                isResizing = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            }
            
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        });
    });
}

function addResizeHandle(element, direction) {
    const handle = document.createElement('div');
    handle.className = `resize-handle resize-handle-${direction}`;
    handle.style.cssText = `
        width: 4px;
        background-color: #6c757d;
        cursor: col-resize;
        position: relative;
        z-index: 10;
    `;
    
    element.appendChild(handle);
    
    let isResizing = false;
    
    handle.addEventListener('mousedown', function(e) {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;
        
        // Update grid template columns
        const container = document.querySelector('.dashboard-container');
        const rect = container.getBoundingClientRect();
        const percentage = ((e.clientX - rect.left) / rect.width) * 100;
        
        if (direction === 'right') {
            container.style.gridTemplateColumns = `${percentage}% 1fr 350px`;
        }
    });
    
    document.addEventListener('mouseup', function() {
        isResizing = false;
        document.body.style.cursor = 'default';
    });
}

// File Upload Drag and Drop
function initializeFileUpload() {
    const uploadArea = document.querySelector('.file-upload-area');
    if (!uploadArea) return;

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--bs-primary)';
        uploadArea.style.backgroundColor = '#495057';
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.style.borderColor = '#6c757d';
        uploadArea.style.backgroundColor = '#343a40';
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.style.borderColor = '#6c757d';
        uploadArea.style.backgroundColor = '#343a40';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });
}

function handleFileUpload(file) {
    // Validate file type
    const allowedTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/json'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Invalid file type. Please upload CSV, XLS, XLSX, or JSON files.', 'error');
        return;
    }

    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
        showNotification('File too large. Maximum size is 100MB.', 'error');
        return;
    }

    // Submit file via HTMX
    const form = document.querySelector('#file-upload-form');
    if (form) {
        const fileInput = form.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.files = new DataTransfer().files;
            fileInput.files = new DataTransfer().files;
            // Create new FileList
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            
            // Trigger HTMX submission
            htmx.trigger(form, 'submit');
        }
    }
}

// Agent Progress Polling
function initializeAgentProgress() {
    const progressContainer = document.querySelector('#agent-progress');
    if (!progressContainer) return;

    let pollInterval = null;
    let agentRunId = null;

    // Start polling when agent run starts
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        if (evt.target.id === 'agent-run-form') {
            const response = evt.detail.xhr.response;
            try {
                const data = JSON.parse(response);
                if (data.agent_run_id) {
                    agentRunId = data.agent_run_id;
                    startProgressPolling();
                }
            } catch (e) {
                console.error('Error parsing agent run response:', e);
            }
        }
    });

    function startProgressPolling() {
        if (pollInterval) clearInterval(pollInterval);
        
        pollInterval = setInterval(function() {
            if (agentRunId) {
                fetch(`/api/agent/run/${agentRunId}/status/`)
                    .then(response => response.json())
                    .then(data => {
                        updateAgentProgress(data);
                        if (data.agent_run.status === 'completed' || data.agent_run.status === 'failed') {
                            clearInterval(pollInterval);
                        }
                    })
                    .catch(error => {
                        console.error('Error polling agent status:', error);
                        clearInterval(pollInterval);
                    });
            }
        }, 2000); // Poll every 2 seconds
    }

    function updateAgentProgress(data) {
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.querySelector('#progress-text');
        const currentStep = document.querySelector('#current-step');
        const nextAction = document.querySelector('#next-action');

        if (progressBar) {
            progressBar.style.width = data.agent_run.progress_percentage + '%';
        }
        if (progressText) {
            progressText.textContent = data.agent_run.progress_percentage + '%';
        }
        if (currentStep) {
            currentStep.textContent = `Step ${data.agent_run.current_step} of ${data.agent_run.total_steps}`;
        }
        if (nextAction) {
            nextAction.textContent = data.next_action || 'Processing...';
        }
    }
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 1050;
        min-width: 300px;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
}

// Chat Auto-scroll
function initializeChatScroll() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        scrollChatToBottom();
    }
}

function scrollChatToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Tool Interactions
function initializeToolInteractions() {
    const toolItems = document.querySelectorAll('.tool-item');
    
    toolItems.forEach(tool => {
        tool.addEventListener('click', function() {
            // Add visual feedback
            tool.style.transform = 'scale(0.98)';
            setTimeout(() => {
                tool.style.transform = '';
            }, 150);
        });
    });
}

// Dataset Info Update
function updateDatasetInfo(datasetData) {
    const datasetName = document.getElementById('dataset-name');
    const rowCount = document.getElementById('row-count');
    const columnCount = document.getElementById('column-count');
    const fileSize = document.getElementById('file-size');
    const datasetStats = document.querySelector('.dataset-stats');
    
    if (datasetName) datasetName.textContent = datasetData.original_filename || 'Uploaded Dataset';
    if (rowCount) rowCount.textContent = datasetData.row_count || '-';
    if (columnCount) columnCount.textContent = datasetData.column_count || '-';
    if (fileSize) fileSize.textContent = formatFileSize(datasetData.file_size_bytes || 0);
    if (datasetStats) datasetStats.style.display = 'grid';
}

// Agent Progress Polling
function startAgentProgressPolling(agentRunId) {
    let pollInterval = null;
    
    function pollAgentStatus() {
        fetch(`/api/agent/run/${agentRunId}/status/`)
            .then(response => response.json())
            .then(data => {
                updateAgentProgress(data);
                if (data.agent_run.status === 'completed' || data.agent_run.status === 'failed') {
                    clearInterval(pollInterval);
                    showNotification('Agent analysis completed!', 'success');
                }
            })
            .catch(error => {
                console.error('Error polling agent status:', error);
                clearInterval(pollInterval);
                showNotification('Agent analysis failed', 'error');
            });
    }
    
    // Start polling every 2 seconds
    pollInterval = setInterval(pollAgentStatus, 2000);
    
    // Initial poll
    pollAgentStatus();
}

function updateAgentProgress(data) {
    const agentStatus = document.getElementById('agent-status');
    if (!agentStatus) return;
    
    const progressHtml = `
        <div class="alert alert-info">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <strong><i class="bi bi-robot"></i> Agent Analysis</strong>
                <span class="badge bg-primary">${data.agent_run.progress_percentage}%</span>
            </div>
            <div class="progress mb-2">
                <div class="progress-bar" style="width: ${data.agent_run.progress_percentage}%"></div>
            </div>
            <small class="text-muted">
                Step ${data.agent_run.current_step} of ${data.agent_run.total_steps}: ${data.next_action || 'Processing...'}
            </small>
        </div>
    `;
    
    agentStatus.innerHTML = progressHtml;
}
