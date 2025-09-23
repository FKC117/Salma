# Quickstart Guide: Data Analysis System

**Date**: 2024-12-19  
**Feature**: Data Analysis System  
**Technology**: Django + HTMX + Bootstrap + LangChain

## Prerequisites

### System Requirements
- Python 3.11+
- Virtual environment (always activated)
- Git for version control
- Modern web browser with HTMX support

### Dependencies
```bash
# Core framework
Django==4.2.7
djangorestframework==3.14.0

# Task queue and background processing (NON-NEGOTIABLE)
celery==5.3.4
redis==5.0.1
flower==2.0.1

# Frontend
htmx==1.9.6
bootstrap5==5.3.0

# Data processing
pandas==2.1.3
lifelines==0.27.8
matplotlib==3.8.2
seaborn==0.13.0
pyarrow==13.0.0
openpyxl==3.1.2

# AI integration
langchain==0.0.350
google-generativeai==0.3.2
tiktoken==0.5.2

# Report generation
python-docx==1.1.0
Pillow==10.1.0

# Security and utilities
django-cleanup==8.2.0
bleach==6.1.0
psutil==5.9.6

# Development
pytest==7.4.3
pytest-django==4.7.0
black==23.9.1
flake8==6.1.0
```

## Installation

### 1. Clone and Setup
```bash
# Clone repository
git clone <repository-url>
cd data-analysis-system

# CRITICAL: Activate virtual environment (NON-NEGOTIABLE)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# VERIFY: Check virtual environment is active
which python  # Should show path to venv/bin/python
pip list      # Should show only base packages

# MANDATORY: Install requirements.txt before any development work
pip install -r requirements.txt

# VERIFY: Check all dependencies are installed
pip list
```

**⚠️ CRITICAL WARNING**: Virtual environment MUST be activated before ANY Python operations. This is NON-NEGOTIABLE and CRITICAL for project consistency.

### 2. PostgreSQL Setup (NON-NEGOTIABLE)
```bash
# Install PostgreSQL (if not already installed)
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (with Homebrew)
brew install postgresql
brew services start postgresql

# Windows - Download from https://www.postgresql.org/download/windows/

# Create database and user
sudo -u postgres psql
CREATE DATABASE analytical;
CREATE USER postgres WITH PASSWORD 'Afroafri117!@';
GRANT ALL PRIVILEGES ON DATABASE analytical TO postgres;
ALTER USER postgres CREATEDB;
\q

# Test connection
psql -h localhost -U postgres -d analytical
```

### 3. Celery Setup (NON-NEGOTIABLE)
```bash
# Start Redis server (required for Celery broker)
# Windows (if Redis installed)
redis-server

# Linux/Mac
sudo systemctl start redis
# OR
redis-server

# Start Celery worker (in separate terminal)
celery -A analytics worker --loglevel=info --concurrency=4

# Start Celery beat scheduler (in separate terminal)
celery -A analytics beat --loglevel=info

# Start Flower monitoring (optional, in separate terminal)
celery -A analytics flower --port=5555
```

**⚠️ CRITICAL**: Celery MUST be running for all background tasks. Without Celery workers, file processing, report generation, and other heavy operations will fail.

### 4. Requirements.txt Generation

The system MUST generate a comprehensive requirements.txt file with all dependencies pinned to specific versions:

```txt
# Core Django Framework
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-redis==5.4.0

# Database & Storage
psycopg2-binary==2.9.9
pyarrow==13.0.0
pandas==2.1.3
numpy==1.24.3

# AI Integration
google-generativeai==0.3.2
tiktoken==0.5.1
langchain==0.0.350

# Data Analysis & Visualization
lifelines==0.27.8
matplotlib==3.8.2
seaborn==0.13.0

# File Processing
openpyxl==3.1.2
xlrd==2.0.1
python-magic==0.4.27

# Caching & Sessions
redis==5.0.1
django-session-cleanup==1.0.0

# Security & Validation
cryptography==41.0.7
python-magic-bin==0.4.14

# Monitoring & Logging
psutil==5.9.6
django-extensions==3.2.3

# Development Dependencies
pytest==7.4.3
pytest-django==4.7.0
coverage==7.3.2
black==23.11.0
flake8==6.1.0
isort==5.12.0

# Testing
factory-boy==3.3.0
faker==20.1.0
```

### 3. Database Setup
```bash
# CRITICAL: Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

### 5. Hybrid Data Architecture

The system uses a **hybrid data storage architecture** optimized for analytical workloads:

#### **PostgreSQL Database**
- **Purpose**: Metadata, user accounts, analysis results, audit trails, agent runs
- **Tables**: User, Dataset, AnalysisResult, AgentRun, AgentStep, AuditTrail, etc.
- **Benefits**: ACID compliance, relational integrity, complex queries

#### **Parquet Files**
- **Purpose**: Raw dataset content (uploaded files converted to Parquet)
- **Location**: `media/datasets/` directory
- **Benefits**: Fast analytical processing, columnar storage, compression

#### **Redis Cache**
- **Purpose**: Session data, analysis results cache, real-time data
- **Key Prefix**: `analytical:` for all cache keys
- **Benefits**: Fast access, session management, temporary data

#### **Data Flow**
1. **Upload**: File → Parquet conversion → PostgreSQL metadata
2. **Analysis**: Read Parquet → Process → Store results in PostgreSQL
3. **Caching**: Cache analysis results in Redis with `analytical:` prefix
4. **Retrieval**: PostgreSQL for metadata, Redis for cached results

### 6. Configuration
```python
# settings.py - Key configurations
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'analytical',
        'USER': 'postgres',
        'PASSWORD': 'Afroafri117!@',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed'
        }
    }
}

# Redis for caching with analytical key prefix
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'KEY_PREFIX': 'analytical',
            'VERSION': 1,
        }
    }
}

# Google AI API configuration
GOOGLE_AI_API_KEY = 'your-google-ai-api-key-here'
GOOGLE_AI_MODEL = 'gemini-pro'

# Token management settings
DEFAULT_USER_TOKEN_LIMIT = 10000
TOKEN_RESET_FREQUENCY = 'monthly'  # monthly, weekly, daily

# Storage management settings
DEFAULT_USER_STORAGE_LIMIT = 262144000  # 250MB in bytes
STORAGE_WARNING_THRESHOLD = 0.8  # 80% of limit
STORAGE_CRITICAL_THRESHOLD = 0.9  # 90% of limit

# Performance monitoring settings
PERFORMANCE_MONITORING_ENABLED = True
METRICS_RETENTION_DAYS = 30
ALERT_EMAIL = 'admin@example.com'

# Error handling settings
ERROR_LOGGING_ENABLED = True
ERROR_CORRELATION_ID_LENGTH = 16
AUTO_RETRY_ATTEMPTS = 3
AUTO_RETRY_DELAY = 1  # seconds

# Backup settings
BACKUP_ENABLED = True
BACKUP_RETENTION_DAYS = 30
BACKUP_SCHEDULE = '0 2 * * *'  # Daily at 2 AM

# API rate limiting settings
API_RATE_LIMIT_ENABLED = True
DEFAULT_RATE_LIMIT = 1000  # requests per hour
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

# Audit trail settings
AUDIT_TRAIL_ENABLED = True
AUDIT_RETENTION_DAYS = 365  # 1 year
AUDIT_LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
AUDIT_MASK_SENSITIVE_DATA = True
AUDIT_CORRELATION_ID_LENGTH = 16

# Detailed logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
        },
        'audit': {
            'format': 'AUDIT|{asctime}|{levelname}|{correlation_id}|{user_id}|{action_type}|{message}',
            'style': '{',
        },
    },
    'filters': {
        'correlation_id': {
            '()': 'analytics.logging.CorrelationIdFilter',
        },
        'sensitive_data': {
            '()': 'analytics.logging.SensitiveDataFilter',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['correlation_id', 'sensitive_data'],
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
            'filters': ['correlation_id', 'sensitive_data'],
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/audit.log',
            'maxBytes': 1024*1024*50,  # 50MB
            'backupCount': 10,
            'formatter': 'audit',
            'filters': ['correlation_id', 'sensitive_data'],
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/errors.log',
            'maxBytes': 1024*1024*20,  # 20MB
            'backupCount': 5,
            'formatter': 'json',
            'filters': ['correlation_id', 'sensitive_data'],
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/performance.log',
            'maxBytes': 1024*1024*30,  # 30MB
            'backupCount': 5,
            'formatter': 'json',
            'filters': ['correlation_id', 'sensitive_data'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'analytics': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'analytics.audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'analytics.performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'analytics.errors': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file', 'error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB

# Data Analysis & Visualization Settings
# Matplotlib Agg backend for server-side plotting (NON-NEGOTIABLE)
import matplotlib
matplotlib.use('Agg')  # Must be set before importing pyplot
import matplotlib.pyplot as plt

# Visualization settings
PLOT_DPI = 300
PLOT_FORMAT = 'png'
PLOT_BBOX_INCHES = 'tight'
PLOT_FACE_COLOR = 'white'
PLOT_EDGE_COLOR = 'none'

# Image storage settings
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
GENERATED_IMAGES_DIR = os.path.join(MEDIA_ROOT, 'generated_images')
SESSION_IMAGES_DIR = os.path.join(GENERATED_IMAGES_DIR, 'sessions')

# LLM Batch Processing Settings
LLM_BATCH_SIZE = 5  # Maximum number of analysis results per batch
LLM_BATCH_TIMEOUT = 30  # Timeout in seconds for batch processing
LLM_MAX_IMAGES_PER_BATCH = 10  # Maximum images per batch request

# Image processing settings
IMAGE_MAX_SIZE = 10 * 1024 * 1024  # 10MB max image size
IMAGE_QUALITY = 95  # JPEG quality (1-100)
BASE64_ENCODING = True  # Enable base64 encoding for LLM processing

# LangChain Sandbox Settings (NON-NEGOTIABLE)
SANDBOX_ENABLED = True
SANDBOX_MAX_EXECUTION_TIME = 30  # seconds
SANDBOX_MAX_MEMORY_MB = 512  # MB
SANDBOX_MAX_CPU_TIME = 60  # seconds
SANDBOX_MAX_RETRIES = 3
SANDBOX_TIMEOUT = 35  # seconds (slightly higher than execution time)

# Sandbox Security Settings
SANDBOX_ALLOWED_LIBRARIES = [
    'pandas', 'numpy', 'matplotlib', 'seaborn', 'lifelines',
    'scipy', 'sklearn', 'statsmodels', 'plotly'
]
SANDBOX_BLOCKED_IMPORTS = [
    'os', 'sys', 'subprocess', 'importlib', 'eval', 'exec',
    'open', 'file', 'input', 'raw_input', '__import__'
]
SANDBOX_BLOCKED_FUNCTIONS = [
    'eval', 'exec', 'compile', 'open', 'file', 'input',
    'raw_input', '__import__', 'reload', 'vars', 'globals', 'locals'
]

# Sandbox Execution Settings
SANDBOX_WORKING_DIR = os.path.join(BASE_DIR, 'sandbox_executions')
SANDBOX_TEMP_DIR = os.path.join(SANDBOX_WORKING_DIR, 'temp')
SANDBOX_OUTPUT_DIR = os.path.join(SANDBOX_WORKING_DIR, 'outputs')
SANDBOX_LOG_DIR = os.path.join(SANDBOX_WORKING_DIR, 'logs')

# Create sandbox directories
os.makedirs(SANDBOX_WORKING_DIR, exist_ok=True)
os.makedirs(SANDBOX_TEMP_DIR, exist_ok=True)
os.makedirs(SANDBOX_OUTPUT_DIR, exist_ok=True)
os.makedirs(SANDBOX_LOG_DIR, exist_ok=True)

# Report Generation Settings (NON-NEGOTIABLE)
REPORT_GENERATION_ENABLED = True
REPORT_OUTPUT_DIR = os.path.join(MEDIA_ROOT, 'generated_reports')
REPORT_TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates', 'reports')
REPORT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max report size
REPORT_GENERATION_TIMEOUT = 300  # 5 minutes max generation time
REPORT_RETENTION_DAYS = 30  # Reports expire after 30 days

# Report Templates
REPORT_TEMPLATES = {
    'default_professional': {
        'name': 'Professional Analysis Report',
        'description': 'Clean, professional report template for business presentations',
        'color_scheme': 'professional',
        'font_family': 'Calibri',
        'font_size': 11,
        'page_orientation': 'portrait'
    },
    'executive_summary': {
        'name': 'Executive Summary',
        'description': 'Concise executive summary template for high-level stakeholders',
        'color_scheme': 'corporate',
        'font_family': 'Arial',
        'font_size': 12,
        'page_orientation': 'portrait'
    },
    'detailed_analysis': {
        'name': 'Detailed Analysis Report',
        'description': 'Comprehensive report template with all analysis details',
        'color_scheme': 'academic',
        'font_family': 'Times New Roman',
        'font_size': 11,
        'page_orientation': 'portrait'
    },
    'creative_presentation': {
        'name': 'Creative Presentation',
        'description': 'Modern, creative template for visual presentations',
        'color_scheme': 'creative',
        'font_family': 'Segoe UI',
        'font_size': 10,
        'page_orientation': 'landscape'
    }
}

# Create report directories
os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_TEMPLATES_DIR, exist_ok=True)

# Performance Optimization & Memory Efficiency Settings (NON-NEGOTIABLE)
PERFORMANCE_OPTIMIZATION_ENABLED = True

# Memory Management
MAX_MEMORY_PER_OPERATION = 512 * 1024 * 1024  # 512MB per operation
MEMORY_CLEANUP_INTERVAL = 300  # 5 minutes
LAZY_LOADING_ENABLED = True
PAGINATION_SIZE = 50  # Default pagination size
STREAMING_CHUNK_SIZE = 8192  # 8KB chunks for file streaming

# Database Optimization
DB_QUERY_TIMEOUT = 30  # seconds
DB_CONNECTION_POOL_SIZE = 10
DB_MAX_CONNECTIONS = 20
SELECT_RELATED_DEPTH = 3
PREFETCH_RELATED_DEPTH = 2

# Caching Configuration
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
CACHE_MAX_ENTRIES = 1000
CACHE_CULL_FREQUENCY = 3
SESSION_CACHE_TIMEOUT = 3600  # 1 hour
ANALYSIS_RESULT_CACHE_TIMEOUT = 7200  # 2 hours

# Image Optimization
IMAGE_COMPRESSION_QUALITY = 85  # JPEG quality (1-100)
IMAGE_MAX_WIDTH = 1920  # pixels
IMAGE_MAX_HEIGHT = 1080  # pixels
IMAGE_THUMBNAIL_SIZE = (300, 200)  # pixels
AUTO_IMAGE_COMPRESSION = True

# File Processing Optimization
FILE_STREAMING_ENABLED = True
PARQUET_CHUNK_SIZE = 10000  # rows per chunk
CSV_CHUNK_SIZE = 10000  # rows per chunk
MAX_CONCURRENT_UPLOADS = 3
UPLOAD_TIMEOUT = 300  # 5 minutes

# Session Management Optimization
SESSION_CLEANUP_INTERVAL = 3600  # 1 hour
MAX_SESSION_DATA_SIZE = 10 * 1024 * 1024  # 10MB per session
SESSION_DATA_COMPRESSION = True
AUTO_SESSION_CLEANUP = True

# LLM Optimization
LLM_RESPONSE_CACHE_TIMEOUT = 1800  # 30 minutes
LLM_CONTEXT_CACHE_SIZE = 100  # max contexts
LLM_BATCH_SIZE_OPTIMIZED = 3  # reduced for memory efficiency
LLM_TIMEOUT_OPTIMIZED = 20  # seconds

# Sandbox Optimization
SANDBOX_MEMORY_LIMIT_OPTIMIZED = 256 * 1024 * 1024  # 256MB
SANDBOX_CLEANUP_INTERVAL = 60  # 1 minute
SANDBOX_MAX_CONCURRENT_EXECUTIONS = 2
SANDBOX_TEMP_CLEANUP_ENABLED = True
```

## Running the Application

### 1. Start Development Server
```bash
# CRITICAL: Activate virtual environment (NON-NEGOTIABLE)
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# VERIFY: Check virtual environment is active
echo $VIRTUAL_ENV  # Should show path to venv
which python       # Should show venv/bin/python

# Start Django server
python manage.py runserver

# Start Redis (separate terminal - also activate venv first)
# In new terminal:
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
redis-server
```

### 2. Access Application
- **URL**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/docs

## User Workflow

### 1. User Registration
```bash
# Register new user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password1": "securepass123",
    "password2": "securepass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": true,
    "is_staff": false,
    "is_superuser": false,
    "date_joined": "2024-12-19T10:30:00Z",
    "last_login": null
  }
}
```

### 2. User Login
```bash
# Login user
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "securepass123"}'
```

**Expected Response**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": true,
    "is_staff": false,
    "is_superuser": false,
    "date_joined": "2024-12-19T10:30:00Z",
    "last_login": "2024-12-19T10:35:00Z"
  },
  "session_id": "abc123def456"
}
```

### 2. Upload Dataset
```bash
# Upload CSV file
curl -X POST http://localhost:8000/api/upload/ \
  -H "X-CSRFToken: <csrf-token>" \
  -F "file=@sample_data.csv" \
  -F "name=Sample Dataset"
```

**Expected Response**:
```json
{
  "success": true,
  "dataset_id": 1,
  "message": "File uploaded and processed successfully",
  "columns": [
    {
      "name": "age",
      "data_type": "integer",
      "is_numeric": true,
      "null_count": 0,
      "unique_count": 45
    },
    {
      "name": "name",
      "data_type": "string",
      "is_numeric": false,
      "null_count": 0,
      "unique_count": 100
    }
  ]
}
```

### 3. Create Analysis Session
```bash
# Create session for dataset
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf-token>" \
  -d '{"dataset_id": 1, "settings": {"theme": "dark"}}'
```

### 4. Execute Analysis Tool
```bash
# Run statistical analysis
curl -X POST http://localhost:8000/api/analysis/execute/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf-token>" \
  -d '{
    "tool_id": 1,
    "dataset_id": 1,
    "parameters": {
      "column": "age",
      "method": "descriptive"
    },
    "session_id": "abc123"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "result_id": 1,
  "execution_time": 245.67,
  "result_data": {
    "mean": 35.2,
    "median": 34.0,
    "std": 12.5,
    "min": 18,
    "max": 65
  },
  "cached": false
}
```

### 5. AI Chat Interaction
```bash
# Send message to AI chat
curl -X POST http://localhost:8000/api/chat/messages/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf-token>" \
  -d '{
    "session_id": "abc123",
    "message": "What does the age distribution tell us about this dataset?",
    "analysis_result_id": 1
  }'
```

### 6. Analysis History Management
```bash
# Get analysis history for session
curl -X GET http://localhost:8000/api/analysis/history/abc123/ \
  -H "X-CSRFToken: <csrf-token>"
```

**Expected Response**:
```json
{
  "history": [
    {
      "id": 1,
      "analysis_result_id": 1,
      "tool_id": 1,
      "execution_order": 1,
      "card_position": {"x": 100, "y": 200},
      "card_size": {"width": 400, "height": 300},
      "card_visible": true,
      "created_at": "2024-12-19T10:30:00Z"
    }
  ]
}
```

### 7. Dataset Switching with History Restoration
```bash
# Switch dataset and restore analysis history
curl -X POST http://localhost:8000/api/sessions/switch-dataset/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf-token>" \
  -d '{
    "current_session_id": "abc123",
    "new_dataset_id": 2
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "new_session_id": "def456",
  "restored_analysis": [
    {
      "id": 2,
      "analysis_result_id": 3,
      "tool_id": 2,
      "execution_order": 1,
      "card_position": {"x": 150, "y": 250},
      "card_size": {"width": 350, "height": 250},
      "card_visible": true,
      "created_at": "2024-12-19T09:15:00Z"
    }
  ]
}
```

### 8. Card Position Management
```bash
# Update card positions and visibility
curl -X POST http://localhost:8000/api/analysis/history/cards/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf-token>" \
  -d '{
    "session_id": "abc123",
    "card_updates": [
      {
        "analysis_id": 1,
        "position": {"x": 200, "y": 300},
        "size": {"width": 450, "height": 350},
        "visible": true
      }
    ]
  }'
```

### 9. Token Management
```bash
# Get user token usage
curl -X GET http://localhost:8000/api/tokens/usage/ \
  -H "X-CSRFToken: <csrf-token>"
```

**Expected Response**:
```json
{
  "token_limit": 10000,
  "tokens_used": 2500,
  "tokens_used_this_month": 1500,
  "tokens_remaining": 7500,
  "usage_percentage": 25.0
}
```

### 10. Token Usage History
```bash
# Get token usage history
curl -X GET http://localhost:8000/api/tokens/usage/history/?limit=10 \
  -H "X-CSRFToken: <csrf-token>"
```

**Expected Response**:
```json
{
  "usage_history": [
    {
      "id": 1,
      "operation_type": "chat",
      "input_tokens": 150,
      "output_tokens": 200,
      "total_tokens": 350,
      "model_used": "gemini-pro",
      "cost_estimate": 0.00175,
      "created_at": "2024-12-19T10:30:00Z"
    }
  ],
  "total_count": 25
}
```

### 11. Update Token Limits (Admin)
```bash
# Update user token limits
curl -X POST http://localhost:8000/api/tokens/limits/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf-token>" \
  -d '{"token_limit": 20000}'
```

## UI Testing

### 1. Three-Panel Layout
- **Left Panel**: Statistical tools list with search and filtering
- **Middle Panel**: Analytical dashboard with results display in cards
- **Right Panel**: AI chat interface
- **Top Bar**: File upload area with drag-and-drop support

### 2. HTMX Interactions
- File upload with progress indicator
- Dynamic tool parameter forms
- Real-time analysis results
- Draggable panel resizing
- AI chat with streaming responses
- Dataset switching with history restoration
- Card position updates

### 3. Analysis History Management
- **Dataset Tagging**: Sessions automatically tagged to datasets
- **History Preservation**: Analysis results preserved across dataset switches
- **Card-Based UI**: All analysis results wrapped in cards
- **Position Tracking**: Card positions and sizes preserved
- **Workspace Restoration**: Previous analysis restored when switching back

### 4. Dark Theme Verification
- All components use dark color scheme
- Cards have proper shadows and borders
- Text is readable with good contrast
- Bootstrap components styled correctly
- Analysis result cards follow dark theme

## Testing

### 1. Run Test Suite
```bash
# CRITICAL: Activate virtual environment (NON-NEGOTIABLE)
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# VERIFY: Check virtual environment is active
which python  # Should show venv/bin/python

# Run all tests
python manage.py test

# Run specific test categories
python manage.py test tests.unit
python manage.py test tests.integration
python manage.py test tests.contract

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### 2. Test Scenarios

#### File Upload Tests
```python
def test_csv_upload():
    """Test CSV file upload and processing"""
    with open('test_data.csv', 'rb') as f:
        response = client.post('/api/upload/', {'file': f, 'name': 'Test CSV'})
    assert response.status_code == 200
    assert response.json()['success'] == True
    assert 'columns' in response.json()
```

#### Analysis Tool Tests
```python
def test_statistical_analysis():
    """Test statistical analysis tool execution"""
    response = client.post('/api/analysis/execute/', {
        'tool_id': 1,
        'dataset_id': 1,
        'parameters': {'column': 'age', 'method': 'descriptive'}
    })
    assert response.status_code == 200
    assert 'result_data' in response.json()
```

#### HTMX Integration Tests
```python
def test_htmx_file_upload():
    """Test HTMX file upload with partial update"""
    response = client.post('/api/upload/', {
        'file': test_file,
        'name': 'Test File'
    }, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert 'hx-trigger' in response.headers

def test_htmx_analysis_execution():
    """Test HTMX analysis execution with partial update"""
    response = client.post('/api/analysis/execute/', {
        'tool_id': 1,
        'dataset_id': 1,
        'parameters': {'column': 'age', 'method': 'descriptive'}
    }, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert 'hx-trigger' in response.headers

def test_htmx_dataset_switching():
    """Test HTMX dataset switching with history restoration"""
    response = client.post('/api/sessions/switch-dataset/', {
        'current_session_id': 'abc123',
        'new_dataset_id': 2
    }, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert 'hx-trigger' in response.headers

def test_htmx_target_validation():
    """Test HTMX target validation prevents errors"""
    # Test valid HTMX target
    response = client.get('/api/datasets/', HTTP_HX_TARGET='#datasets-list')
    assert response.status_code == 200
    
    # Test invalid HTMX target (should not cause error)
    response = client.get('/api/datasets/', HTTP_HX_TARGET='#invalid-target')
    assert response.status_code == 200
```

### 3. Performance Tests
```bash
# Load testing with locust
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Memory profiling
python -m memory_profiler manage.py runserver
```

## Security Testing

### 1. File Upload Security
```python
def test_malicious_file_upload():
    """Test that malicious files are rejected"""
    malicious_file = create_malicious_excel()
    response = client.post('/api/upload/', {'file': malicious_file})
    assert response.status_code == 400
    assert 'security' in response.json()['error'].lower()
```

### 2. Input Validation
```python
def test_sql_injection_prevention():
    """Test SQL injection prevention"""
    response = client.post('/api/analysis/execute/', {
        'tool_id': 1,
        'dataset_id': "1; DROP TABLE datasets;",
        'parameters': {}
    })
    assert response.status_code == 400
```

### 3. CSRF Protection
```python
def test_csrf_protection():
    """Test CSRF protection on state-changing operations"""
    response = client.post('/api/upload/', {'file': test_file})
    assert response.status_code == 403  # CSRF token required
```

### 4. HTMX Error Prevention Testing
```python
def test_htmx_target_errors():
    """Test that HTMX target errors are prevented"""
    # Test with valid target
    response = client.get('/api/datasets/', HTTP_HX_TARGET='#datasets-list')
    assert response.status_code == 200
    
    # Test with invalid target (should not cause server error)
    response = client.get('/api/datasets/', HTTP_HX_TARGET='#nonexistent')
    assert response.status_code == 200
    
def test_htmx_request_validation():
    """Test HTMX request validation"""
    # Test valid HTMX request
    response = client.post('/api/analysis/execute/', {
        'tool_id': 1,
        'dataset_id': 1,
        'parameters': {}
    }, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    
    # Test malformed HTMX request
    response = client.post('/api/analysis/execute/', {
        'tool_id': 'invalid',
        'dataset_id': 1,
        'parameters': {}
    }, HTTP_HX_REQUEST='true')
    assert response.status_code == 400

def test_htmx_loading_states():
    """Test HTMX loading states are implemented"""
    response = client.post('/api/upload/', {
        'file': test_file,
        'name': 'Test File'
    }, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    # Check for loading state indicators in response
    assert 'hx-indicator' in response.content.decode() or 'loading' in response.content.decode()
```

## Troubleshooting

### Common Issues

#### 1. Virtual Environment Not Activated (CRITICAL)
```bash
# Error: ModuleNotFoundError: No module named 'django'
# Error: Command not found: python
# Error: Package not found in global environment

# Solution: ALWAYS activate virtual environment (NON-NEGOTIABLE)
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# VERIFY activation:
which python  # Should show venv/bin/python
echo $VIRTUAL_ENV  # Should show venv path
pip list  # Should show project packages

# If still having issues, recreate virtual environment:
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### 2. Redis Connection Error
```bash
# Error: redis.exceptions.ConnectionError
# Solution: Start Redis server
redis-server
# or install Redis
sudo apt-get install redis-server  # Ubuntu
brew install redis                 # macOS
```

#### 3. HTMX Not Working
```bash
# Check: HTMX script loaded in templates
# Verify: No JavaScript errors in browser console
# Test: Check network tab for HTMX requests
```

#### 4. File Upload Fails
```bash
# Check: File size limits in settings.py
# Verify: File type validation
# Test: Check file permissions
```

### Debug Mode
```python
# Enable debug logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Code Organization & Architecture

### Project Structure (NON-NEGOTIABLE)
```
analytics/
├── tools/                    # Individual tool files
│   ├── __init__.py
│   ├── descriptive_stats.py
│   ├── correlation_analysis.py
│   ├── regression_analysis.py
│   └── survival_analysis.py
├── views/                    # Separated view modules
│   ├── __init__.py
│   ├── dataset_views.py
│   ├── analysis_views.py
│   ├── chat_views.py
│   └── tool_views.py
├── views.py                  # Main views file (imports from views/)
├── models.py
├── urls.py
└── utils/
    ├── __init__.py
    ├── llm_context.py
    └── tool_registry.py
```

### Tool Organization
```python
# tools/descriptive_stats.py
class DescriptiveStatsTool:
    def __init__(self):
        self.name = "Descriptive Statistics"
        self.description = "Calculate basic descriptive statistics"
        self.parameters = {
            "column": {"type": "string", "required": True},
            "include_plots": {"type": "boolean", "default": True}
        }
    
    def execute(self, data, parameters):
        """Execute descriptive statistics analysis"""
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Set Agg backend
        matplotlib.use('Agg')
        
        column = parameters['column']
        stats = data[column].describe()
        
        if parameters.get('include_plots', True):
            plt.figure(figsize=(10, 6))
            sns.histplot(data[column], kde=True)
            plt.title(f'Distribution of {column}')
            plt.tight_layout()
            
            # Save plot
            plot_path = f'/tmp/descriptive_{column}.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return {
                'statistics': stats.to_dict(),
                'plot_path': plot_path
            }
        
        return {'statistics': stats.to_dict()}
```

### View Separation
```python
# views/analysis_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from tools.descriptive_stats import DescriptiveStatsTool
from utils.llm_context import LLMContextManager

@csrf_exempt
@require_http_methods(["POST"])
def execute_analysis(request):
    """Execute analysis tool with LLM context"""
    tool_id = request.POST.get('tool_id')
    session_id = request.POST.get('session_id')
    
    # Get LLM context (last 10 messages)
    context_manager = LLMContextManager()
    context = context_manager.get_context(session_id, 'analysis_context')
    
    # Execute tool
    if tool_id == 'descriptive_stats':
        tool = DescriptiveStatsTool()
        result = tool.execute(data, parameters)
        
        # Update LLM context with new analysis
        context_manager.update_context(session_id, 'analysis_context', {
            'role': 'assistant',
            'content': f'Analysis completed: {result}',
            'timestamp': timezone.now()
        })
        
        return JsonResponse({'success': True, 'result': result})
    
    return JsonResponse({'success': False, 'error': 'Invalid tool'})
```

### LLM Context Management
```python
# utils/llm_context.py
from django.utils import timezone
from .models import LLMContextCache, ChatMessage
import hashlib
import json

class LLMContextManager:
    def __init__(self):
        self.max_messages = 10
    
    def get_context(self, session_id, context_type='chat_history'):
        """Get last 10 messages for LLM context"""
        try:
            context = LLMContextCache.objects.get(
                session_id=session_id,
                context_type=context_type,
                is_active=True
            )
            return context.context_data
        except LLMContextCache.DoesNotExist:
            return []
    
    def update_context(self, session_id, context_type, new_message):
        """Update LLM context with new message"""
        # Get existing context
        messages = self.get_context(session_id, context_type)
        
        # Add new message
        messages.append(new_message)
        
        # Keep only last 10 messages
        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages:]
        
        # Create context hash
        context_hash = hashlib.md5(
            json.dumps(messages, sort_keys=True).encode()
        ).hexdigest()
        
        # Update or create context
        context, created = LLMContextCache.objects.update_or_create(
            session_id=session_id,
            context_type=context_type,
            defaults={
                'context_data': messages,
                'message_count': len(messages),
                'context_hash': context_hash,
                'is_active': True,
                'last_updated': timezone.now()
            }
        )
        
        return context
    
    def get_llm_prompt_with_context(self, session_id, user_message):
        """Get LLM prompt with context for intelligent responses"""
        context = self.get_context(session_id, 'chat_history')
        
        # Build context string
        context_string = ""
        for msg in context:
            context_string += f"{msg['role']}: {msg['content']}\n"
        
        # Create full prompt
        prompt = f"""
        Previous conversation context:
        {context_string}
        
        Current user message: {user_message}
        
        Please provide a helpful response based on the context and current message.
        """
        
        return prompt
```

### LLM Batch Processing & Image Management
```python
# utils/llm_batch_processor.py
import base64
import os
from django.conf import settings
from .models import GeneratedImage, AnalysisResult
import google.generativeai as genai

class LLMBatchProcessor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.batch_size = settings.LLM_BATCH_SIZE
        self.max_images = settings.LLM_MAX_IMAGES_PER_BATCH
    
    def process_analysis_batch(self, session_id, analysis_results, prompt_template=None):
        """Process multiple analysis results in batch with LLM"""
        if not prompt_template:
            prompt_template = "Analyze the following analysis results and provide insights:"
        
        # Prepare batch data
        batch_data = []
        for result in analysis_results:
            result_data = {
                'result_id': result['result_id'],
                'result_type': result['result_type'],
                'data': result['data']
            }
            
            # Add images if present
            if 'images' in result:
                result_data['images'] = self._prepare_images_for_llm(result['images'])
            
            batch_data.append(result_data)
        
        # Create batch prompt
        batch_prompt = self._create_batch_prompt(prompt_template, batch_data)
        
        # Process with LLM
        response = self.model.generate_content(batch_prompt)
        
        # Parse and format response
        formatted_response = self._parse_llm_response(response.text)
        
        return {
            'success': True,
            'batch_id': f"batch_{session_id}_{timezone.now().timestamp()}",
            'results': formatted_response
        }
    
    def _prepare_images_for_llm(self, images):
        """Prepare images for LLM processing (base64 encoding)"""
        prepared_images = []
        
        for image in images[:self.max_images]:  # Limit images per batch
            image_obj = GeneratedImage.objects.get(id=image['image_id'])
            
            # Read and encode image
            with open(image_obj.file_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            prepared_images.append({
                'image_id': image_obj.id,
                'image_type': image_obj.image_type,
                'base64_data': image_data,
                'access_url': image_obj.access_url,
                'description': f"{image_obj.image_type} visualization"
            })
        
        return prepared_images
    
    def _create_batch_prompt(self, template, batch_data):
        """Create comprehensive prompt for batch processing"""
        prompt = f"{template}\n\n"
        
        for i, result in enumerate(batch_data, 1):
            prompt += f"\n--- Analysis Result {i} ---\n"
            prompt += f"Type: {result['result_type']}\n"
            prompt += f"Data: {json.dumps(result['data'], indent=2)}\n"
            
            if 'images' in result:
                prompt += f"Images: {len(result['images'])} visualization(s)\n"
                for img in result['images']:
                    prompt += f"- {img['description']}: {img['access_url']}\n"
        
        prompt += "\nPlease provide:\n"
        prompt += "1. Overall insights from all results\n"
        prompt += "2. Specific interpretations for each result\n"
        prompt += "3. Formatted tables for statistical data\n"
        prompt += "4. Descriptions of visualizations\n"
        prompt += "5. Recommendations based on the analysis\n"
        
        return prompt
    
    def _parse_llm_response(self, response_text):
        """Parse LLM response and format for different content types"""
        # This would parse the LLM response and extract:
        # - Text insights
        # - Formatted tables
        # - Image descriptions
        # - Recommendations
        
        return {
            'overall_insights': response_text,
            'formatted_tables': [],  # Extract tables from response
            'image_descriptions': [],  # Extract image descriptions
            'recommendations': []  # Extract recommendations
        }

# utils/image_manager.py
import os
import base64
from django.core.files.storage import default_storage
from django.conf import settings
from .models import GeneratedImage

class ImageManager:
    def __init__(self):
        self.media_root = settings.MEDIA_ROOT
        self.images_dir = settings.GENERATED_IMAGES_DIR
        self.session_dir = settings.SESSION_IMAGES_DIR
    
    def save_generated_image(self, session_id, analysis_result_id, tool_id, 
                           image_data, image_type, filename):
        """Save generated image with proper organization"""
        # Create session directory
        session_path = os.path.join(self.session_dir, session_id)
        os.makedirs(session_path, exist_ok=True)
        
        # Generate unique filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{image_type}_{timestamp}_{filename}"
        file_path = os.path.join(session_path, unique_filename)
        
        # Save image file
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # Get image metadata
        from PIL import Image
        with Image.open(file_path) as img:
            width, height = img.size
        
        # Create database record
        image_obj = GeneratedImage.objects.create(
            session_id=session_id,
            analysis_result_id=analysis_result_id,
            tool_id=tool_id,
            image_type=image_type,
            file_path=file_path,
            file_name=unique_filename,
            file_size=os.path.getsize(file_path),
            image_format='PNG',
            width=width,
            height=height,
            dpi=300,
            access_url=f"/media/generated_images/sessions/{session_id}/{unique_filename}"
        )
        
        # Generate base64 data for LLM
        if settings.BASE64_ENCODING:
            with open(file_path, 'rb') as img_file:
                image_obj.base64_data = base64.b64encode(img_file.read()).decode('utf-8')
                image_obj.save()
        
        return image_obj
    
    def get_image_for_llm(self, image_id, format='base64'):
        """Get image in format suitable for LLM processing"""
        try:
            image_obj = GeneratedImage.objects.get(id=image_id)
            
            if format == 'base64':
                return image_obj.base64_data
            elif format == 'url':
                return image_obj.access_url
            elif format == 'path':
                return image_obj.file_path
            else:
                return None
        except GeneratedImage.DoesNotExist:
            return None
    
    def cleanup_expired_images(self):
        """Clean up expired images to save storage"""
        expired_images = GeneratedImage.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        for image in expired_images:
            if os.path.exists(image.file_path):
                os.remove(image.file_path)
            image.delete()
```

### LangChain Sandbox & Code Execution
```python
# utils/sandbox_executor.py
import os
import sys
import uuid
import time
import psutil
import subprocess
import tempfile
import ast
import re
from django.conf import settings
from django.utils import timezone
from .models import SandboxExecution, GeneratedImage
from .llm_context import LLMContextManager
import google.generativeai as genai

class SandboxExecutor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.max_execution_time = settings.SANDBOX_MAX_EXECUTION_TIME
        self.max_memory_mb = settings.SANDBOX_MAX_MEMORY_MB
        self.max_retries = settings.SANDBOX_MAX_RETRIES
        self.allowed_libraries = settings.SANDBOX_ALLOWED_LIBRARIES
        self.blocked_imports = settings.SANDBOX_BLOCKED_IMPORTS
        self.blocked_functions = settings.SANDBOX_BLOCKED_FUNCTIONS
    
    def execute_user_query(self, session_id, user_id, user_query, context_data=None):
        """Execute user query in secure sandbox"""
        execution_id = str(uuid.uuid4())
        
        # Create execution record
        execution = SandboxExecution.objects.create(
            session_id=session_id,
            user_id=user_id,
            execution_id=execution_id,
            user_query=user_query,
            execution_status='pending',
            max_retries=self.max_retries
        )
        
        try:
            # Generate Python code from user query
            generated_code = self._generate_code(user_query, context_data)
            execution.generated_code = generated_code
            execution.save()
            
            # Execute code in sandbox
            result = self._execute_in_sandbox(execution_id, generated_code)
            
            # Update execution record
            execution.execution_status = 'completed'
            execution.execution_result = result['output']
            execution.execution_time_ms = result['execution_time_ms']
            execution.memory_used_mb = result['memory_used_mb']
            execution.cpu_time_ms = result['cpu_time_ms']
            execution.output_data = result['formatted_output']
            execution.images_generated = result['images_generated']
            execution.tables_generated = result['tables_generated']
            execution.variables_created = result['variables_created']
            execution.libraries_used = result['libraries_used']
            execution.completed_at = timezone.now()
            execution.save()
            
            return {
                'success': True,
                'execution_id': execution_id,
                'execution_status': 'completed',
                'output_data': result['formatted_output'],
                'images_generated': result['images_generated'],
                'tables_generated': result['tables_generated'],
                'execution_time_ms': result['execution_time_ms'],
                'memory_used_mb': result['memory_used_mb']
            }
            
        except Exception as e:
            # Handle execution errors
            execution.execution_status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = timezone.now()
            execution.save()
            
            # Generate LLM suggestions for fixing errors
            suggestions = self._generate_error_suggestions(user_query, str(e), generated_code)
            
            return {
                'success': False,
                'execution_id': execution_id,
                'execution_status': 'failed',
                'error_message': str(e),
                'suggestions': suggestions
            }
    
    def _generate_code(self, user_query, context_data):
        """Generate Python code from user query using LLM"""
        # Get context from session
        context_manager = LLMContextManager()
        context = context_manager.get_context(context_data.get('session_id', ''), 'analysis_context')
        
        # Build prompt for code generation
        prompt = f"""
        You are a Python data analysis expert. Generate secure Python code for the following query:
        
        User Query: {user_query}
        
        Context Data: {context_data or 'No additional context'}
        
        Requirements:
        1. Use only these approved libraries: {', '.join(self.allowed_libraries)}
        2. Do NOT use: {', '.join(self.blocked_imports)}
        3. Do NOT use these functions: {', '.join(self.blocked_functions)}
        4. Use matplotlib with Agg backend: matplotlib.use('Agg')
        5. Save plots to: /tmp/sandbox_output/
        6. Return results as JSON with keys: 'data', 'plots', 'tables'
        7. Handle errors gracefully
        8. Keep code simple and focused
        
        Generate only the Python code, no explanations:
        """
        
        response = self.model.generate_content(prompt)
        return response.text.strip()
    
    def _execute_in_sandbox(self, execution_id, code):
        """Execute code in secure sandbox environment"""
        # Create temporary directory for execution
        with tempfile.TemporaryDirectory(dir=settings.SANDBOX_TEMP_DIR) as temp_dir:
            # Create sandbox environment
            sandbox_env = self._create_sandbox_environment(temp_dir)
            
            # Write code to file
            code_file = os.path.join(temp_dir, 'execute.py')
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Execute code with resource limits
            start_time = time.time()
            process = subprocess.Popen(
                [sys.executable, code_file],
                cwd=temp_dir,
                env=sandbox_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=self._set_limits
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.max_execution_time)
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Get memory usage
                memory_used_mb = psutil.Process(process.pid).memory_info().rss / 1024 / 1024
                
                if process.returncode == 0:
                    # Parse output
                    output = stdout.decode('utf-8')
                    result = self._parse_execution_output(output, temp_dir)
                    
                    return {
                        'output': result,
                        'execution_time_ms': execution_time_ms,
                        'memory_used_mb': memory_used_mb,
                        'cpu_time_ms': execution_time_ms,  # Simplified
                        'formatted_output': self._format_output_for_user(result),
                        'images_generated': result.get('plots', []),
                        'tables_generated': result.get('tables', []),
                        'variables_created': result.get('variables', {}),
                        'libraries_used': self._extract_libraries_used(code)
                    }
                else:
                    raise Exception(f"Execution failed: {stderr.decode('utf-8')}")
                    
            except subprocess.TimeoutExpired:
                process.kill()
                raise Exception("Execution timeout exceeded")
    
    def _create_sandbox_environment(self, temp_dir):
        """Create secure sandbox environment"""
        env = os.environ.copy()
        
        # Set up sandbox environment
        env['PYTHONPATH'] = temp_dir
        env['SANDBOX_MODE'] = '1'
        env['TMPDIR'] = temp_dir
        
        # Create output directory
        output_dir = os.path.join(temp_dir, 'sandbox_output')
        os.makedirs(output_dir, exist_ok=True)
        env['SANDBOX_OUTPUT_DIR'] = output_dir
        
        return env
    
    def _set_limits(self):
        """Set resource limits for sandbox process"""
        import resource
        
        # Set memory limit
        resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_mb * 1024 * 1024, -1))
        
        # Set CPU time limit
        resource.setrlimit(resource.RLIMIT_CPU, (self.max_execution_time, -1))
    
    def _parse_execution_output(self, output, temp_dir):
        """Parse execution output and extract results"""
        try:
            # Try to parse as JSON
            import json
            result = json.loads(output)
            return result
        except:
            # Fallback to text output
            return {
                'text_output': output,
                'plots': self._find_generated_plots(temp_dir),
                'tables': [],
                'variables': {}
            }
    
    def _find_generated_plots(self, temp_dir):
        """Find generated plot files"""
        plots = []
        output_dir = os.path.join(temp_dir, 'sandbox_output')
        
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.endswith(('.png', '.jpg', '.jpeg')):
                    plots.append(os.path.join(output_dir, file))
        
        return plots
    
    def _format_output_for_user(self, result):
        """Format execution result for user display"""
        formatted = {
            'text': result.get('text_output', ''),
            'tables': result.get('tables', []),
            'plots': result.get('plots', []),
            'summary': f"Execution completed successfully. Generated {len(result.get('plots', []))} plots and {len(result.get('tables', []))} tables."
        }
        return formatted
    
    def _extract_libraries_used(self, code):
        """Extract libraries used in code"""
        libraries = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        libraries.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        libraries.append(node.module)
        except:
            pass
        
        return libraries
    
    def _generate_error_suggestions(self, user_query, error_message, generated_code):
        """Generate LLM suggestions for fixing errors"""
        prompt = f"""
        The following Python code failed to execute:
        
        User Query: {user_query}
        Generated Code: {generated_code}
        Error Message: {error_message}
        
        Please provide 3-5 specific suggestions to fix this error. Focus on:
        1. Missing imports or libraries
        2. Incorrect syntax or logic
        3. Variable name issues
        4. Data type problems
        5. Resource or permission issues
        
        Provide concise, actionable suggestions:
        """
        
        try:
            response = self.model.generate_content(prompt)
            suggestions = response.text.strip().split('\n')
            return [s.strip() for s in suggestions if s.strip()]
        except:
            return ["Check your code syntax", "Verify all imports are available", "Check variable names and data types"]

# utils/sandbox_security.py
import ast
import re

class SandboxSecurity:
    def __init__(self):
        self.blocked_imports = settings.SANDBOX_BLOCKED_IMPORTS
        self.blocked_functions = settings.SANDBOX_BLOCKED_FUNCTIONS
        self.allowed_libraries = settings.SANDBOX_ALLOWED_LIBRARIES
    
    def validate_code(self, code):
        """Validate code for security violations"""
        violations = []
        
        try:
            tree = ast.parse(code)
            
            # Check for blocked imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.blocked_imports:
                            violations.append(f"Blocked import: {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.blocked_imports:
                        violations.append(f"Blocked import: {node.module}")
                
                # Check for blocked function calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.blocked_functions:
                            violations.append(f"Blocked function: {node.func.id}")
                
                # Check for dangerous operations
                elif isinstance(node, ast.Exec):
                    violations.append("Blocked operation: exec()")
                elif isinstance(node, ast.Eval):
                    violations.append("Blocked operation: eval()")
        
        except SyntaxError as e:
            violations.append(f"Syntax error: {str(e)}")
        
        return violations
    
    def sanitize_code(self, code):
        """Sanitize code to remove dangerous operations"""
        # Remove dangerous function calls
        for func in self.blocked_functions:
            code = re.sub(rf'\b{func}\s*\(', f'# BLOCKED: {func}(', code)
        
        # Remove dangerous imports
        for imp in self.blocked_imports:
            code = re.sub(rf'^import\s+{imp}\b', f'# BLOCKED: import {imp}', code, flags=re.MULTILINE)
            code = re.sub(rf'^from\s+{imp}\b', f'# BLOCKED: from {imp}', code, flags=re.MULTILINE)
        
        return code
```

### Report Generation & Document Export
```python
# utils/report_generator.py
import os
import uuid
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import ReportGeneration, AnalysisSession, ChatMessage, AnalysisResult, SandboxExecution, GeneratedImage
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.shared import OxmlElement, qn
import asyncio
import threading

class ReportGenerator:
    def __init__(self):
        self.templates_dir = settings.REPORT_TEMPLATES_DIR
        self.output_dir = settings.REPORT_OUTPUT_DIR
        self.max_file_size = settings.REPORT_MAX_FILE_SIZE
        self.generation_timeout = settings.REPORT_GENERATION_TIMEOUT
        self.templates = settings.REPORT_TEMPLATES
    
    def generate_report_async(self, session_id, user_id, report_title, report_type, 
                            content_selection, template_id, generation_settings):
        """Generate report asynchronously"""
        report_id = str(uuid.uuid4())
        
        # Create report record
        report = ReportGeneration.objects.create(
            session_id=session_id,
            user_id=user_id,
            report_id=report_id,
            report_title=report_title,
            report_type=report_type,
            content_selection=content_selection,
            template_id=template_id,
            generation_settings=generation_settings,
            report_status='pending',
            generation_progress=0
        )
        
        # Start generation in background thread
        thread = threading.Thread(
            target=self._generate_report_worker,
            args=(report_id, session_id, content_selection, template_id, generation_settings)
        )
        thread.daemon = True
        thread.start()
        
        return {
            'success': True,
            'report_id': report_id,
            'report_status': 'pending',
            'estimated_completion_time': self._estimate_completion_time(session_id)
        }
    
    def _generate_report_worker(self, report_id, session_id, content_selection, 
                               template_id, generation_settings):
        """Background worker for report generation"""
        try:
            report = ReportGeneration.objects.get(report_id=report_id)
            report.report_status = 'generating'
            report.generation_progress = 10
            report.save()
            
            # Create Word document
            doc = self._create_document_template(template_id, generation_settings)
            
            # Add cover page
            if generation_settings.get('include_cover_page', True):
                self._add_cover_page(doc, report.report_title, session_id)
                report.generation_progress = 20
                report.save()
            
            # Add table of contents
            if generation_settings.get('include_table_of_contents', True):
                self._add_table_of_contents(doc)
                report.generation_progress = 30
                report.save()
            
            # Add executive summary
            if generation_settings.get('include_executive_summary', True):
                self._add_executive_summary(doc, session_id, content_selection)
                report.generation_progress = 40
                report.save()
            
            # Add methodology
            if generation_settings.get('include_methodology', True):
                self._add_methodology(doc, session_id)
                report.generation_progress = 50
                report.save()
            
            # Add analysis results
            self._add_analysis_results(doc, session_id, content_selection)
            report.generation_progress = 70
            report.save()
            
            # Add chat messages and LLM responses
            if content_selection.get('include_chat_messages', True):
                self._add_chat_messages(doc, session_id, content_selection)
                report.generation_progress = 80
                report.save()
            
            # Add sandbox executions
            if content_selection.get('include_sandbox_executions', True):
                self._add_sandbox_executions(doc, session_id, content_selection)
                report.generation_progress = 90
                report.save()
            
            # Add appendix
            if generation_settings.get('include_appendix', True):
                self._add_appendix(doc, session_id, content_selection)
                report.generation_progress = 95
                report.save()
            
            # Save document
            filename = f"{report.report_title.replace(' ', '_')}_{report_id[:8]}.docx"
            file_path = os.path.join(self.output_dir, filename)
            doc.save(file_path)
            
            # Update report record
            report.report_status = 'completed'
            report.generation_progress = 100
            report.file_path = file_path
            report.file_name = filename
            report.file_size = os.path.getsize(file_path)
            report.generation_time_ms = int((timezone.now() - report.created_at).total_seconds() * 1000)
            report.completed_at = timezone.now()
            report.expires_at = timezone.now() + timedelta(days=settings.REPORT_RETENTION_DAYS)
            report.save()
            
        except Exception as e:
            report = ReportGeneration.objects.get(report_id=report_id)
            report.report_status = 'failed'
            report.error_message = str(e)
            report.completed_at = timezone.now()
            report.save()
    
    def _create_document_template(self, template_id, generation_settings):
        """Create Word document with template styling"""
        doc = Document()
        
        # Get template settings
        template = self.templates.get(template_id, self.templates['default_professional'])
        
        # Set document properties
        doc.core_properties.title = "Analysis Report"
        doc.core_properties.author = "Analytics Platform"
        doc.core_properties.created = datetime.now()
        
        # Set page orientation
        if template['page_orientation'] == 'landscape':
            section = doc.sections[0]
            section.orientation = 1  # Landscape
        
        # Apply template styling
        self._apply_template_styling(doc, template, generation_settings)
        
        return doc
    
    def _apply_template_styling(self, doc, template, generation_settings):
        """Apply template-specific styling to document"""
        # Define color schemes
        color_schemes = {
            'professional': {
                'primary': RGBColor(0, 51, 102),      # Dark blue
                'secondary': RGBColor(102, 153, 204), # Light blue
                'accent': RGBColor(255, 140, 0),      # Orange
                'text': RGBColor(51, 51, 51)          # Dark gray
            },
            'corporate': {
                'primary': RGBColor(0, 0, 0),         # Black
                'secondary': RGBColor(128, 128, 128), # Gray
                'accent': RGBColor(0, 100, 0),        # Green
                'text': RGBColor(0, 0, 0)             # Black
            },
            'academic': {
                'primary': RGBColor(0, 0, 0),         # Black
                'secondary': RGBColor(100, 100, 100), # Gray
                'accent': RGBColor(0, 0, 139),        # Dark blue
                'text': RGBColor(0, 0, 0)             # Black
            },
            'creative': {
                'primary': RGBColor(138, 43, 226),    # Blue violet
                'secondary': RGBColor(72, 61, 139),   # Dark slate blue
                'accent': RGBColor(255, 20, 147),     # Deep pink
                'text': RGBColor(25, 25, 112)         # Midnight blue
            }
        }
        
        colors = color_schemes.get(template['color_scheme'], color_schemes['professional'])
        
        # Create custom styles
        styles = doc.styles
        
        # Title style
        title_style = styles.add_style('CustomTitle', WD_STYLE_TYPE.PARAGRAPH)
        title_style.font.name = template['font_family']
        title_style.font.size = Pt(24)
        title_style.font.color.rgb = colors['primary']
        title_style.font.bold = True
        title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_style.paragraph_format.space_after = Pt(12)
        
        # Heading 1 style
        h1_style = styles.add_style('CustomHeading1', WD_STYLE_TYPE.PARAGRAPH)
        h1_style.font.name = template['font_family']
        h1_style.font.size = Pt(18)
        h1_style.font.color.rgb = colors['primary']
        h1_style.font.bold = True
        h1_style.paragraph_format.space_before = Pt(12)
        h1_style.paragraph_format.space_after = Pt(6)
        
        # Heading 2 style
        h2_style = styles.add_style('CustomHeading2', WD_STYLE_TYPE.PARAGRAPH)
        h2_style.font.name = template['font_family']
        h2_style.font.size = Pt(14)
        h2_style.font.color.rgb = colors['secondary']
        h2_style.font.bold = True
        h2_style.paragraph_format.space_before = Pt(10)
        h2_style.paragraph_format.space_after = Pt(4)
        
        # Body text style
        body_style = styles.add_style('CustomBody', WD_STYLE_TYPE.PARAGRAPH)
        body_style.font.name = template['font_family']
        body_style.font.size = Pt(template['font_size'])
        body_style.font.color.rgb = colors['text']
        body_style.paragraph_format.space_after = Pt(6)
        body_style.paragraph_format.line_spacing = 1.15
    
    def _add_cover_page(self, doc, title, session_id):
        """Add professional cover page"""
        # Title
        title_para = doc.add_paragraph()
        title_para.style = 'CustomTitle'
        title_para.add_run(title)
        
        # Subtitle
        subtitle_para = doc.add_paragraph()
        subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_para.add_run("Data Analysis Report").font.size = Pt(16)
        subtitle_para.add_run("\nGenerated by Analytics Platform").font.size = Pt(12)
        subtitle_para.add_run(f"\nSession ID: {session_id}").font.size = Pt(10)
        
        # Date
        date_para = doc.add_paragraph()
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        date_para.add_run(f"Generated on: {datetime.now().strftime('%B %d, %Y')}").font.size = Pt(12)
        
        # Add page break
        doc.add_page_break()
    
    def _add_table_of_contents(self, doc):
        """Add table of contents"""
        toc_para = doc.add_paragraph()
        toc_para.style = 'CustomHeading1'
        toc_para.add_run("Table of Contents")
        
        # TOC entries (simplified - in real implementation, would be dynamic)
        toc_entries = [
            "Executive Summary",
            "Methodology",
            "Analysis Results",
            "Data Visualizations",
            "Statistical Findings",
            "Recommendations",
            "Appendix"
        ]
        
        for entry in toc_entries:
            toc_item = doc.add_paragraph()
            toc_item.style = 'CustomBody'
            toc_item.add_run(f"• {entry}")
    
    def _add_executive_summary(self, doc, session_id, content_selection):
        """Add executive summary section"""
        summary_para = doc.add_paragraph()
        summary_para.style = 'CustomHeading1'
        summary_para.add_run("Executive Summary")
        
        # Get session data for summary
        session = AnalysisSession.objects.get(session_id=session_id)
        
        # Generate summary content
        summary_content = f"""
        This report presents a comprehensive analysis of the dataset '{session.dataset.name}' 
        conducted on {session.created_at.strftime('%B %d, %Y')}. The analysis utilized advanced 
        statistical methods and machine learning techniques to extract meaningful insights 
        from the data.
        
        Key findings include:
        • Dataset contains {session.dataset.row_count:,} rows and {session.dataset.column_count} columns
        • Analysis completed in {session.analysis_count} individual analyses
        • Generated {session.visualization_count} data visualizations
        • Identified {session.insight_count} key insights and recommendations
        
        The methodology employed ensures statistical rigor while maintaining practical 
        applicability for business decision-making.
        """
        
        summary_text = doc.add_paragraph()
        summary_text.style = 'CustomBody'
        summary_text.add_run(summary_content.strip())
    
    def _add_methodology(self, doc, session_id):
        """Add methodology section"""
        method_para = doc.add_paragraph()
        method_para.style = 'CustomHeading1'
        method_para.add_run("Methodology")
        
        methodology_content = """
        This analysis employed a systematic approach combining statistical analysis, 
        data visualization, and machine learning techniques:
        
        1. Data Preprocessing: Raw data was cleaned, validated, and transformed into 
           a standardized format suitable for analysis.
        
        2. Exploratory Data Analysis: Initial exploration of data distributions, 
           correlations, and patterns using descriptive statistics and visualizations.
        
        3. Statistical Analysis: Application of appropriate statistical tests and 
           models based on data characteristics and research questions.
        
        4. Machine Learning: Implementation of supervised and unsupervised learning 
           algorithms to identify patterns and make predictions.
        
        5. Visualization: Creation of comprehensive charts and graphs to communicate 
           findings effectively.
        
        6. Interpretation: AI-powered analysis of results to provide insights and 
           recommendations.
        """
        
        method_text = doc.add_paragraph()
        method_text.style = 'CustomBody'
        method_text.add_run(methodology_content.strip())
    
    def _add_analysis_results(self, doc, session_id, content_selection):
        """Add analysis results section"""
        results_para = doc.add_paragraph()
        results_para.style = 'CustomHeading1'
        results_para.add_run("Analysis Results")
        
        # Get analysis results
        analysis_results = AnalysisResult.objects.filter(session_id=session_id)
        
        for i, result in enumerate(analysis_results, 1):
            # Result title
            result_title = doc.add_paragraph()
            result_title.style = 'CustomHeading2'
            result_title.add_run(f"Analysis {i}: {result.tool.name}")
            
            # Result description
            if result.description:
                desc_para = doc.add_paragraph()
                desc_para.style = 'CustomBody'
                desc_para.add_run(result.description)
            
            # Add result data as table if available
            if result.result_data and content_selection.get('include_tables', True):
                self._add_result_table(doc, result.result_data)
            
            # Add generated images if available
            if content_selection.get('include_images', True):
                self._add_result_images(doc, result)
    
    def _add_chat_messages(self, doc, session_id, content_selection):
        """Add chat messages and LLM responses"""
        if not content_selection.get('include_chat_messages', True):
            return
        
        chat_para = doc.add_paragraph()
        chat_para.style = 'CustomHeading1'
        chat_para.add_run("Analysis Discussion")
        
        # Get chat messages
        chat_messages = ChatMessage.objects.filter(session_id=session_id).order_by('created_at')
        
        for message in chat_messages:
            # Message header
            msg_header = doc.add_paragraph()
            msg_header.style = 'CustomHeading2'
            msg_header.add_run(f"{message.role.title()}: {message.created_at.strftime('%H:%M:%S')}")
            
            # Message content
            msg_content = doc.add_paragraph()
            msg_content.style = 'CustomBody'
            msg_content.add_run(message.content)
    
    def _add_sandbox_executions(self, doc, session_id, content_selection):
        """Add sandbox execution results"""
        if not content_selection.get('include_sandbox_executions', True):
            return
        
        sandbox_para = doc.add_paragraph()
        sandbox_para.style = 'CustomHeading1'
        sandbox_para.add_run("Dynamic Analysis Results")
        
        # Get sandbox executions
        executions = SandboxExecution.objects.filter(
            session_id=session_id, 
            execution_status='completed'
        ).order_by('created_at')
        
        for i, execution in enumerate(executions, 1):
            # Execution header
            exec_header = doc.add_paragraph()
            exec_header.style = 'CustomHeading2'
            exec_header.add_run(f"Dynamic Analysis {i}: {execution.user_query}")
            
            # Execution results
            if execution.output_data:
                exec_content = doc.add_paragraph()
                exec_content.style = 'CustomBody'
                exec_content.add_run(str(execution.output_data))
    
    def _add_result_table(self, doc, result_data):
        """Add result data as formatted table"""
        if not isinstance(result_data, dict):
            return
        
        # Create table
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        # Add header
        header_cells = table.rows[0].cells
        header_cells[0].text = 'Metric'
        header_cells[1].text = 'Value'
        
        # Add data rows
        for key, value in result_data.items():
            row_cells = table.add_row().cells
            row_cells[0].text = str(key)
            row_cells[1].text = str(value)
    
    def _add_result_images(self, doc, result):
        """Add generated images to document"""
        # Get associated images
        images = GeneratedImage.objects.filter(
            analysis_result=result,
            image_format='PNG'
        )
        
        for image in images:
            if os.path.exists(image.file_path):
                try:
                    # Add image to document
                    doc.add_picture(image.file_path, width=Inches(6))
                    
                    # Add caption
                    caption = doc.add_paragraph()
                    caption.style = 'CustomBody'
                    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    caption.add_run(f"Figure: {image.image_type.replace('_', ' ').title()}")
                except Exception as e:
                    # If image can't be added, add placeholder text
                    placeholder = doc.add_paragraph()
                    placeholder.style = 'CustomBody'
                    placeholder.add_run(f"[Image: {image.image_type} - {image.file_name}]")
    
    def _add_appendix(self, doc, session_id, content_selection):
        """Add appendix with additional details"""
        appendix_para = doc.add_paragraph()
        appendix_para.style = 'CustomHeading1'
        appendix_para.add_run("Appendix")
        
        # Add technical details
        tech_para = doc.add_paragraph()
        tech_para.style = 'CustomHeading2'
        tech_para.add_run("Technical Specifications")
        
        tech_content = f"""
        • Analysis Platform: Analytics Platform v1.0
        • Session ID: {session_id}
        • Generation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        • Report Template: Professional
        • Data Processing: Python with pandas, numpy, matplotlib, seaborn
        • AI Integration: Google AI API with LangChain
        • Security: Sandbox execution with resource limits
        """
        
        tech_text = doc.add_paragraph()
        tech_text.style = 'CustomBody'
        tech_text.add_run(tech_content.strip())
    
    def _estimate_completion_time(self, session_id):
        """Estimate report generation completion time"""
        # Get session data to estimate complexity
        session = AnalysisSession.objects.get(session_id=session_id)
        
        # Base time in seconds
        base_time = 30
        
        # Add time based on content complexity
        content_multiplier = 1
        content_multiplier += session.analysis_count * 2  # 2 seconds per analysis
        content_multiplier += session.visualization_count * 1  # 1 second per visualization
        content_multiplier += session.chat_message_count * 0.5  # 0.5 seconds per message
        
        estimated_time = int(base_time * content_multiplier)
        return min(estimated_time, 300)  # Cap at 5 minutes

# utils/report_manager.py
class ReportManager:
    def __init__(self):
        self.generator = ReportGenerator()
    
    def get_available_templates(self):
        """Get list of available report templates"""
        templates = []
        for template_id, template_data in settings.REPORT_TEMPLATES.items():
            templates.append({
                'template_id': template_id,
                'template_name': template_data['name'],
                'template_description': template_data['description'],
                'color_scheme': template_data['color_scheme'],
                'font_family': template_data['font_family'],
                'font_size': template_data['font_size'],
                'page_orientation': template_data['page_orientation']
            })
        return templates
    
    def get_report_status(self, report_id):
        """Get report generation status"""
        try:
            report = ReportGeneration.objects.get(report_id=report_id)
            return {
                'report': report,
                'status': report.report_status,
                'progress_percentage': report.generation_progress,
                'estimated_remaining_time': self._calculate_remaining_time(report)
            }
        except ReportGeneration.DoesNotExist:
            return None
    
    def download_report(self, report_id, format='docx'):
        """Download generated report"""
        try:
            report = ReportGeneration.objects.get(report_id=report_id)
            
            if report.report_status != 'completed':
                return None
            
            # Update download count
            report.download_count += 1
            report.last_downloaded_at = timezone.now()
            report.save()
            
            return {
                'file_path': report.file_path,
                'file_name': report.file_name,
                'file_size': report.file_size,
                'download_count': report.download_count
            }
        except ReportGeneration.DoesNotExist:
            return None
    
    def _calculate_remaining_time(self, report):
        """Calculate estimated remaining time for report generation"""
        if report.report_status == 'completed':
            return 0
        
        # Simple estimation based on current progress
        if report.generation_progress == 0:
            return 300  # 5 minutes if not started
        
        # Estimate based on progress
        remaining_progress = 100 - report.generation_progress
        time_per_progress = 3  # 3 seconds per progress point
        return remaining_progress * time_per_progress
```

### Performance Optimization & Memory Efficiency
```python
# utils/performance_optimizer.py
import gc
import psutil
import threading
import time
from contextlib import contextmanager
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from functools import wraps
import pandas as pd
import numpy as np
from PIL import Image
import io

class PerformanceOptimizer:
    def __init__(self):
        self.max_memory = settings.MAX_MEMORY_PER_OPERATION
        self.cleanup_interval = settings.MEMORY_CLEANUP_INTERVAL
        self.monitoring_enabled = True
    
    @contextmanager
    def memory_monitor(self, operation_name):
        """Monitor memory usage during operations"""
        initial_memory = psutil.Process().memory_info().rss
        start_time = time.time()
        
        try:
            yield
        finally:
            final_memory = psutil.Process().memory_info().rss
            memory_used = final_memory - initial_memory
            duration = time.time() - start_time
            
            # Log performance metrics
            self._log_performance_metrics(operation_name, memory_used, duration)
            
            # Force garbage collection
            gc.collect()
    
    def optimize_dataframe(self, df):
        """Optimize DataFrame memory usage"""
        initial_memory = df.memory_usage(deep=True).sum()
        
        # Convert object columns to category if beneficial
        for col in df.select_dtypes(include=['object']):
            if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')
        
        # Downcast numeric columns
        for col in df.select_dtypes(include=['int64']):
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        for col in df.select_dtypes(include=['float64']):
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        final_memory = df.memory_usage(deep=True).sum()
        reduction = (initial_memory - final_memory) / initial_memory * 100
        
        return df, reduction
    
    def stream_large_file(self, file_path, chunk_size=None):
        """Stream large files in chunks to avoid memory overload"""
        if chunk_size is None:
            chunk_size = settings.PARQUET_CHUNK_SIZE
        
        if file_path.endswith('.parquet'):
            return pd.read_parquet(file_path, engine='pyarrow')
        elif file_path.endswith('.csv'):
            return pd.read_csv(file_path, chunksize=chunk_size)
        else:
            raise ValueError("Unsupported file format for streaming")
    
    def compress_image(self, image_data, quality=None):
        """Compress images to reduce memory usage"""
        if quality is None:
            quality = settings.IMAGE_COMPRESSION_QUALITY
        
        # Open image
        img = Image.open(io.BytesIO(image_data))
        
        # Resize if too large
        max_width = settings.IMAGE_MAX_WIDTH
        max_height = settings.IMAGE_MAX_HEIGHT
        
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Compress
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        
        return output.getvalue()
    
    def optimize_database_query(self, queryset):
        """Optimize database queries with select_related and prefetch_related"""
        # Apply select_related for foreign keys
        if hasattr(queryset.model, '_meta'):
            foreign_keys = [f.name for f in queryset.model._meta.fields 
                          if f.many_to_one and f.related_model]
            
            if foreign_keys:
                queryset = queryset.select_related(*foreign_keys[:settings.SELECT_RELATED_DEPTH])
        
        # Apply prefetch_related for many-to-many and reverse foreign keys
        many_to_many = [f.name for f in queryset.model._meta.many_to_many]
        if many_to_many:
            queryset = queryset.prefetch_related(*many_to_many[:settings.PREFETCH_RELATED_DEPTH])
        
        return queryset
    
    def paginate_large_dataset(self, data, page_size=None):
        """Paginate large datasets to avoid memory overload"""
        if page_size is None:
            page_size = settings.PAGINATION_SIZE
        
        if isinstance(data, pd.DataFrame):
            total_pages = len(data) // page_size + (1 if len(data) % page_size else 0)
            
            for page in range(total_pages):
                start_idx = page * page_size
                end_idx = min((page + 1) * page_size, len(data))
                yield data.iloc[start_idx:end_idx], page + 1, total_pages
        
        elif hasattr(data, 'count'):  # Django QuerySet
            total_count = data.count()
            total_pages = total_count // page_size + (1 if total_count % page_size else 0)
            
            for page in range(total_pages):
                start_idx = page * page_size
                end_idx = min((page + 1) * page_size, total_count)
                yield data[start_idx:end_idx], page + 1, total_pages
    
    def cache_frequently_accessed_data(self, key, data, timeout=None):
        """Cache frequently accessed data with compression"""
        if timeout is None:
            timeout = settings.CACHE_DEFAULT_TIMEOUT
        
        # Compress large data before caching
        if isinstance(data, (pd.DataFrame, np.ndarray)):
            compressed_data = self._compress_data(data)
            cache.set(f"{key}_compressed", compressed_data, timeout)
        else:
            cache.set(key, data, timeout)
    
    def get_cached_data(self, key):
        """Retrieve cached data with decompression"""
        # Try compressed version first
        compressed_data = cache.get(f"{key}_compressed")
        if compressed_data:
            return self._decompress_data(compressed_data)
        
        # Fallback to regular cache
        return cache.get(key)
    
    def cleanup_session_data(self, session_id):
        """Clean up session data to free memory"""
        # Remove old cached data
        cache.delete_many([
            f"session_{session_id}_context",
            f"session_{session_id}_results",
            f"session_{session_id}_images"
        ])
        
        # Force garbage collection
        gc.collect()
    
    def monitor_system_resources(self):
        """Monitor system resources and trigger cleanup if needed"""
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent()
        
        if memory_percent > 85:  # High memory usage
            self._trigger_emergency_cleanup()
        
        if cpu_percent > 90:  # High CPU usage
            self._throttle_operations()
    
    def _log_performance_metrics(self, operation_name, memory_used, duration):
        """Log performance metrics for monitoring"""
        metrics = {
            'operation': operation_name,
            'memory_used_mb': memory_used / 1024 / 1024,
            'duration_seconds': duration,
            'timestamp': time.time()
        }
        
        # Store in cache for monitoring dashboard
        cache.set(f"metrics_{operation_name}_{int(time.time())}", metrics, 3600)
    
    def _compress_data(self, data):
        """Compress data for caching"""
        import pickle
        import gzip
        
        pickled_data = pickle.dumps(data)
        compressed_data = gzip.compress(pickled_data)
        return compressed_data
    
    def _decompress_data(self, compressed_data):
        """Decompress cached data"""
        import pickle
        import gzip
        
        pickled_data = gzip.decompress(compressed_data)
        return pickle.loads(pickled_data)
    
    def _trigger_emergency_cleanup(self):
        """Trigger emergency memory cleanup"""
        # Clear old cache entries
        cache.clear()
        
        # Force garbage collection
        gc.collect()
        
        # Log cleanup event
        self._log_performance_metrics("emergency_cleanup", 0, 0)
    
    def _throttle_operations(self):
        """Throttle operations during high CPU usage"""
        time.sleep(0.1)  # Brief pause to reduce CPU load

# Decorator for automatic memory optimization
def optimize_memory(operation_name=None):
    """Decorator to automatically optimize memory usage"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            optimizer = PerformanceOptimizer()
            name = operation_name or func.__name__
            
            with optimizer.memory_monitor(name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# utils/lazy_loader.py
class LazyDataLoader:
    """Lazy loading implementation for large datasets"""
    
    def __init__(self, data_source, chunk_size=None):
        self.data_source = data_source
        self.chunk_size = chunk_size or settings.PAGINATION_SIZE
        self._current_chunk = None
        self._current_index = 0
        self._total_items = None
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self._current_chunk is None or self._current_index >= len(self._current_chunk):
            self._load_next_chunk()
        
        if self._current_index >= len(self._current_chunk):
            raise StopIteration
        
        item = self._current_chunk[self._current_index]
        self._current_index += 1
        return item
    
    def _load_next_chunk(self):
        """Load next chunk of data"""
        start_idx = self._current_index
        end_idx = start_idx + self.chunk_size
        
        if isinstance(self.data_source, pd.DataFrame):
            self._current_chunk = self.data_source.iloc[start_idx:end_idx].values.tolist()
        elif hasattr(self.data_source, 'count'):  # Django QuerySet
            self._current_chunk = list(self.data_source[start_idx:end_idx])
        else:
            self._current_chunk = list(self.data_source[start_idx:end_idx])
        
        self._current_index = 0
    
    def get_total_count(self):
        """Get total number of items"""
        if self._total_items is None:
            if isinstance(self.data_source, pd.DataFrame):
                self._total_items = len(self.data_source)
            elif hasattr(self.data_source, 'count'):
                self._total_items = self.data_source.count()
            else:
                self._total_items = len(self.data_source)
        
        return self._total_items

# utils/image_optimizer.py
class ImageOptimizer:
    """Optimize images for memory efficiency"""
    
    @staticmethod
    def create_thumbnail(image_data, size=None):
        """Create thumbnail for faster loading"""
        if size is None:
            size = settings.IMAGE_THUMBNAIL_SIZE
        
        img = Image.open(io.BytesIO(image_data))
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()
    
    @staticmethod
    def optimize_for_web(image_data, max_size=(1920, 1080), quality=85):
        """Optimize image for web display"""
        img = Image.open(io.BytesIO(image_data))
        
        # Resize if too large
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Optimize
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    
    @staticmethod
    def get_image_info(image_data):
        """Get image information without loading full image"""
        img = Image.open(io.BytesIO(image_data))
        return {
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'mode': img.mode,
            'size_bytes': len(image_data)
        }

# Background task for memory cleanup
def memory_cleanup_task():
    """Background task for periodic memory cleanup"""
    optimizer = PerformanceOptimizer()
    
    while True:
        try:
            optimizer.monitor_system_resources()
            time.sleep(settings.MEMORY_CLEANUP_INTERVAL)
        except Exception as e:
            # Log error but continue
            print(f"Memory cleanup error: {e}")
            time.sleep(60)  # Wait 1 minute before retry

# Start background cleanup thread
if settings.PERFORMANCE_OPTIMIZATION_ENABLED:
    cleanup_thread = threading.Thread(target=memory_cleanup_task, daemon=True)
    cleanup_thread.start()
```

### Audit Trail & Compliance (NON-NEGOTIABLE)
```python
# utils/audit_trail.py
import uuid
import json
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from analytics.models import AuditTrail, AuditTrailDetail
from datetime import timedelta

class AuditTrailManager:
    def __init__(self):
        self.retention_days = settings.AUDIT_RETENTION_DAYS
        self.mask_sensitive_data = settings.AUDIT_MASK_SENSITIVE_DATA
    
    def log_action(self, user_id, action_type, action_category, resource_type, 
                   resource_id=None, resource_name=None, action_description=None,
                   before_snapshot=None, after_snapshot=None, request=None,
                   success=True, error_message=None, execution_time_ms=None,
                   data_changed=False, sensitive_data_accessed=False,
                   compliance_flags=None, additional_details=None):
        """Log a comprehensive audit trail entry"""
        
        # Generate correlation ID if not provided
        correlation_id = str(uuid.uuid4())[:8]
        
        # Extract request information
        ip_address = self._get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        request_id = str(uuid.uuid4()) if request else None
        session_id_http = request.session.session_key if request and hasattr(request, 'session') else None
        
        # Mask sensitive data in snapshots
        if self.mask_sensitive_data:
            before_snapshot = self._mask_sensitive_data(before_snapshot)
            after_snapshot = self._mask_sensitive_data(after_snapshot)
        
        # Create audit trail entry
        with transaction.atomic():
            audit_entry = AuditTrail.objects.create(
                user_id=user_id,
                action_type=action_type,
                action_category=action_category,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                action_description=action_description or f"{action_type} on {resource_type}",
                before_snapshot=before_snapshot,
                after_snapshot=after_snapshot,
                ip_address=ip_address,
                user_agent=user_agent,
                correlation_id=correlation_id,
                request_id=request_id,
                session_id_http=session_id_http,
                success=success,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
                data_changed=data_changed,
                sensitive_data_accessed=sensitive_data_accessed,
                compliance_flags=compliance_flags or [],
                retention_status='active',
                retention_expires_at=timezone.now() + timedelta(days=self.retention_days),
                created_at=timezone.now(),
                created_by=str(user_id) if user_id else 'system'
            )
            
            # Add additional details if provided
            if additional_details:
                for detail in additional_details:
                    AuditTrailDetail.objects.create(
                        audit_trail=audit_entry,
                        detail_type=detail.get('type', 'parameter'),
                        detail_key=detail.get('key', ''),
                        detail_value=detail.get('value', ''),
                        is_sensitive=detail.get('is_sensitive', False),
                        masked_value=self._mask_value(detail.get('value', '')) if detail.get('is_sensitive', False) else None
                    )
        
        return audit_entry
    
    def log_user_action(self, user_id, action_type, resource_type, resource_id=None, 
                       resource_name=None, request=None, **kwargs):
        """Log user-initiated actions"""
        return self.log_action(
            user_id=user_id,
            action_type=action_type,
            action_category=self._get_action_category(action_type),
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            request=request,
            **kwargs
        )
    
    def log_system_event(self, action_type, resource_type, resource_id=None,
                        resource_name=None, **kwargs):
        """Log system-initiated events"""
        return self.log_action(
            user_id=None,
            action_type=action_type,
            action_category='system',
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            **kwargs
        )
    
    def log_data_access(self, user_id, resource_type, resource_id, resource_name,
                       sensitive_data_accessed=False, request=None, **kwargs):
        """Log data access events"""
        return self.log_action(
            user_id=user_id,
            action_type='data_access',
            action_category='data_management',
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            sensitive_data_accessed=sensitive_data_accessed,
            request=request,
            **kwargs
        )
    
    def log_security_event(self, user_id, action_type, resource_type, resource_id=None,
                          resource_name=None, request=None, **kwargs):
        """Log security-related events"""
        return self.log_action(
            user_id=user_id,
            action_type=action_type,
            action_category='security',
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            request=request,
            compliance_flags=['gdpr', 'hipaa'],
            **kwargs
        )
    
    def get_audit_trail(self, filters=None, page=1, page_size=50):
        """Retrieve audit trail records with filtering and pagination"""
        queryset = AuditTrail.objects.all()
        
        if filters:
            if filters.get('user_id'):
                queryset = queryset.filter(user_id=filters['user_id'])
            if filters.get('action_type'):
                queryset = queryset.filter(action_type=filters['action_type'])
            if filters.get('action_category'):
                queryset = queryset.filter(action_category=filters['action_category'])
            if filters.get('resource_type'):
                queryset = queryset.filter(resource_type=filters['resource_type'])
            if filters.get('success') is not None:
                queryset = queryset.filter(success=filters['success'])
            if filters.get('sensitive_data_accessed') is not None:
                queryset = queryset.filter(sensitive_data_accessed=filters['sensitive_data_accessed'])
            if filters.get('start_date'):
                queryset = queryset.filter(created_at__gte=filters['start_date'])
            if filters.get('end_date'):
                queryset = queryset.filter(created_at__lte=filters['end_date'])
            if filters.get('correlation_id'):
                queryset = queryset.filter(correlation_id=filters['correlation_id'])
        
        # Order by creation time (newest first)
        queryset = queryset.order_by('-created_at')
        
        # Pagination
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        records = queryset[start:end]
        
        return {
            'records': records,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }
    
    def export_audit_data(self, start_date, end_date, export_format='csv', 
                         filters=None, include_details=False, mask_sensitive_data=True):
        """Export audit trail data for compliance reporting"""
        queryset = AuditTrail.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if filters:
            queryset = self._apply_filters(queryset, filters)
        
        # Generate export file
        export_id = str(uuid.uuid4())
        export_data = self._prepare_export_data(queryset, include_details, mask_sensitive_data)
        
        # Save export file
        file_path = self._save_export_file(export_id, export_data, export_format)
        
        return {
            'export_id': export_id,
            'file_path': file_path,
            'record_count': queryset.count(),
            'export_format': export_format
        }
    
    def generate_compliance_report(self, compliance_standard, start_date, end_date, 
                                  report_type='summary', format='pdf'):
        """Generate compliance reports for various standards"""
        queryset = AuditTrail.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Filter by compliance flags
        if compliance_standard in ['gdpr', 'hipaa', 'sox', 'pci_dss']:
            queryset = queryset.filter(compliance_flags__contains=[compliance_standard])
        
        # Generate report data
        report_data = self._generate_report_data(queryset, compliance_standard, report_type)
        
        # Create report file
        report_id = str(uuid.uuid4())
        file_path = self._create_report_file(report_id, report_data, format)
        
        return {
            'report_id': report_id,
            'report_title': f"{compliance_standard.upper()} Compliance Report",
            'compliance_standard': compliance_standard,
            'report_type': report_type,
            'generated_at': timezone.now(),
            'report_summary': report_data['summary'],
            'file_path': file_path
        }
    
    def cleanup_expired_records(self):
        """Clean up expired audit records"""
        expired_records = AuditTrail.objects.filter(
            retention_expires_at__lt=timezone.now(),
            retention_status='active'
        )
        
        deleted_count = 0
        for record in expired_records:
            # Archive before deletion
            record.retention_status = 'archived'
            record.save()
            
            # Delete associated details
            AuditTrailDetail.objects.filter(audit_trail=record).delete()
            
            # Delete the record
            record.delete()
            deleted_count += 1
        
        return deleted_count
    
    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _mask_sensitive_data(self, data):
        """Mask sensitive data in JSON objects"""
        if not data or not isinstance(data, dict):
            return data
        
        sensitive_fields = ['password', 'token', 'key', 'secret', 'ssn', 'credit_card']
        masked_data = data.copy()
        
        for key, value in masked_data.items():
            if any(sensitive_field in key.lower() for sensitive_field in sensitive_fields):
                masked_data[key] = '***MASKED***'
            elif isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                masked_data[key] = [self._mask_sensitive_data(item) if isinstance(item, dict) else item for item in value]
        
        return masked_data
    
    def _mask_value(self, value):
        """Mask a single value"""
        if not value:
            return value
        
        if len(value) <= 4:
            return '***'
        else:
            return value[:2] + '***' + value[-2:]
    
    def _get_action_category(self, action_type):
        """Map action type to category"""
        category_mapping = {
            'login': 'authentication',
            'logout': 'authentication',
            'upload': 'data_management',
            'analysis': 'analysis',
            'delete': 'data_management',
            'export': 'data_management',
            'admin_action': 'system',
            'system_event': 'system'
        }
        return category_mapping.get(action_type, 'system')
    
    def _apply_filters(self, queryset, filters):
        """Apply filters to queryset"""
        if filters.get('user_ids'):
            queryset = queryset.filter(user_id__in=filters['user_ids'])
        if filters.get('action_types'):
            queryset = queryset.filter(action_type__in=filters['action_types'])
        if filters.get('action_categories'):
            queryset = queryset.filter(action_category__in=filters['action_categories'])
        if filters.get('resource_types'):
            queryset = queryset.filter(resource_type__in=filters['resource_types'])
        if filters.get('success_only'):
            queryset = queryset.filter(success=True)
        if filters.get('sensitive_data_only'):
            queryset = queryset.filter(sensitive_data_accessed=True)
        if filters.get('compliance_flags'):
            queryset = queryset.filter(compliance_flags__overlap=filters['compliance_flags'])
        
        return queryset
    
    def _prepare_export_data(self, queryset, include_details, mask_sensitive_data):
        """Prepare data for export"""
        data = []
        for record in queryset:
            record_data = {
                'id': record.id,
                'user_id': record.user_id,
                'action_type': record.action_type,
                'action_category': record.action_category,
                'resource_type': record.resource_type,
                'resource_id': record.resource_id,
                'resource_name': record.resource_name,
                'action_description': record.action_description,
                'ip_address': record.ip_address,
                'user_agent': record.user_agent,
                'correlation_id': record.correlation_id,
                'success': record.success,
                'error_message': record.error_message,
                'execution_time_ms': record.execution_time_ms,
                'data_changed': record.data_changed,
                'sensitive_data_accessed': record.sensitive_data_accessed,
                'compliance_flags': record.compliance_flags,
                'created_at': record.created_at.isoformat()
            }
            
            if include_details:
                details = AuditTrailDetail.objects.filter(audit_trail=record)
                record_data['details'] = [
                    {
                        'type': detail.detail_type,
                        'key': detail.detail_key,
                        'value': detail.masked_value if mask_sensitive_data and detail.is_sensitive else detail.detail_value,
                        'is_sensitive': detail.is_sensitive
                    }
                    for detail in details
                ]
            
            if mask_sensitive_data:
                record_data['before_snapshot'] = self._mask_sensitive_data(record.before_snapshot)
                record_data['after_snapshot'] = self._mask_sensitive_data(record.after_snapshot)
            else:
                record_data['before_snapshot'] = record.before_snapshot
                record_data['after_snapshot'] = record.after_snapshot
            
            data.append(record_data)
        
        return data
    
    def _save_export_file(self, export_id, data, format):
        """Save export data to file"""
        import os
        import json
        import csv
        import pandas as pd
        
        export_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        if format == 'json':
            file_path = os.path.join(export_dir, f'audit_export_{export_id}.json')
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'csv':
            file_path = os.path.join(export_dir, f'audit_export_{export_id}.csv')
            if data:
                df = pd.json_normalize(data)
                df.to_csv(file_path, index=False)
        elif format == 'xlsx':
            file_path = os.path.join(export_dir, f'audit_export_{export_id}.xlsx')
            if data:
                df = pd.json_normalize(data)
                df.to_excel(file_path, index=False)
        
        return file_path
    
    def _generate_report_data(self, queryset, compliance_standard, report_type):
        """Generate compliance report data"""
        total_events = queryset.count()
        successful_events = queryset.filter(success=True).count()
        failed_events = queryset.filter(success=False).count()
        sensitive_access_events = queryset.filter(sensitive_data_accessed=True).count()
        
        # Calculate compliance score
        compliance_score = (successful_events / total_events * 100) if total_events > 0 else 100
        
        # Identify violations
        violations = queryset.filter(success=False).count()
        
        # Generate recommendations
        recommendations = []
        if failed_events > 0:
            recommendations.append(f"Review {failed_events} failed events for potential security issues")
        if sensitive_access_events > 0:
            recommendations.append(f"Monitor {sensitive_access_events} sensitive data access events")
        if compliance_score < 95:
            recommendations.append("Improve system reliability to meet compliance standards")
        
        return {
            'summary': {
                'total_events': total_events,
                'compliance_score': round(compliance_score, 2),
                'violations_found': violations,
                'recommendations': recommendations
            },
            'detailed_data': list(queryset.values()) if report_type == 'detailed' else None
        }
    
    def _create_report_file(self, report_id, report_data, format):
        """Create compliance report file"""
        import os
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(report_dir, exist_ok=True)
        
        if format == 'pdf':
            file_path = os.path.join(report_dir, f'compliance_report_{report_id}.pdf')
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Add report content
            story.append(Paragraph(f"Compliance Report - {report_data['summary']['total_events']} Events", styles['Title']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Compliance Score: {report_data['summary']['compliance_score']}%", styles['Heading1']))
            story.append(Paragraph(f"Violations Found: {report_data['summary']['violations_found']}", styles['Heading2']))
            
            # Add recommendations
            story.append(Paragraph("Recommendations:", styles['Heading2']))
            for rec in report_data['summary']['recommendations']:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
            
            doc.build(story)
        
        return file_path

# Decorator for automatic audit logging
def audit_action(action_type, resource_type, resource_id_field='id', resource_name_field='name'):
    """Decorator to automatically log actions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract request and resource information
            request = None
            resource_id = None
            resource_name = None
            
            for arg in args:
                if hasattr(arg, 'META'):  # Django request object
                    request = arg
                    break
            
            # Try to extract resource information from kwargs or args
            if resource_id_field in kwargs:
                resource_id = kwargs[resource_id_field]
            if resource_name_field in kwargs:
                resource_name = kwargs[resource_name_field]
            
            # Execute the function
            start_time = timezone.now()
            try:
                result = func(*args, **kwargs)
                success = True
                error_message = None
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                execution_time = (timezone.now() - start_time).total_seconds() * 1000
                
                # Log the action
                audit_manager = AuditTrailManager()
                audit_manager.log_action(
                    user_id=request.user.id if request and hasattr(request, 'user') and request.user.is_authenticated else None,
                    action_type=action_type,
                    action_category=audit_manager._get_action_category(action_type),
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    request=request,
                    success=success,
                    error_message=error_message,
                    execution_time_ms=int(execution_time)
                )
            
            return result
        return wrapper
    return decorator
```

### Agentic AI System (NON-NEGOTIABLE)
```python
# utils/agentic_ai.py
import uuid
import json
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from analytics.models import AgentRun, AgentStep, Dataset, AnalysisTool, AnalysisResult
from .llm_processor import LLMProcessor
from .analysis_executor import AnalysisExecutor
from .performance import PerformanceOptimizer

class AgenticAIController:
    def __init__(self):
        self.llm_processor = LLMProcessor()
        self.analysis_executor = AnalysisExecutor()
        self.performance_optimizer = PerformanceOptimizer()
        self.agent_version = "1.0"
        self.max_retries = 3
    
    def start_agent_run(self, user_id, dataset_id, goal, constraints=None, agent_config=None):
        """Start an autonomous AI agent analysis session"""
        
        # Default constraints
        if constraints is None:
            constraints = {
                'max_steps': 20,
                'max_cost': 10000,
                'max_time': 1800  # 30 minutes
            }
        
        # Default agent config
        if agent_config is None:
            agent_config = {
                'agent_version': self.agent_version,
                'llm_model': 'gemini-pro',
                'planning_mode': 'balanced',
                'auto_retry': True,
                'human_feedback': False
            }
        
        # Create agent run
        with transaction.atomic():
            agent_run = AgentRun.objects.create(
                user_id=user_id,
                dataset_id=dataset_id,
                goal=goal,
                status='planning',
                current_step=0,
                total_steps=0,
                max_steps=constraints['max_steps'],
                max_cost=constraints['max_cost'],
                max_time=constraints['max_time'],
                total_cost=0,
                total_time=0,
                progress_percentage=0,
                agent_version=agent_config['agent_version'],
                llm_model=agent_config['llm_model'],
                started_at=timezone.now(),
                correlation_id=str(uuid.uuid4())[:8]
            )
        
        # Start planning phase
        self._plan_analysis(agent_run, agent_config)
        
        # Start execution phase
        self._execute_agent_run(agent_run, agent_config)
        
        return agent_run
    
    def _plan_analysis(self, agent_run, agent_config):
        """Plan the analysis strategy using LLM"""
        
        # Get dataset information
        dataset = Dataset.objects.get(id=agent_run.dataset_id)
        
        # Create planning prompt
        planning_prompt = f"""
        You are an autonomous data analysis agent. Your goal is to analyze the following dataset to answer: "{agent_run.goal}"
        
        Dataset Information:
        - Name: {dataset.name}
        - Columns: {dataset.column_types}
        - Rows: {dataset.row_count}
        - File type: {dataset.file_type}
        
        Constraints:
        - Maximum steps: {agent_run.max_steps}
        - Maximum cost: {agent_run.max_cost} tokens
        - Maximum time: {agent_run.max_time} seconds
        
        Available Analysis Tools:
        - descriptive_stats: Basic statistical analysis
        - correlation_analysis: Correlation matrix and analysis
        - regression_analysis: Linear and multiple regression
        - clustering_analysis: K-means and hierarchical clustering
        - time_series_analysis: Time series decomposition and forecasting
        - survival_analysis: Survival curves and hazard ratios
        - hypothesis_testing: Statistical hypothesis tests
        - data_visualization: Charts and plots
        
        Create a detailed analysis plan with the following structure:
        {{
            "strategy": "Brief description of overall strategy",
            "steps": [
                {{
                    "step_number": 1,
                    "tool_name": "descriptive_stats",
                    "parameters": {{"columns": ["column1", "column2"]}},
                    "reasoning": "Why this step is needed",
                    "expected_outcome": "What we expect to learn"
                }},
                ...
            ],
            "success_criteria": "How we'll know if the analysis is successful",
            "risk_mitigation": "How we'll handle potential issues"
        }}
        
        Plan mode: {agent_config['planning_mode']}
        """
        
        # Get LLM response
        response = self.llm_processor.generate_response(
            session_id=None,
            user_message=planning_prompt,
            context_data={'agent_run_id': agent_run.id},
            user_id=agent_run.user_id
        )
        
        # Parse and validate plan
        try:
            plan = json.loads(response['response'])
            agent_run.plan_json = plan
            agent_run.total_steps = len(plan['steps'])
            agent_run.status = 'running'
            agent_run.save()
            
            # Log planning step
            AgentStep.objects.create(
                agent_run=agent_run,
                step_number=0,
                thought="Planning analysis strategy based on user goal and dataset characteristics",
                tool_name="planning",
                parameters_json={"goal": agent_run.goal, "constraints": agent_run.max_steps},
                observation_json={"plan": plan},
                status='completed',
                token_usage=response['tokens_used'],
                execution_time_ms=response['processing_time'],
                confidence_score=0.9,
                reasoning="Created comprehensive analysis plan using LLM",
                next_action="Begin executing analysis steps",
                started_at=timezone.now(),
                finished_at=timezone.now()
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            agent_run.status = 'failed'
            agent_run.error_message = f"Planning failed: {str(e)}"
            agent_run.finished_at = timezone.now()
            agent_run.save()
            raise
    
    def _execute_agent_run(self, agent_run, agent_config):
        """Execute the agent run step by step"""
        
        plan = agent_run.plan_json
        steps = plan['steps']
        
        for step_data in steps:
            # Check constraints
            if not self._check_constraints(agent_run):
                break
            
            # Execute step
            self._execute_step(agent_run, step_data, agent_config)
            
            # Update progress
            agent_run.current_step += 1
            agent_run.progress_percentage = (agent_run.current_step / agent_run.total_steps) * 100
            agent_run.save()
        
        # Complete the run
        if agent_run.status == 'running':
            agent_run.status = 'completed'
            agent_run.finished_at = timezone.now()
            agent_run.save()
    
    def _execute_step(self, agent_run, step_data, agent_config):
        """Execute a single agent step"""
        
        step_number = step_data['step_number']
        tool_name = step_data['tool_name']
        parameters = step_data['parameters']
        reasoning = step_data['reasoning']
        
        # Create step record
        step = AgentStep.objects.create(
            agent_run=agent_run,
            step_number=step_number,
            thought=reasoning,
            tool_name=tool_name,
            parameters_json=parameters,
            status='running',
            started_at=timezone.now()
        )
        
        try:
            # Execute the tool
            with self.performance_optimizer.memory_monitor(f'agent_step_{step_number}'):
                result = self.analysis_executor.execute_tool(
                    tool_name=tool_name,
                    session_id=agent_run.session_id,
                    parameters=parameters,
                    user_id=agent_run.user_id
                )
            
            # Update step with results
            step.observation_json = result['data']
            step.status = 'completed'
            step.execution_time_ms = result['execution_time']
            step.memory_used_mb = result['memory_used']
            step.confidence_score = self._calculate_confidence_score(result)
            step.finished_at = timezone.now()
            step.save()
            
            # Update agent run
            agent_run.total_cost += result.get('tokens_used', 0)
            agent_run.total_time += result['execution_time']
            agent_run.save()
            
            # Analyze results and plan next action
            next_action = self._analyze_step_results(agent_run, step, result)
            step.next_action = next_action
            step.save()
            
        except Exception as e:
            # Handle step failure
            step.status = 'failed'
            step.error_message = str(e)
            step.finished_at = timezone.now()
            step.save()
            
            # Retry if enabled
            if agent_config['auto_retry'] and step.retry_count < self.max_retries:
                step.retry_count += 1
                step.status = 'running'
                step.started_at = timezone.now()
                step.save()
                
                # Retry the step
                self._execute_step(agent_run, step_data, agent_config)
            else:
                # Mark agent run as failed
                agent_run.status = 'failed'
                agent_run.error_message = f"Step {step_number} failed: {str(e)}"
                agent_run.finished_at = timezone.now()
                agent_run.save()
                break
    
    def _check_constraints(self, agent_run):
        """Check if agent run is within constraints"""
        
        # Check time constraint
        if agent_run.total_time >= agent_run.max_time:
            agent_run.status = 'failed'
            agent_run.error_message = "Maximum time limit exceeded"
            agent_run.finished_at = timezone.now()
            agent_run.save()
            return False
        
        # Check cost constraint
        if agent_run.total_cost >= agent_run.max_cost:
            agent_run.status = 'failed'
            agent_run.error_message = "Maximum cost limit exceeded"
            agent_run.finished_at = timezone.now()
            agent_run.save()
            return False
        
        # Check step constraint
        if agent_run.current_step >= agent_run.max_steps:
            agent_run.status = 'completed'
            agent_run.finished_at = timezone.now()
            agent_run.save()
            return False
        
        return True
    
    def _calculate_confidence_score(self, result):
        """Calculate confidence score based on result quality"""
        
        # Simple confidence calculation based on result completeness
        if result.get('data') and len(result['data']) > 0:
            return 0.8
        elif result.get('error'):
            return 0.2
        else:
            return 0.5
    
    def _analyze_step_results(self, agent_run, step, result):
        """Analyze step results and suggest next action"""
        
        # Create analysis prompt
        analysis_prompt = f"""
        Analyze the results of this analysis step and suggest the next action.
        
        Step: {step.tool_name}
        Parameters: {step.parameters_json}
        Results: {result['data']}
        Goal: {agent_run.goal}
        
        Provide a brief suggestion for the next action based on these results.
        """
        
        try:
            response = self.llm_processor.generate_response(
                session_id=None,
                user_message=analysis_prompt,
                context_data={'agent_run_id': agent_run.id},
                user_id=agent_run.user_id
            )
            
            return response['response']
        except Exception:
            return "Continue with next planned step"
    
    def pause_agent_run(self, agent_run_id):
        """Pause an active agent run"""
        
        agent_run = AgentRun.objects.get(id=agent_run_id)
        
        if agent_run.status == 'running':
            agent_run.status = 'paused'
            agent_run.save()
            return True
        else:
            return False
    
    def resume_agent_run(self, agent_run_id):
        """Resume a paused agent run"""
        
        agent_run = AgentRun.objects.get(id=agent_run_id)
        
        if agent_run.status == 'paused':
            agent_run.status = 'running'
            agent_run.save()
            
            # Continue execution
            agent_config = {
                'agent_version': agent_run.agent_version,
                'llm_model': agent_run.llm_model,
                'planning_mode': 'balanced',
                'auto_retry': True,
                'human_feedback': False
            }
            
            self._execute_agent_run(agent_run, agent_config)
            return True
        else:
            return False
    
    def cancel_agent_run(self, agent_run_id):
        """Cancel an active or paused agent run"""
        
        agent_run = AgentRun.objects.get(id=agent_run_id)
        
        if agent_run.status in ['running', 'paused']:
            agent_run.status = 'cancelled'
            agent_run.finished_at = timezone.now()
            agent_run.save()
            return True
        else:
            return False
    
    def provide_feedback(self, agent_run_id, feedback_type, message, step_id=None, suggested_action=None):
        """Provide human feedback to guide agent behavior"""
        
        agent_run = AgentRun.objects.get(id=agent_run_id)
        
        # Create feedback prompt
        feedback_prompt = f"""
        Human feedback received:
        Type: {feedback_type}
        Message: {message}
        Step ID: {step_id}
        Suggested Action: {suggested_action}
        
        Current goal: {agent_run.goal}
        Current step: {agent_run.current_step}
        
        How should the agent adapt its behavior based on this feedback?
        """
        
        try:
            response = self.llm_processor.generate_response(
                session_id=None,
                user_message=feedback_prompt,
                context_data={'agent_run_id': agent_run_id},
                user_id=agent_run.user_id
            )
            
            # Update agent run with feedback
            if 'feedback_history' not in agent_run.plan_json:
                agent_run.plan_json['feedback_history'] = []
            
            agent_run.plan_json['feedback_history'].append({
                'type': feedback_type,
                'message': message,
                'step_id': step_id,
                'suggested_action': suggested_action,
                'timestamp': timezone.now().isoformat(),
                'agent_response': response['response']
            })
            
            agent_run.save()
            
            return {
                'success': True,
                'agent_response': response['response'],
                'updated_plan': agent_run.plan_json
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_agent_run_status(self, agent_run_id, include_steps=True):
        """Get current status and progress of an agent run"""
        
        agent_run = AgentRun.objects.get(id=agent_run_id)
        
        result = {
            'agent_run': agent_run,
            'current_plan': agent_run.plan_json,
            'next_action': self._get_next_action(agent_run),
            'estimated_remaining_time': self._estimate_remaining_time(agent_run)
        }
        
        if include_steps:
            steps = AgentStep.objects.filter(agent_run=agent_run).order_by('step_number')
            result['steps'] = steps
        
        return result
    
    def _get_next_action(self, agent_run):
        """Get the next planned action"""
        
        if agent_run.status == 'completed':
            return "Analysis completed successfully"
        elif agent_run.status == 'failed':
            return f"Analysis failed: {agent_run.error_message}"
        elif agent_run.status == 'cancelled':
            return "Analysis was cancelled"
        else:
            plan = agent_run.plan_json
            if plan and 'steps' in plan:
                current_step = agent_run.current_step
                if current_step < len(plan['steps']):
                    next_step = plan['steps'][current_step]
                    return f"Next: {next_step['tool_name']} - {next_step['reasoning']}"
                else:
                    return "Analysis completed"
            else:
                return "Planning analysis strategy"
    
    def _estimate_remaining_time(self, agent_run):
        """Estimate remaining time for agent run"""
        
        if agent_run.status in ['completed', 'failed', 'cancelled']:
            return 0
        
        if agent_run.current_step == 0:
            return agent_run.max_time
        
        # Estimate based on average step time
        if agent_run.current_step > 0:
            avg_step_time = agent_run.total_time / agent_run.current_step
            remaining_steps = agent_run.total_steps - agent_run.current_step
            return remaining_steps * avg_step_time
        
        return agent_run.max_time - agent_run.total_time

# Celery task for agent execution
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def execute_agent_run_task(self, agent_run_id, agent_config):
    """Execute agent run asynchronously"""
    try:
        controller = AgenticAIController()
        agent_run = AgentRun.objects.get(id=agent_run_id)
        
        # Execute the agent run
        controller._execute_agent_run(agent_run, agent_config)
        
        return {
            'success': True,
            'agent_run_id': agent_run_id,
            'status': agent_run.status,
            'total_steps': agent_run.total_steps,
            'total_cost': agent_run.total_cost,
            'total_time': agent_run.total_time
        }
    
    except Exception as exc:
        # Update agent run status
        agent_run = AgentRun.objects.get(id=agent_run_id)
        agent_run.status = 'failed'
        agent_run.error_message = str(exc)
        agent_run.finished_at = timezone.now()
        agent_run.save()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'success': False,
            'agent_run_id': agent_run_id,
            'error': str(exc)
        }
```

### Agentic AI Runtime Wiring (NON-NEGOTIABLE)
```python
# views/agent_views.py - Agentic AI API Endpoints
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from analytics.models import AgentRun, AgentStep, Dataset
from analytics.tasks import execute_agent_run_task
from utils.agentic_ai import AgenticAIController
import uuid

class AgentRunViewSet(viewsets.ModelViewSet):
    """Agentic AI runtime endpoints for autonomous analysis"""
    
    def create(self, request):
        """Start autonomous AI agent analysis"""
        dataset_id = request.data.get('dataset_id')
        goal = request.data.get('goal')
        constraints = request.data.get('constraints', {})
        agent_config = request.data.get('agent_config', {})
        
        # Validate dataset exists and user has access
        dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
        
        # Create agent run
        controller = AgenticAIController()
        agent_run = controller.start_agent_run(
            user_id=request.user.id,
            dataset_id=dataset_id,
            goal=goal,
            constraints=constraints,
            agent_config=agent_config
        )
        
        # Start Celery task for execution
        task = execute_agent_run_task.delay(agent_run.id, agent_config)
        
        return Response({
            'agent_run_id': agent_run.id,
            'status': agent_run.status,
            'correlation_id': agent_run.correlation_id,
            'estimated_completion_time': agent_run.max_time,
            'progress_url': f'/api/agent/run/{agent_run.id}/',
            'celery_task_id': task.id
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get real-time agent run status and progress"""
        agent_run = get_object_or_404(AgentRun, id=pk, user=request.user)
        include_steps = request.query_params.get('include_steps', 'true').lower() == 'true'
        
        controller = AgenticAIController()
        status_data = controller.get_agent_run_status(agent_run.id, include_steps)
        
        return Response({
            'agent_run': {
                'id': agent_run.id,
                'status': agent_run.status,
                'progress_percentage': agent_run.progress_percentage,
                'current_step': agent_run.current_step,
                'total_steps': agent_run.total_steps,
                'total_cost': agent_run.total_cost,
                'total_time': agent_run.total_time,
                'goal': agent_run.goal,
                'started_at': agent_run.started_at,
                'finished_at': agent_run.finished_at,
                'error_message': agent_run.error_message
            },
            'current_plan': status_data['current_plan'],
            'next_action': status_data['next_action'],
            'estimated_remaining_time': status_data['estimated_remaining_time'],
            'steps': [
                {
                    'step_number': step.step_number,
                    'thought': step.thought,
                    'tool_name': step.tool_name,
                    'status': step.status,
                    'confidence_score': step.confidence_score,
                    'reasoning': step.reasoning,
                    'next_action': step.next_action,
                    'execution_time_ms': step.execution_time_ms,
                    'token_usage': step.token_usage,
                    'error_message': step.error_message
                }
                for step in status_data.get('steps', [])
            ] if include_steps else []
        })
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause an active agent run"""
        agent_run = get_object_or_404(AgentRun, id=pk, user=request.user)
        
        controller = AgenticAIController()
        success = controller.pause_agent_run(agent_run.id)
        
        if success:
            return Response({
                'success': True,
                'status': 'paused',
                'paused_at': agent_run.updated_at
            })
        else:
            return Response({
                'success': False,
                'error': 'Agent run cannot be paused in current state'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused agent run"""
        agent_run = get_object_or_404(AgentRun, id=pk, user=request.user)
        
        controller = AgenticAIController()
        success = controller.resume_agent_run(agent_run.id)
        
        if success:
            return Response({
                'success': True,
                'status': 'running',
                'resumed_at': agent_run.updated_at
            })
        else:
            return Response({
                'success': False,
                'error': 'Agent run cannot be resumed in current state'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an active or paused agent run"""
        agent_run = get_object_or_404(AgentRun, id=pk, user=request.user)
        
        controller = AgenticAIController()
        success = controller.cancel_agent_run(agent_run.id)
        
        if success:
            return Response({
                'success': True,
                'status': 'cancelled',
                'cancelled_at': agent_run.finished_at
            })
        else:
            return Response({
                'success': False,
                'error': 'Agent run cannot be cancelled in current state'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """Provide human feedback to guide agent behavior"""
        agent_run = get_object_or_404(AgentRun, id=pk, user=request.user)
        
        feedback_type = request.data.get('feedback_type')
        message = request.data.get('message')
        step_id = request.data.get('step_id')
        suggested_action = request.data.get('suggested_action')
        
        controller = AgenticAIController()
        result = controller.provide_feedback(
            agent_run_id=agent_run.id,
            feedback_type=feedback_type,
            message=message,
            step_id=step_id,
            suggested_action=suggested_action
        )
        
        if result['success']:
            return Response({
                'success': True,
                'feedback_id': uuid.uuid4(),
                'agent_response': result['agent_response'],
                'updated_plan': result['updated_plan']
            })
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)

# templates/analysis_dashboard.html - HTMX Integration
"""
<!-- Analyze Button Integration -->
<div class="card mb-4">
    <div class="card-header">
        <h5 class="card-title">Autonomous Analysis</h5>
    </div>
    <div class="card-body">
        <form hx-post="/api/agent/run/" 
              hx-target="#agent-results" 
              hx-indicator="#loading-spinner"
              hx-vals='{"dataset_id": "{{dataset.id}}"}'>
            <div class="mb-3">
                <label for="analysis-goal" class="form-label">Analysis Goal</label>
                <textarea class="form-control" 
                          id="analysis-goal" 
                          name="goal" 
                          rows="3" 
                          placeholder="Describe what you want to analyze..."></textarea>
            </div>
            <div class="mb-3">
                <label for="max-steps" class="form-label">Max Steps</label>
                <input type="number" 
                       class="form-control" 
                       id="max-steps" 
                       name="constraints.max_steps" 
                       value="20" 
                       min="1" 
                       max="100">
            </div>
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-robot"></i> Analyze with AI Agent
            </button>
        </form>
    </div>
</div>

<!-- Agent Results Display -->
<div id="agent-results" class="mt-4">
    <!-- Results will be populated here -->
</div>

<!-- Real-time Progress Updates -->
<div id="agent-progress" class="card mt-4" style="display: none;">
    <div class="card-header">
        <h6 class="card-title">Agent Progress</h6>
    </div>
    <div class="card-body">
        <div class="progress mb-3">
            <div class="progress-bar" 
                 role="progressbar" 
                 style="width: 0%" 
                 aria-valuenow="0" 
                 aria-valuemin="0" 
                 aria-valuemax="100">
                <span id="progress-text">0%</span>
            </div>
        </div>
        <div id="current-step" class="mb-2"></div>
        <div id="next-action" class="mb-2"></div>
        <div class="btn-group">
            <button class="btn btn-sm btn-warning" 
                    hx-post="/api/agent/run/{agent_run_id}/pause/" 
                    hx-target="#agent-progress">
                Pause
            </button>
            <button class="btn btn-sm btn-danger" 
                    hx-post="/api/agent/run/{agent_run_id}/cancel/" 
                    hx-target="#agent-progress">
                Cancel
            </button>
        </div>
    </div>
</div>

<!-- HTMX Script for Real-time Updates -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Poll for agent status updates
    function pollAgentStatus(agentRunId) {
        fetch(`/api/agent/run/${agentRunId}/status/`)
            .then(response => response.json())
            .then(data => {
                updateProgress(data);
                if (data.agent_run.status === 'running') {
                    setTimeout(() => pollAgentStatus(agentRunId), 2000);
                }
            });
    }
    
    function updateProgress(data) {
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.getElementById('progress-text');
        const currentStep = document.getElementById('current-step');
        const nextAction = document.getElementById('next-action');
        
        progressBar.style.width = data.agent_run.progress_percentage + '%';
        progressText.textContent = data.agent_run.progress_percentage + '%';
        currentStep.textContent = `Step ${data.agent_run.current_step} of ${data.agent_run.total_steps}`;
        nextAction.textContent = data.next_action;
        
        if (data.agent_run.status === 'completed') {
            progressText.textContent = 'Completed!';
            // Show results
            showResults(data);
        }
    }
    
    function showResults(data) {
        // Display analysis results
        const resultsDiv = document.getElementById('agent-results');
        resultsDiv.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5>Analysis Complete</h5>
                </div>
                <div class="card-body">
                    <p><strong>Goal:</strong> ${data.agent_run.goal}</p>
                    <p><strong>Steps Completed:</strong> ${data.agent_run.total_steps}</p>
                    <p><strong>Total Cost:</strong> ${data.agent_run.total_cost} tokens</p>
                    <p><strong>Total Time:</strong> ${data.agent_run.total_time} seconds</p>
                    <div class="mt-3">
                        <button class="btn btn-primary" 
                                hx-get="/api/analysis/results/${data.agent_run.id}/" 
                                hx-target="#analysis-results">
                            View Results
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
});
</script>
"""

# urls.py - URL Configuration
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from analytics.views.agent_views import AgentRunViewSet

router = DefaultRouter()
router.register(r'agent/run', AgentRunViewSet, basename='agentrun')

urlpatterns = [
    path('api/', include(router.urls)),
    # ... other URLs
]
```

### Celery Background Task Processing (NON-NEGOTIABLE)
```python
# settings.py - Celery Configuration
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytics.settings')

# Celery Configuration (NON-NEGOTIABLE)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_DEFAULT_QUEUE = 'analytical'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Task Configuration
CELERY_TASK_ALWAYS_EAGER = False  # Use Celery workers in production
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_IGNORE_RESULT = False
CELERY_TASK_STORE_EAGER_RESULT = True

# Task Routing and Prioritization
CELERY_TASK_ROUTES = {
    'analytics.tasks.file_processing.*': {'queue': 'file_processing'},
    'analytics.tasks.analysis.*': {'queue': 'analysis'},
    'analytics.tasks.llm.*': {'queue': 'llm_processing'},
    'analytics.tasks.sandbox.*': {'queue': 'sandbox'},
    'analytics.tasks.reports.*': {'queue': 'reports'},
    'analytics.tasks.images.*': {'queue': 'image_processing'},
    'analytics.tasks.backup.*': {'queue': 'backup'},
    'analytics.tasks.monitoring.*': {'queue': 'monitoring'},
}

# Task Priority Configuration
CELERY_TASK_DEFAULT_PRIORITY = 5
CELERY_TASK_PRIORITY_STEPS = list(range(10))
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True

# Retry Configuration
CELERY_TASK_RETRY_DELAY = 60  # seconds
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_RETRY_BACKOFF = True
CELERY_TASK_RETRY_BACKOFF_MAX = 600  # seconds
CELERY_TASK_RETRY_JITTER = True

# Worker Configuration
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_DISABLE_RATE_LIMITS = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Monitoring Configuration
CELERY_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# Security Configuration
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Create Celery app
app = Celery('analytics')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic Tasks Configuration
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'backup-daily': {
        'task': 'analytics.tasks.backup.daily_backup',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'cleanup-sessions': {
        'task': 'analytics.tasks.monitoring.cleanup_expired_sessions',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'cleanup-temp-files': {
        'task': 'analytics.tasks.monitoring.cleanup_temp_files',
        'schedule': crontab(minute=30, hour='*/2'),  # Every 2 hours
    },
    'monitor-system-health': {
        'task': 'analytics.tasks.monitoring.system_health_check',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-old-reports': {
        'task': 'analytics.tasks.reports.cleanup_old_reports',
        'schedule': crontab(hour=1, minute=0),  # 1 AM daily
    },
    'cleanup-old-images': {
        'task': 'analytics.tasks.images.cleanup_old_images',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    },
}

# Task Time Limits
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes
CELERY_WORKER_TASK_TIME_LIMIT = 300
CELERY_WORKER_TASK_SOFT_TIME_LIMIT = 240

# Memory Limits
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 200000  # 200MB
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'

# Error Handling
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_IGNORE_RESULT = False
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Flower Configuration (Task Monitoring)
FLOWER_BASIC_AUTH = ['admin:password']  # Change in production
FLOWER_PORT = 5555
FLOWER_ADDRESS = '0.0.0.0'
FLOWER_URL_PREFIX = 'flower'
```

```python
# analytics/tasks/__init__.py
from celery import Celery

app = Celery('analytics')

# Import all task modules
from . import file_processing
from . import analysis
from . import llm
from . import sandbox
from . import reports
from . import images
from . import backup
from . import monitoring

__all__ = ['app']
```

```python
# analytics/tasks/file_processing.py
from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os
import tempfile
from .utils.file_processor import FileProcessor
from .utils.security import SecurityValidator
from .utils.performance import PerformanceOptimizer

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_uploaded_file(self, file_id, user_id, session_id):
    """Process uploaded file asynchronously"""
    try:
        with PerformanceOptimizer().memory_monitor('file_processing'):
            # Get file from storage
            file_path = default_storage.path(f'uploads/{file_id}')
            
            # Security validation
            validator = SecurityValidator()
            if not validator.validate_file(file_path):
                raise ValueError("File failed security validation")
            
            # Process file
            processor = FileProcessor()
            result = processor.process_file(file_path, user_id, session_id)
            
            # Update database
            from analytics.models import UploadedFile
            file_obj = UploadedFile.objects.get(id=file_id)
            file_obj.processing_status = 'completed'
            file_obj.parquet_path = result['parquet_path']
            file_obj.column_types = result['column_types']
            file_obj.file_size = result['file_size']
            file_obj.save()
            
            return {
                'success': True,
                'file_id': file_id,
                'parquet_path': result['parquet_path'],
                'column_types': result['column_types'],
                'rows_processed': result['rows_processed']
            }
    
    except Exception as exc:
        # Update status to failed
        from analytics.models import UploadedFile
        file_obj = UploadedFile.objects.get(id=file_id)
        file_obj.processing_status = 'failed'
        file_obj.error_message = str(exc)
        file_obj.save()
        
        # Retry if not max retries reached
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'success': False,
            'file_id': file_id,
            'error': str(exc)
        }

@shared_task(bind=True, max_retries=2)
def convert_to_parquet(self, file_path, output_path, file_type):
    """Convert file to Parquet format"""
    try:
        with PerformanceOptimizer().memory_monitor('parquet_conversion'):
            if file_type == 'csv':
                df = pd.read_csv(file_path)
            elif file_type == 'xlsx':
                df = pd.read_excel(file_path)
            elif file_type == 'json':
                df = pd.read_json(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Optimize DataFrame
            optimizer = PerformanceOptimizer()
            df_optimized, reduction = optimizer.optimize_dataframe(df)
            
            # Save as Parquet
            df_optimized.to_parquet(output_path, engine='pyarrow', compression='snappy')
            
            return {
                'success': True,
                'output_path': output_path,
                'rows': len(df_optimized),
                'columns': len(df_optimized.columns),
                'memory_reduction': reduction
            }
    
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'success': False,
            'error': str(exc)
        }
```

```python
# analytics/tasks/analysis.py
from celery import shared_task
from django.conf import settings
from .utils.analysis_executor import AnalysisExecutor
from .utils.performance import PerformanceOptimizer

@shared_task(bind=True, max_retries=2)
def execute_analysis_tool(self, tool_id, session_id, parameters, user_id):
    """Execute analysis tool asynchronously"""
    try:
        with PerformanceOptimizer().memory_monitor('analysis_execution'):
            executor = AnalysisExecutor()
            result = executor.execute_tool(tool_id, session_id, parameters, user_id)
            
            # Update analysis result in database
            from analytics.models import AnalysisResult
            analysis_result = AnalysisResult.objects.create(
                session_id=session_id,
                tool_id=tool_id,
                parameters=parameters,
                result_data=result['data'],
                execution_time_ms=result['execution_time'],
                memory_used_mb=result['memory_used'],
                status='completed'
            )
            
            return {
                'success': True,
                'analysis_id': analysis_result.id,
                'result': result
            }
    
    except Exception as exc:
        # Update status to failed
        from analytics.models import AnalysisResult
        AnalysisResult.objects.create(
            session_id=session_id,
            tool_id=tool_id,
            parameters=parameters,
            status='failed',
            error_message=str(exc)
        )
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'success': False,
            'error': str(exc)
        }

@shared_task(bind=True, max_retries=1)
def batch_analysis_execution(self, tool_ids, session_id, parameters_list, user_id):
    """Execute multiple analysis tools in batch"""
    try:
        results = []
        for tool_id, parameters in zip(tool_ids, parameters_list):
            result = execute_analysis_tool.delay(tool_id, session_id, parameters, user_id)
            results.append(result.get())
        
        return {
            'success': True,
            'results': results,
            'total_tools': len(tool_ids)
        }
    
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc)
        }
```

```python
# analytics/tasks/llm.py
from celery import shared_task
from django.conf import settings
from .utils.llm_processor import LLMProcessor
from .utils.performance import PerformanceOptimizer

@shared_task(bind=True, max_retries=2)
def process_llm_batch(self, session_id, analysis_results, prompt_template, user_id):
    """Process multiple analysis results with LLM in batch"""
    try:
        with PerformanceOptimizer().memory_monitor('llm_batch_processing'):
            processor = LLMProcessor()
            result = processor.process_batch(session_id, analysis_results, prompt_template, user_id)
            
            return {
                'success': True,
                'session_id': session_id,
                'interpretations': result['interpretations'],
                'tokens_used': result['tokens_used'],
                'processing_time': result['processing_time']
            }
    
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'success': False,
            'error': str(exc)
        }

@shared_task(bind=True, max_retries=1)
def generate_llm_response(self, session_id, user_message, context_data, user_id):
    """Generate LLM response with context"""
    try:
        with PerformanceOptimizer().memory_monitor('llm_response_generation'):
            processor = LLMProcessor()
            result = processor.generate_response(session_id, user_message, context_data, user_id)
            
            return {
                'success': True,
                'response': result['response'],
                'tokens_used': result['tokens_used'],
                'context_updated': result['context_updated']
            }
    
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc)
        }
```

```python
# analytics/tasks/sandbox.py
from celery import shared_task
from django.conf import settings
from .utils.sandbox_executor import SandboxExecutor
from .utils.performance import PerformanceOptimizer

@shared_task(bind=True, max_retries=1, time_limit=60)
def execute_sandbox_code(self, session_id, user_id, user_query, context_data):
    """Execute user query in secure sandbox"""
    try:
        with PerformanceOptimizer().memory_monitor('sandbox_execution'):
            executor = SandboxExecutor()
            result = executor.execute_user_query(session_id, user_id, user_query, context_data)
            
            return {
                'success': True,
                'execution_id': result['execution_id'],
                'output_data': result['output_data'],
                'images_generated': result['images_generated'],
                'tables_generated': result['tables_generated'],
                'execution_time': result['execution_time']
            }
    
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc)
        }
```

```python
# analytics/tasks/reports.py
from celery import shared_task
from django.conf import settings
from .utils.report_generator import ReportGenerator
from .utils.performance import PerformanceOptimizer

@shared_task(bind=True, max_retries=2)
def generate_report(self, report_id, session_id, user_id, report_title, report_type, content_selection, template_id, generation_settings):
    """Generate professional report asynchronously"""
    try:
        with PerformanceOptimizer().memory_monitor('report_generation'):
            generator = ReportGenerator()
            result = generator.generate_report_async(
                report_id, session_id, user_id, report_title, 
                report_type, content_selection, template_id, generation_settings
            )
            
            return {
                'success': True,
                'report_id': report_id,
                'file_path': result['file_path'],
                'file_size': result['file_size'],
                'generation_time': result['generation_time']
            }
    
    except Exception as exc:
        # Update report status to failed
        from analytics.models import ReportGeneration
        report = ReportGeneration.objects.get(id=report_id)
        report.report_status = 'failed'
        report.error_message = str(exc)
        report.save()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'success': False,
            'error': str(exc)
        }

@shared_task(bind=True, max_retries=1)
def cleanup_old_reports(self):
    """Clean up old reports to free storage"""
    try:
        from analytics.models import ReportGeneration
        from django.utils import timezone
        from datetime import timedelta
        
        # Delete reports older than retention period
        cutoff_date = timezone.now() - timedelta(days=settings.REPORT_RETENTION_DAYS)
        old_reports = ReportGeneration.objects.filter(
            created_at__lt=cutoff_date,
            report_status='completed'
        )
        
        deleted_count = 0
        for report in old_reports:
            if report.file_path and os.path.exists(report.file_path):
                os.remove(report.file_path)
            report.delete()
            deleted_count += 1
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
    
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc)
        }
```

```python
# analytics/tasks/images.py
from celery import shared_task
from django.conf import settings
from .utils.image_manager import ImageManager
from .utils.performance import PerformanceOptimizer

@shared_task(bind=True, max_retries=2)
def process_generated_image(self, session_id, analysis_result_id, tool_id, image_data, image_type, filename):
    """Process and optimize generated image"""
    try:
        with PerformanceOptimizer().memory_monitor('image_processing'):
            manager = ImageManager()
            result = manager.save_generated_image(
                session_id, analysis_result_id, tool_id, 
                image_data, image_type, filename
            )
            
            return {
                'success': True,
                'image_id': result['image_id'],
                'file_path': result['file_path'],
                'access_url': result['access_url'],
                'file_size': result['file_size']
            }
    
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'success': False,
            'error': str(exc)
        }

@shared_task(bind=True, max_retries=1)
def cleanup_old_images(self):
    """Clean up old images to free storage"""
    try:
        from analytics.models import GeneratedImage
        from django.utils import timezone
        from datetime import timedelta
        
        # Delete images older than retention period
        cutoff_date = timezone.now() - timedelta(days=settings.IMAGE_RETENTION_DAYS)
        old_images = GeneratedImage.objects.filter(created_at__lt=cutoff_date)
        
        deleted_count = 0
        for image in old_images:
            if image.file_path and os.path.exists(image.file_path):
                os.remove(image.file_path)
            image.delete()
            deleted_count += 1
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
    
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc)
        }
```

```python
# analytics/tasks/backup.py
from celery import shared_task
from django.conf import settings
from .utils.backup_manager import BackupManager

@shared_task(bind=True, max_retries=3)
def daily_backup(self):
    """Perform daily automated backup"""
    try:
        manager = BackupManager()
        result = manager.create_backup('daily')
        
        return {
            'success': True,
            'backup_id': result['backup_id'],
            'backup_path': result['backup_path'],
            'backup_size': result['backup_size']
        }
    
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            'success': False,
            'error': str(exc)
        }

@shared_task(bind=True, max_retries=2)
def verify_backup_integrity(self, backup_id):
    """Verify backup integrity"""
    try:
        manager = BackupManager()
        result = manager.verify_backup(backup_id)
        
        return {
            'success': True,
            'backup_id': backup_id,
            'integrity_check': result['integrity_check'],
            'verification_time': result['verification_time']
        }
    
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc)
        }
```

```python
# analytics/tasks/monitoring.py
from celery import shared_task
from django.conf import settings
from .utils.performance import PerformanceOptimizer

@shared_task(bind=True, max_retries=1)
def system_health_check(self):
    """Perform system health check"""
    try:
        optimizer = PerformanceOptimizer()
        optimizer.monitor_system_resources()
        
        # Check database connectivity
        from django.db import connection
        connection.ensure_connection()
        
        # Check Redis connectivity
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        
        return {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'status': 'healthy'
        }
    
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc),
            'status': 'unhealthy'
        }

@shared_task(bind=True, max_retries=1)
def cleanup_expired_sessions(self):
    """Clean up expired sessions"""
    try:
        from analytics.models import AnalysisSession
        from django.utils import timezone
        from datetime import timedelta
        
        # Clean up sessions older than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        expired_sessions = AnalysisSession.objects.filter(
            last_activity__lt=cutoff_date
        )
        
        deleted_count = 0
        for session in expired_sessions:
            # Clean up session data
            optimizer = PerformanceOptimizer()
            optimizer.cleanup_session_data(session.id)
            session.delete()
            deleted_count += 1
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
    
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc)
        }

@shared_task(bind=True, max_retries=1)
def cleanup_temp_files(self):
    """Clean up temporary files"""
    try:
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        deleted_count = 0
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.startswith('analytics_') and file.endswith('.tmp'):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except OSError:
                        pass
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
    
    except Exception as exc:
        return {
            'success': False,
            'error': str(exc)
        }
```

## Data Analysis & Visualization

### Matplotlib Agg Backend Usage (NON-NEGOTIABLE)
```python
# CRITICAL: Always use Agg backend for server-side plotting
import matplotlib
matplotlib.use('Agg')  # Must be set before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from lifelines import KaplanMeierFitter

# Example: Generate statistical plot
def create_analysis_plot(data, plot_type='histogram'):
    """Create server-side plot using Agg backend"""
    plt.figure(figsize=(10, 6))
    
    if plot_type == 'histogram':
        sns.histplot(data, kde=True)
    elif plot_type == 'correlation':
        sns.heatmap(data.corr(), annot=True, cmap='coolwarm')
    elif plot_type == 'survival':
        kmf = KaplanMeierFitter()
        kmf.fit(data['duration'], data['event'])
        kmf.plot()
    
    plt.tight_layout()
    
    # Save plot as PNG (server-side generation)
    plot_path = f'/tmp/analysis_plot_{plot_type}.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()  # Important: Close figure to free memory
    
    return plot_path
```

## Storage Management

### Check Storage Usage
```bash
# Get user storage usage
curl -X GET "http://localhost:8000/api/storage/usage/" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "storage_limit": 262144000,
  "storage_used": 52428800,
  "storage_remaining": 209715200,
  "usage_percentage": 20.0,
  "warning_sent": false
}
```

### Clean Up Storage
```bash
# Clean up old analysis results
curl -X POST "http://localhost:8000/api/storage/cleanup/" \
  -H "Cookie: sessionid=your_session_id" \
  -H "X-CSRFToken: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "keep_recent": 10,
    "delete_archived": true
  }'

# Response
{
  "success": true,
  "space_freed": 10485760,
  "items_deleted": 5
}
```

## System Health & Monitoring

### Check System Health
```bash
# Get system health status
curl -X GET "http://localhost:8000/api/health/" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "status": "healthy",
  "metrics": [
    {
      "metric_name": "response_time",
      "metric_value": 150.5,
      "metric_unit": "ms",
      "status": "normal"
    }
  ],
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### Get Detailed Metrics
```bash
# Get detailed system metrics
curl -X GET "http://localhost:8000/api/health/metrics/?hours=24" \
  -H "Cookie: sessionid=your_session_id"
```

## Error Management

### View Error Logs
```bash
# Get user error logs
curl -X GET "http://localhost:8000/api/errors/?limit=20" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "errors": [
    {
      "id": 1,
      "error_type": "FileProcessingError",
      "error_message": "Invalid file format",
      "correlation_id": "abc123def456",
      "resolved": false,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 1
}
```

### Resolve Errors
```bash
# Mark error as resolved
curl -X POST "http://localhost:8000/api/errors/1/resolve/" \
  -H "Cookie: sessionid=your_session_id" \
  -H "X-CSRFToken: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution_notes": "Fixed file format validation"
  }'
```

## LangChain Sandbox & Code Execution

### Execute User Query in Sandbox
```bash
# Execute user query in secure sandbox
curl -X POST "http://localhost:8000/api/sandbox/execute/" \
  -H "Cookie: sessionid=your_session_id" \
  -H "X-CSRFToken: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123",
    "user_query": "Create a correlation matrix for all numeric columns and plot it as a heatmap",
    "context_data": {
      "dataset_id": "dataset_123",
      "numeric_columns": ["age", "income", "score"]
    },
    "max_execution_time": 30,
    "max_memory_mb": 512
  }'

# Response (Success)
{
  "success": true,
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "execution_status": "completed",
  "output_data": {
    "text": "Correlation matrix analysis completed successfully",
    "tables": [
      {
        "title": "Correlation Matrix",
        "data": [
          ["", "age", "income", "score"],
          ["age", "1.00", "0.75", "0.60"],
          ["income", "0.75", "1.00", "0.85"],
          ["score", "0.60", "0.85", "1.00"]
        ]
      }
    ],
    "plots": [
      "/media/generated_images/sessions/abc123/correlation_heatmap_20241219_104500.png"
    ],
    "summary": "Execution completed successfully. Generated 1 plots and 1 tables."
  },
  "images_generated": [1],
  "tables_generated": [{"title": "Correlation Matrix", "data": [...]}],
  "execution_time_ms": 1250,
  "memory_used_mb": 45.2
}

# Response (Error with Suggestions)
{
  "success": false,
  "execution_id": "550e8400-e29b-41d4-a716-446655440001",
  "execution_status": "failed",
  "error_message": "NameError: name 'data' is not defined",
  "suggestions": [
    "Load your dataset first using: data = pd.read_parquet('your_file.parquet')",
    "Check if the dataset variable is properly defined",
    "Verify the dataset path is correct",
    "Ensure the dataset is loaded before analysis",
    "Consider using the session context data for column information"
  ]
}
```

### Check Sandbox Execution Status
```bash
# Check execution status
curl -X GET "http://localhost:8000/api/sandbox/status/550e8400-e29b-41d4-a716-446655440000/" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "execution": {
    "id": 1,
    "session_id": "abc123",
    "execution_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_query": "Create a correlation matrix for all numeric columns",
    "execution_status": "completed",
    "execution_time_ms": 1250,
    "memory_used_mb": 45.2,
    "libraries_used": ["pandas", "numpy", "matplotlib", "seaborn"],
    "created_at": "2024-12-19T10:45:00Z",
    "completed_at": "2024-12-19T10:45:01Z"
  },
  "status": "completed"
}
```

### Retry Failed Execution
```bash
# Retry failed execution with LLM corrections
curl -X POST "http://localhost:8000/api/sandbox/retry/550e8400-e29b-41d4-a716-446655440001/" \
  -H "Cookie: sessionid=your_session_id" \
  -H "X-CSRFToken: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "user_feedback": "The dataset should be loaded from the session context",
    "max_retries": 3
  }'

# Response
{
  "success": true,
  "new_execution_id": "550e8400-e29b-41d4-a716-446655440002",
  "retry_count": 1
}
```

### Get Sandbox Execution History
```bash
# Get execution history for session
curl -X GET "http://localhost:8000/api/sandbox/history/abc123/?limit=10&status=completed" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "executions": [
    {
      "id": 1,
      "execution_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_query": "Create a correlation matrix for all numeric columns",
      "execution_status": "completed",
      "execution_time_ms": 1250,
      "memory_used_mb": 45.2,
      "created_at": "2024-12-19T10:45:00Z"
    },
    {
      "id": 2,
      "execution_id": "550e8400-e29b-41d4-a716-446655440002",
      "user_query": "Plot a histogram of age distribution",
      "execution_status": "completed",
      "execution_time_ms": 890,
      "memory_used_mb": 32.1,
      "created_at": "2024-12-19T10:47:00Z"
    }
  ],
  "total_count": 2
}
```

## LLM Batch Processing & Image Management

### Process Analysis Results in Batch
```bash
# Process multiple analysis results with LLM
curl -X POST "http://localhost:8000/api/llm/batch/process/" \
  -H "Cookie: sessionid=your_session_id" \
  -H "X-CSRFToken: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123",
    "analysis_results": [
      {
        "result_id": 1,
        "result_type": "statistical",
        "data": {
          "mean": 35.2,
          "median": 34.0,
          "std": 12.5
        },
        "images": [
          {
            "image_id": 1,
            "image_type": "histogram",
            "access_url": "/media/generated_images/sessions/abc123/histogram_20241219_103000.png"
          }
        ]
      },
      {
        "result_id": 2,
        "result_type": "visualization",
        "data": {
          "correlation_matrix": [[1.0, 0.75], [0.75, 1.0]]
        },
        "images": [
          {
            "image_id": 2,
            "image_type": "correlation_matrix",
            "access_url": "/media/generated_images/sessions/abc123/correlation_20241219_103100.png"
          }
        ]
      }
    ],
    "prompt_template": "Analyze these statistical results and provide comprehensive insights:"
  }'

# Response
{
  "success": true,
  "batch_id": "batch_abc123_1703000000.123",
  "results": [
    {
      "result_id": 1,
      "interpretation": "The age distribution shows a normal distribution with mean 35.2...",
      "formatted_response": {
        "text": "Statistical analysis reveals...",
        "tables": [
          {
            "title": "Descriptive Statistics",
            "data": [["Mean", "35.2"], ["Median", "34.0"], ["Std Dev", "12.5"]]
          }
        ],
        "images": [
          {
            "description": "Histogram shows normal distribution",
            "access_url": "/media/generated_images/sessions/abc123/histogram_20241219_103000.png"
          }
        ]
      },
      "tokens_used": 450
    }
  ]
}
```

### Get Generated Image
```bash
# Get specific image by ID
curl -X GET "http://localhost:8000/api/images/1/?format=base64" \
  -H "Cookie: sessionid=your_session_id"

# Response (base64 format)
{
  "image": {
    "id": 1,
    "session_id": "abc123",
    "image_type": "histogram",
    "file_name": "histogram_20241219_103000.png",
    "file_size": 245760,
    "image_format": "PNG",
    "width": 800,
    "height": 600,
    "dpi": 300,
    "access_url": "/media/generated_images/sessions/abc123/histogram_20241219_103000.png",
    "created_at": "2024-12-19T10:30:00Z"
  },
  "base64_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "access_url": "/media/generated_images/sessions/abc123/histogram_20241219_103000.png"
}
```

### Get All Images for Session
```bash
# Get all images for a session
curl -X GET "http://localhost:8000/api/images/session/abc123/?image_type=histogram&limit=10" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "images": [
    {
      "id": 1,
      "session_id": "abc123",
      "image_type": "histogram",
      "file_name": "histogram_20241219_103000.png",
      "access_url": "/media/generated_images/sessions/abc123/histogram_20241219_103000.png",
      "created_at": "2024-12-19T10:30:00Z"
    },
    {
      "id": 2,
      "session_id": "abc123",
      "image_type": "scatter_plot",
      "file_name": "scatter_20241219_103100.png",
      "access_url": "/media/generated_images/sessions/abc123/scatter_20241219_103100.png",
      "created_at": "2024-12-19T10:31:00Z"
    }
  ],
  "total_count": 2
}
```

## LLM Context Management

### Get LLM Context
```bash
# Get LLM context for current session
curl -X GET "http://localhost:8000/api/llm/context/abc123/?context_type=chat_history" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "context": {
    "id": 1,
    "session_id": "abc123",
    "context_type": "chat_history",
    "message_count": 8,
    "is_active": true,
    "last_updated": "2024-01-15T10:30:00Z"
  },
  "messages": [
    {
      "role": "user",
      "content": "What does the age distribution tell us?",
      "timestamp": "2024-01-15T10:25:00Z"
    },
    {
      "role": "assistant",
      "content": "The age distribution shows a normal distribution with mean 35.2...",
      "timestamp": "2024-01-15T10:25:30Z"
    }
  ]
}
```

### Update LLM Context
```bash
# Update LLM context with new messages
curl -X POST "http://localhost:8000/api/llm/context/abc123/update/" \
  -H "Cookie: sessionid=your_session_id" \
  -H "X-CSRFToken: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "context_type": "chat_history",
    "new_messages": [
      {
        "role": "user",
        "content": "Can you explain the correlation between age and income?",
        "timestamp": "2024-01-15T10:35:00Z"
      }
    ]
  }'

# Response
{
  "success": true,
  "context_id": 1,
  "message_count": 9
}
```

## Audit Trail & Compliance

### View Audit Trail
```bash
# Get audit trail for current user
curl -X GET "http://localhost:8000/api/audit/trail/?limit=20" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "audit_records": [
    {
      "id": 1,
      "action_type": "file_upload",
      "action_category": "data_management",
      "action_description": "Uploaded dataset 'sales_data.csv'",
      "resource_type": "dataset",
      "resource_id": 1,
      "resource_name": "sales_data.csv",
      "ip_address": "192.168.1.100",
      "request_path": "/api/upload/",
      "request_method": "POST",
      "response_status": 200,
      "duration_ms": 1250,
      "success": true,
      "correlation_id": "abc123def456",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 150
}
```

### Export Audit Trail
```bash
# Export audit trail for compliance
curl -X POST "http://localhost:8000/api/audit/export/" \
  -H "Cookie: sessionid=your_session_id" \
  -H "X-CSRFToken: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "format": "csv",
    "include_system_events": false
  }' \
  --output audit_export.csv
```

### Generate Compliance Report
```bash
# Generate compliance report
curl -X GET "http://localhost:8000/api/audit/reports/compliance/?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z&report_type=summary" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "report_type": "summary",
  "period": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z"
  },
  "summary": {
    "total_actions": 1250,
    "successful_actions": 1180,
    "failed_actions": 70,
    "unique_users": 25,
    "data_access_events": 450
  },
  "details": [
    {
      "action_type": "file_upload",
      "count": 150,
      "success_rate": 95.5
    },
    {
      "action_type": "analysis_execute",
      "count": 800,
      "success_rate": 98.2
    }
  ]
}
```

## Backup & Recovery

### Check Backup Status
```bash
# Get backup status
curl -X GET "http://localhost:8000/api/backup/status/" \
  -H "Cookie: sessionid=your_session_id"

# Response
{
  "last_backup": "2024-01-15T02:00:00Z",
  "backup_status": "completed",
  "recent_backups": [
    {
      "id": 1,
      "backup_type": "user_data",
      "backup_size": 52428800,
      "status": "completed",
      "verified": true
    }
  ]
}
```

### Trigger Manual Backup
```bash
# Trigger manual backup (admin only)
curl -X POST "http://localhost:8000/api/backup/trigger/" \
  -H "Cookie: sessionid=your_session_id" \
  -H "X-CSRFToken: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "backup_type": "user_data"
  }'
```

## Next Steps

1. **Customize Analysis Tools**: Add your specific statistical tools
2. **Configure Google AI**: Set up Google AI API with your API key
3. **Deploy to Production**: Configure production database and Redis
4. **Add Authentication**: Implement user registration and login
5. **Extend UI**: Customize the three-panel layout for your needs
6. **Monitor Performance**: Set up alerting for critical metrics
7. **Configure Backups**: Set up automated backup schedules
8. **Test Error Handling**: Verify error recovery procedures

## Support

- **Documentation**: `/docs/` directory
- **API Reference**: `/api/docs/` endpoint
- **Issue Tracking**: GitHub Issues
- **Development Guide**: `DEVELOPMENT.md`
