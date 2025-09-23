# UI Implementation Guide

## Overview
This guide provides comprehensive instructions for implementing the three-panel UI with Bootstrap 5+, HTMX, and dark theme for the Data Analysis System.

## Design Principles

### 1. Three-Panel Layout
- **Left Panel**: Statistical Tools (300px width)
- **Middle Panel**: Analytical Dashboard (flexible width)
- **Right Panel**: AI Chat (350px width)
- **Draggable Resizing**: Users can resize panels
- **Responsive Design**: Adapts to different screen sizes

### 2. Dark Theme Implementation
- **Color Palette**: Cursor AI dark theme inspired
- **CSS Variables**: Custom properties for consistent theming
- **Bootstrap Override**: Dark theme variables override Bootstrap defaults
- **Eye-soothing**: Avoid white/cream colors, maintain clean look

### 3. Card-Based UI
- **Consistent Cards**: All content wrapped in Bootstrap cards
- **Card Headers**: Clear section titles
- **Card Bodies**: Content areas with proper spacing
- **Card Footers**: Action buttons and metadata

## File Structure

```
analytics/
├── templates/
│   ├── analytics/
│   │   ├── base.html                 # Base template with dark theme
│   │   ├── dashboard/
│   │   │   ├── index.html           # Main dashboard
│   │   │   ├── upload.html          # File upload page
│   │   │   └── history.html        # Analysis history
│   │   ├── components/
│   │   │   ├── tools_panel.html     # Left tools panel
│   │   │   ├── dashboard_panel.html # Middle dashboard panel
│   │   │   ├── chat_panel.html      # Right chat panel
│   │   │   ├── file_upload.html     # File upload component
│   │   │   ├── analysis_results.html # Analysis results display
│   │   │   └── agent_progress.html  # Agent progress display
│   │   └── partials/
│   │       ├── navbar.html          # Navigation bar
│   │       ├── sidebar.html         # Sidebar navigation
│   │       └── modals.html         # Modal dialogs
├── static/
│   ├── analytics/
│   │   ├── css/
│   │   │   ├── style.css           # Main stylesheet
│   │   │   ├── components.css      # Component-specific styles
│   │   │   ├── dark-theme.css      # Dark theme variables
│   │   │   └── responsive.css      # Responsive design
│   │   ├── js/
│   │   │   ├── main.js             # Main JavaScript
│   │   │   ├── panel-resize.js     # Panel resizing functionality
│   │   │   ├── htmx-config.js      # HTMX configuration
│   │   │   ├── file-upload.js      # File upload handling
│   │   │   ├── analysis-execution.js # Analysis execution
│   │   │   ├── chat-interaction.js # Chat functionality
│   │   │   └── agent-control.js    # Agent control
│   │   └── images/
│   │       ├── logos/              # Company logos
│   │       ├── icons/              # Custom icons
│   │       └── placeholders/       # Placeholder images
└── views/
    ├── dashboard_views.py          # Dashboard views
    ├── upload_views.py             # File upload views
    ├── analysis_views.py           # Analysis views
    ├── chat_views.py               # Chat views
    └── agent_views.py              # Agent views
```

## Implementation Tasks

### Phase 1: Base Template and Theme Setup

#### T066: Base Template Implementation
**File**: `analytics/templates/analytics/base.html`

**Requirements**:
- Bootstrap 5+ integration
- Custom dark theme CSS variables
- HTMX integration
- Three-panel layout structure
- Responsive design

**Implementation**:
```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Data Analysis System{% endblock %}</title>
    
    <!-- Bootstrap 5+ with Dark Theme -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="{% static 'analytics/js/htmx-config.js' %}"></script>
    
    <!-- Custom Dark Theme CSS Variables -->
    <style>
        :root {
            /* Dark Theme Color Palette */
            --bs-body-bg: #1a1a1a;
            --bs-body-color: #e9ecef;
            --bs-primary: #0d6efd;
            --bs-secondary: #6c757d;
            --bs-success: #198754;
            --bs-info: #0dcaf0;
            --bs-warning: #ffc107;
            --bs-danger: #dc3545;
            --bs-light: #f8f9fa;
            --bs-dark: #212529;
            
            /* Custom Dark Theme Variables */
            --analytical-bg-primary: #1a1a1a;
            --analytical-bg-secondary: #2d2d2d;
            --analytical-bg-tertiary: #343a40;
            --analytical-border-color: #495057;
            --analytical-text-primary: #e9ecef;
            --analytical-text-secondary: #adb5bd;
            --analytical-text-muted: #6c757d;
            --analytical-accent-blue: #0d6efd;
            --analytical-accent-green: #198754;
            --analytical-accent-orange: #fd7e14;
            --analytical-accent-purple: #6f42c1;
            --analytical-shadow: rgba(0, 0, 0, 0.3);
            --analytical-shadow-lg: rgba(0, 0, 0, 0.5);
            
            /* Panel Layout Variables */
            --panel-header-height: 60px;
            --panel-border-radius: 0.5rem;
            --panel-padding: 1rem;
            --panel-gap: 1rem;
            
            /* Animation Variables */
            --transition-fast: 0.15s ease-in-out;
            --transition-normal: 0.3s ease-in-out;
            --transition-slow: 0.5s ease-in-out;
        }
        
        body {
            background-color: var(--bs-body-bg);
            color: var(--bs-body-color);
        }
    </style>
    <link rel="stylesheet" href="{% static 'analytics/css/style.css' %}">
</head>
<body>
    <!-- Navigation Bar -->
    {% include 'analytics/partials/navbar.html' %}
    
    <!-- Main Content -->
    <div class="container-fluid mt-3 dashboard-container">
        {% block content %}
        <!-- Main content will be loaded here -->
        {% endblock %}
    </div>

    <!-- Bootstrap Bundle with Popper -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Custom JS for panel resizing -->
    <script src="{% static 'analytics/js/main.js' %}"></script>
</body>
</html>
```

#### T067: Three-Panel Layout CSS
**File**: `analytics/static/analytics/css/style.css`

**Requirements**:
- CSS Grid-based three-panel layout
- Draggable resizing functionality
- Responsive design
- Dark theme styling

**Implementation**:
```css
/* Three-Panel Layout */
.dashboard-container {
    display: grid;
    grid-template-columns: 300px 1fr 350px; /* Left, Middle, Right panel widths */
    grid-template-rows: auto 1fr; /* Header row, content row */
    height: calc(100vh - 76px); /* Adjust for navbar height */
    gap: var(--panel-gap);
}

.tools-panel, .dashboard-panel, .chat-panel {
    background-color: var(--analytical-bg-secondary);
    border: 1px solid var(--analytical-border-color);
    border-radius: var(--panel-border-radius);
    padding: var(--panel-padding);
    overflow-y: auto;
    transition: all var(--transition-normal);
}

/* Panel Headers */
.panel-header {
    background-color: var(--analytical-bg-tertiary);
    border-bottom: 1px solid var(--analytical-border-color);
    padding: 0.75rem var(--panel-padding);
    margin: calc(-1 * var(--panel-padding)) calc(-1 * var(--panel-padding)) var(--panel-padding) calc(-1 * var(--panel-padding));
    border-top-left-radius: var(--panel-border-radius);
    border-top-right-radius: var(--panel-border-radius);
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: var(--panel-header-height);
}

/* Draggable Resizers */
.resizer {
    background-color: var(--analytical-border-color);
    opacity: 0;
    z-index: 1;
    transition: opacity var(--transition-fast);
}

.resizer:hover {
    opacity: 1;
}

.resizer.vertical {
    width: 11px;
    margin: 0 -5px;
    border-left: 5px solid rgba(255, 255, 255, 0);
    border-right: 5px solid rgba(255, 255, 255, 0);
    cursor: col-resize;
}

.resizer.vertical:hover {
    border-left: 5px solid var(--analytical-accent-blue);
    border-right: 5px solid var(--analytical-accent-blue);
}

/* Responsive Design */
@media (max-width: 1200px) {
    .dashboard-container {
        grid-template-columns: 250px 1fr 300px;
    }
}

@media (max-width: 992px) {
    .dashboard-container {
        grid-template-columns: 1fr;
        grid-template-rows: auto auto auto;
    }
    
    .tools-panel, .dashboard-panel, .chat-panel {
        height: 400px;
    }
}
```

### Phase 2: Panel Components

#### T068: Tools Panel Component
**File**: `analytics/templates/analytics/components/tools_panel.html`

**Requirements**:
- Tool categories (Statistical, Advanced, Custom)
- Tool search functionality
- Tool parameter configuration
- Tool execution buttons

**Implementation**:
```html
<div class="tools-panel" id="tools-panel">
    <div class="panel-header">
        <h5 class="mb-0">
            <i class="bi bi-tools"></i> Statistical Tools
        </h5>
        <button class="btn btn-sm btn-outline-secondary" data-bs-toggle="collapse" data-bs-target="#tools-search">
            <i class="bi bi-search"></i>
        </button>
    </div>
    
    <!-- Tool Search -->
    <div class="collapse mb-3" id="tools-search">
        <div class="input-group input-group-sm">
            <input type="text" class="form-control" placeholder="Search tools..." 
                   hx-get="/api/tools/search/" 
                   hx-trigger="keyup changed delay:300ms"
                   hx-target="#tools-list">
            <button class="btn btn-outline-secondary" type="button">
                <i class="bi bi-search"></i>
            </button>
        </div>
    </div>
    
    <!-- Tool Categories -->
    <div class="accordion" id="tools-accordion">
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#statistical-tools">
                    <i class="bi bi-graph-up"></i> Statistical Tools
                </button>
            </h2>
            <div id="statistical-tools" class="accordion-collapse collapse" data-bs-parent="#tools-accordion">
                <div class="accordion-body">
                    <div id="tools-list">
                        <!-- Tools will be loaded here via HTMX -->
                    </div>
                </div>
            </div>
        </div>
        
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#advanced-tools">
                    <i class="bi bi-gear"></i> Advanced Tools
                </button>
            </h2>
            <div id="advanced-tools" class="accordion-collapse collapse" data-bs-parent="#tools-accordion">
                <div class="accordion-body">
                    <!-- Advanced tools will be loaded here -->
                </div>
            </div>
        </div>
    </div>
</div>
```

#### T069: Dashboard Panel Component
**File**: `analytics/templates/analytics/components/dashboard_panel.html`

**Requirements**:
- Analysis results display
- Chart visualization
- Table rendering
- Export functionality

**Implementation**:
```html
<div class="dashboard-panel" id="dashboard-panel">
    <div class="panel-header">
        <h5 class="mb-0">
            <i class="bi bi-graph-up-arrow"></i> Analytical Dashboard
        </h5>
        <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-secondary" data-bs-toggle="dropdown">
                <i class="bi bi-three-dots"></i>
            </button>
            <ul class="dropdown-menu">
                <li><a class="dropdown-item" href="#" hx-get="/api/analysis/export/" hx-target="#dashboard-content">
                    <i class="bi bi-download"></i> Export Results
                </a></li>
                <li><a class="dropdown-item" href="#" hx-post="/api/analysis/clear/" hx-target="#dashboard-content">
                    <i class="bi bi-trash"></i> Clear Results
                </a></li>
            </ul>
        </div>
    </div>
    
    <!-- Dashboard Content -->
    <div id="dashboard-content" class="dashboard-content">
        <!-- Welcome Message -->
        <div class="text-center py-5" id="welcome-message">
            <i class="bi bi-graph-up display-1 text-muted"></i>
            <h4 class="mt-3">Welcome to Analytical Dashboard</h4>
            <p class="text-muted">Upload a dataset and start analyzing with the tools on the left.</p>
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#uploadModal">
                <i class="bi bi-upload"></i> Upload Dataset
            </button>
        </div>
        
        <!-- Analysis Results will be loaded here via HTMX -->
    </div>
</div>
```

#### T070: Chat Panel Component
**File**: `analytics/templates/analytics/components/chat_panel.html`

**Requirements**:
- Chat message display
- Message input
- Context awareness
- Agent status display

**Implementation**:
```html
<div class="chat-panel" id="chat-panel">
    <div class="panel-header">
        <h5 class="mb-0">
            <i class="bi bi-chat-dots"></i> AI Assistant
        </h5>
        <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-secondary" data-bs-toggle="dropdown">
                <i class="bi bi-gear"></i>
            </button>
            <ul class="dropdown-menu">
                <li><a class="dropdown-item" href="#" hx-get="/api/chat/clear/" hx-target="#chat-messages">
                    <i class="bi bi-trash"></i> Clear Chat
                </a></li>
                <li><a class="dropdown-item" href="#" hx-get="/api/chat/export/" hx-target="#chat-messages">
                    <i class="bi bi-download"></i> Export Chat
                </a></li>
            </ul>
        </div>
    </div>
    
    <!-- Chat Messages -->
    <div id="chat-messages" class="chat-messages">
        <!-- Welcome Message -->
        <div class="chat-message assistant-message">
            <div class="message-content">
                <p>Hello! I'm your AI assistant. I can help you interpret analysis results, suggest next steps, and answer questions about your data.</p>
            </div>
            <div class="message-time">Just now</div>
        </div>
    </div>
    
    <!-- Chat Input -->
    <div class="chat-input">
        <form hx-post="/api/chat/messages/" 
              hx-target="#chat-messages" 
              hx-swap="beforeend"
              hx-indicator="#chat-loading">
            <div class="input-group">
                <input type="text" class="form-control" name="message" placeholder="Ask me anything about your data..." required>
                <button class="btn btn-primary" type="submit">
                    <i class="bi bi-send"></i>
                </button>
            </div>
            <div class="form-check form-check-sm mt-2">
                <input class="form-check-input" type="checkbox" name="include_context" id="include-context" checked>
                <label class="form-check-label" for="include-context">
                    Include analysis context
                </label>
            </div>
        </form>
        
        <!-- Loading Indicator -->
        <div id="chat-loading" class="htmx-indicator">
            <div class="text-center py-2">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">AI is thinking...</span>
            </div>
        </div>
    </div>
</div>
```

### Phase 3: Interactive Components

#### T071: File Upload Component
**File**: `analytics/templates/analytics/components/file_upload.html`

**Requirements**:
- Drag and drop functionality
- File type validation
- Progress indication
- Security scanning feedback

**Implementation**:
```html
<!-- Upload Modal -->
<div class="modal fade" id="uploadModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-upload"></i> Upload Dataset
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form hx-post="/api/upload/" 
                      hx-target="#upload-results" 
                      hx-indicator="#upload-progress"
                      enctype="multipart/form-data">
                    
                    <!-- File Drop Zone -->
                    <div class="upload-dropzone" id="upload-dropzone">
                        <div class="upload-content">
                            <i class="bi bi-cloud-upload display-1 text-muted"></i>
                            <h5>Drag & Drop your file here</h5>
                            <p class="text-muted">or click to browse</p>
                            <input type="file" class="form-control" name="file" accept=".csv,.xls,.xlsx,.json" required>
                        </div>
                    </div>
                    
                    <!-- File Info -->
                    <div class="mt-3">
                        <label for="description" class="form-label">Description (Optional)</label>
                        <textarea class="form-control" name="description" rows="3" placeholder="Describe your dataset..."></textarea>
                    </div>
                    
                    <!-- Supported Formats -->
                    <div class="mt-3">
                        <small class="text-muted">
                            <strong>Supported formats:</strong> CSV, XLS, XLSX, JSON<br>
                            <strong>Max file size:</strong> 10MB<br>
                            <strong>Security:</strong> All files are scanned for threats
                        </small>
                    </div>
                    
                    <!-- Upload Progress -->
                    <div id="upload-progress" class="htmx-indicator mt-3">
                        <div class="progress">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%"></div>
                        </div>
                        <div class="text-center mt-2">
                            <span class="spinner-border spinner-border-sm" role="status"></span>
                            <span class="ms-2">Processing file...</span>
                        </div>
                    </div>
                    
                    <!-- Upload Results -->
                    <div id="upload-results" class="mt-3"></div>
                    
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-upload"></i> Upload Dataset
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
```

#### T072: Analysis Results Component
**File**: `analytics/templates/analytics/components/analysis_results.html`

**Requirements**:
- Table rendering
- Chart display
- Export options
- LLM interpretation

**Implementation**:
```html
<div class="analysis-result" data-analysis-id="{{ analysis.id }}">
    <div class="result-header">
        <h6 class="mb-0">
            <i class="bi bi-graph-up"></i> {{ analysis.tool_name|title }}
        </h6>
        <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-secondary" data-bs-toggle="dropdown">
                <i class="bi bi-three-dots"></i>
            </button>
            <ul class="dropdown-menu">
                <li><a class="dropdown-item" href="#" hx-get="/api/analysis/{{ analysis.id }}/export/" hx-target="#export-results">
                    <i class="bi bi-download"></i> Export Results
                </a></li>
                <li><a class="dropdown-item" href="#" hx-post="/api/analysis/{{ analysis.id }}/interpret/" hx-target="#interpretation-{{ analysis.id }}">
                    <i class="bi bi-chat"></i> Get AI Interpretation
                </a></li>
            </ul>
        </div>
    </div>
    
    <!-- Analysis Summary -->
    <div class="result-summary">
        <p class="text-muted mb-2">{{ analysis.summary }}</p>
        <small class="text-muted">
            <i class="bi bi-clock"></i> {{ analysis.execution_time }}s
            <span class="ms-3"><i class="bi bi-calendar"></i> {{ analysis.created_at|date:"M d, Y H:i" }}</span>
        </small>
    </div>
    
    <!-- Tables -->
    {% if analysis.tables %}
    <div class="result-tables mt-3">
        {% for table in analysis.tables %}
        <div class="table-container">
            <h6 class="table-title">{{ table.title }}</h6>
            <div class="table-responsive">
                <table class="table table-dark table-striped table-hover">
                    <thead>
                        <tr>
                            {% for header in table.headers %}
                            <th>{{ header }}</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in table.data %}
                        <tr>
                            {% for cell in row %}
                            <td>{{ cell }}</td>
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Charts -->
    {% if analysis.charts %}
    <div class="result-charts mt-3">
        {% for chart in analysis.charts %}
        <div class="chart-container">
            <h6 class="chart-title">{{ chart.title }}</h6>
            <div class="chart-image">
                <img src="{{ chart.image_url }}" alt="{{ chart.title }}" class="img-fluid">
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- AI Interpretation -->
    <div id="interpretation-{{ analysis.id }}" class="interpretation mt-3">
        <!-- AI interpretation will be loaded here -->
    </div>
</div>
```

### Phase 4: JavaScript Functionality

#### T073: Panel Resizing JavaScript
**File**: `analytics/static/analytics/js/panel-resize.js`

**Requirements**:
- Draggable panel resizing
- State persistence
- Responsive behavior
- Smooth animations

**Implementation**:
```javascript
class PanelResizer {
    constructor() {
        this.panels = {
            tools: document.getElementById('tools-panel'),
            dashboard: document.getElementById('dashboard-panel'),
            chat: document.getElementById('chat-panel')
        };
        this.resizers = document.querySelectorAll('.resizer');
        this.isResizing = false;
        this.currentResizer = null;
        
        this.init();
    }
    
    init() {
        this.createResizers();
        this.bindEvents();
        this.loadPanelState();
    }
    
    createResizers() {
        // Create vertical resizers between panels
        const toolsResizer = this.createResizer('vertical', 'tools-dashboard');
        const chatResizer = this.createResizer('vertical', 'dashboard-chat');
        
        // Insert resizers into DOM
        this.panels.tools.parentNode.insertBefore(toolsResizer, this.panels.dashboard);
        this.panels.dashboard.parentNode.insertBefore(chatResizer, this.panels.chat);
    }
    
    createResizer(direction, id) {
        const resizer = document.createElement('div');
        resizer.className = `resizer ${direction}`;
        resizer.id = id;
        return resizer;
    }
    
    bindEvents() {
        document.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('resizer')) {
                this.startResize(e);
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (this.isResizing) {
                this.resize(e);
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (this.isResizing) {
                this.stopResize();
            }
        });
    }
    
    startResize(e) {
        this.isResizing = true;
        this.currentResizer = e.target;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    }
    
    resize(e) {
        const container = document.querySelector('.dashboard-container');
        const containerRect = container.getBoundingClientRect();
        const mouseX = e.clientX - containerRect.left;
        
        if (this.currentResizer.id === 'tools-dashboard') {
            const toolsWidth = Math.max(200, Math.min(500, mouseX));
            this.panels.tools.style.width = `${toolsWidth}px`;
        } else if (this.currentResizer.id === 'dashboard-chat') {
            const chatWidth = Math.max(250, Math.min(500, containerRect.width - mouseX));
            this.panels.chat.style.width = `${chatWidth}px`;
        }
    }
    
    stopResize() {
        this.isResizing = false;
        this.currentResizer = null;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        this.savePanelState();
    }
    
    savePanelState() {
        const state = {
            toolsWidth: this.panels.tools.style.width,
            chatWidth: this.panels.chat.style.width,
            timestamp: Date.now()
        };
        localStorage.setItem('panelState', JSON.stringify(state));
    }
    
    loadPanelState() {
        const saved = localStorage.getItem('panelState');
        if (saved) {
            const state = JSON.parse(saved);
            if (state.toolsWidth) this.panels.tools.style.width = state.toolsWidth;
            if (state.chatWidth) this.panels.chat.style.width = state.chatWidth;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new PanelResizer();
});
```

#### T074: HTMX Configuration
**File**: `analytics/static/analytics/js/htmx-config.js`

**Requirements**:
- Error handling
- Loading indicators
- Request/response logging
- Retry mechanisms

**Implementation**:
```javascript
// HTMX Configuration
document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX
    htmx.config.defaultSwapStyle = 'innerHTML';
    htmx.config.defaultSwapDelay = 100;
    htmx.config.defaultSettleDelay = 100;
    
    // Global error handling
    document.body.addEventListener('htmx:responseError', function(event) {
        console.error('HTMX Error:', event.detail);
        showError('Request failed. Please try again.');
    });
    
    // Global request handling
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        // Add CSRF token to all requests
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            event.detail.headers['X-CSRFToken'] = csrfToken.value;
        }
        
        // Log request
        console.log('HTMX Request:', event.detail.method, event.detail.path);
    });
    
    // Global response handling
    document.body.addEventListener('htmx:afterRequest', function(event) {
        console.log('HTMX Response:', event.detail.status, event.detail.path);
        
        // Handle different status codes
        if (event.detail.status === 401) {
            showError('Please log in to continue.');
            window.location.href = '/login/';
        } else if (event.detail.status === 403) {
            showError('You do not have permission to perform this action.');
        } else if (event.detail.status >= 500) {
            showError('Server error. Please try again later.');
        }
    });
    
    // Loading indicators
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        const target = event.target;
        const indicator = target.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    });
    
    document.body.addEventListener('htmx:afterRequest', function(event) {
        const target = event.target;
        const indicator = target.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    });
});

// Utility functions
function showError(message) {
    // Create error toast
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-danger border-0';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to toast container
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove after hide
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function showSuccess(message) {
    // Similar to showError but with success styling
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-success border-0';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to toast container and show
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}
```

### Phase 5: Responsive Design

#### T075: Responsive CSS
**File**: `analytics/static/analytics/css/responsive.css`

**Requirements**:
- Mobile-first design
- Tablet optimization
- Desktop enhancement
- Touch-friendly interactions

**Implementation**:
```css
/* Mobile First - Base styles for mobile */
@media (max-width: 576px) {
    .dashboard-container {
        grid-template-columns: 1fr;
        grid-template-rows: auto auto auto;
        gap: 1rem;
        padding: 0.5rem;
    }
    
    .tools-panel, .dashboard-panel, .chat-panel {
        height: 300px;
        min-height: 300px;
    }
    
    .panel-header {
        padding: 0.5rem;
        height: 50px;
    }
    
    .panel-header h5 {
        font-size: 1rem;
    }
    
    .btn-group-sm .btn {
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
    }
    
    .table-responsive {
        font-size: 0.875rem;
    }
    
    .chat-input .input-group {
        flex-direction: column;
    }
    
    .chat-input .btn {
        margin-top: 0.5rem;
        width: 100%;
    }
}

/* Tablet */
@media (min-width: 577px) and (max-width: 992px) {
    .dashboard-container {
        grid-template-columns: 250px 1fr;
        grid-template-rows: auto auto;
    }
    
    .chat-panel {
        grid-column: 1 / -1;
        grid-row: 2;
        height: 400px;
    }
    
    .tools-panel, .dashboard-panel {
        height: calc(100vh - 200px);
    }
}

/* Desktop */
@media (min-width: 993px) {
    .dashboard-container {
        grid-template-columns: 300px 1fr 350px;
        grid-template-rows: auto 1fr;
    }
    
    .tools-panel, .dashboard-panel, .chat-panel {
        height: calc(100vh - 100px);
    }
    
    /* Hover effects for desktop */
    .tools-panel:hover, .dashboard-panel:hover, .chat-panel:hover {
        box-shadow: 0 0.5rem 1rem var(--analytical-shadow-lg);
    }
    
    .btn:hover {
        transform: translateY(-1px);
        transition: transform var(--transition-fast);
    }
}

/* Large Desktop */
@media (min-width: 1400px) {
    .dashboard-container {
        grid-template-columns: 350px 1fr 400px;
    }
    
    .tools-panel, .dashboard-panel, .chat-panel {
        padding: 1.5rem;
    }
    
    .panel-header {
        padding: 1rem 1.5rem;
    }
}

/* Touch-friendly interactions */
@media (hover: none) and (pointer: coarse) {
    .btn {
        min-height: 44px;
        min-width: 44px;
    }
    
    .form-control {
        min-height: 44px;
    }
    
    .resizer {
        width: 20px;
        height: 20px;
    }
    
    .accordion-button {
        min-height: 44px;
    }
}
```

## Testing Guidelines

### UI Testing Checklist

1. **Layout Testing**
   - [ ] Three-panel layout displays correctly
   - [ ] Panels resize properly
   - [ ] Responsive design works on all screen sizes
   - [ ] Dark theme applies consistently

2. **Functionality Testing**
   - [ ] File upload works with drag & drop
   - [ ] Tool selection and execution
   - [ ] Chat interaction with AI
   - [ ] Analysis results display correctly

3. **HTMX Testing**
   - [ ] All HTMX requests work without page refresh
   - [ ] Error handling displays appropriate messages
   - [ ] Loading indicators show during requests
   - [ ] CSRF protection works correctly

4. **Performance Testing**
   - [ ] Page load time < 2 seconds
   - [ ] UI updates < 1 second
   - [ ] Smooth animations and transitions
   - [ ] No memory leaks in JavaScript

5. **Accessibility Testing**
   - [ ] Keyboard navigation works
   - [ ] Screen reader compatibility
   - [ ] Color contrast meets WCAG standards
   - [ ] Focus indicators are visible

## Implementation Order

1. **T066**: Base template and theme setup
2. **T067**: Three-panel layout CSS
3. **T068**: Tools panel component
4. **T069**: Dashboard panel component
5. **T070**: Chat panel component
6. **T071**: File upload component
7. **T072**: Analysis results component
8. **T073**: Panel resizing JavaScript
9. **T074**: HTMX configuration
10. **T075**: Responsive design

## Notes

- All components should follow the card-based UI pattern
- Use Bootstrap 5+ components and utilities
- Implement proper error handling and user feedback
- Ensure all interactions work without JavaScript (progressive enhancement)
- Test thoroughly on different devices and browsers
- Follow the dark theme color palette consistently
- Use HTMX for all dynamic interactions
- Implement proper loading states and error messages
