from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

# Create your models here.

class User(AbstractUser):
    """
    Extended User model with token and storage limits for the analytical system
    """
    # Override the groups and user_permissions fields to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="analytics_user_set",
        related_query_name="analytics_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="analytics_user_set",
        related_query_name="analytics_user",
    )
    # Token Management
    token_usage_current_month = models.PositiveIntegerField(
        default=0,
        help_text="Current month's token usage"
    )
    token_usage_last_reset = models.DateTimeField(
        default=timezone.now,
        help_text="When token usage was last reset"
    )
    max_tokens_per_month = models.PositiveIntegerField(
        default=1000000,  # 1M tokens per month
        help_text="Maximum tokens allowed per month"
    )
    
    # Storage Management
    storage_used_bytes = models.PositiveBigIntegerField(
        default=0,
        help_text="Current storage usage in bytes"
    )
    max_storage_bytes = models.PositiveBigIntegerField(
        default=262144000,  # 250MB = 250 * 1024 * 1024 bytes
        help_text="Maximum storage allowed in bytes"
    )
    storage_warning_sent = models.BooleanField(
        default=False,
        help_text="Whether storage warning has been sent"
    )
    
    # User Preferences
    preferred_theme = models.CharField(
        max_length=20,
        default='dark',
        choices=[
            ('dark', 'Dark Theme'),
            ('light', 'Light Theme'),
            ('auto', 'Auto (System)')
        ],
        help_text="User's preferred UI theme"
    )
    auto_save_analysis = models.BooleanField(
        default=True,
        help_text="Whether to automatically save analysis results"
    )
    notification_preferences = models.JSONField(
        default=dict,
        help_text="User notification preferences"
    )
    
    # Account Status
    is_premium = models.BooleanField(
        default=False,
        help_text="Whether user has premium features"
    )
    account_suspended = models.BooleanField(
        default=False,
        help_text="Whether account is suspended"
    )
    suspension_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for account suspension"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(
        default=timezone.now,
        help_text="Last user activity timestamp"
    )
    
    class Meta:
        db_table = 'analytics_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['token_usage_current_month']),
            models.Index(fields=['storage_used_bytes']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['is_premium']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    @property
    def storage_used_mb(self):
        """Return storage used in MB"""
        return round(self.storage_used_bytes / (1024 * 1024), 2)
    
    @property
    def max_storage_mb(self):
        """Return max storage in MB"""
        return round(self.max_storage_bytes / (1024 * 1024), 2)
    
    @property
    def storage_usage_percentage(self):
        """Return storage usage as percentage"""
        if self.max_storage_bytes == 0:
            return 0
        return round((self.storage_used_bytes / self.max_storage_bytes) * 100, 2)
    
    @property
    def token_usage_percentage(self):
        """Return token usage as percentage"""
        if self.max_tokens_per_month == 0:
            return 0
        return round((self.token_usage_current_month / self.max_tokens_per_month) * 100, 2)
    
    def can_use_tokens(self, token_count):
        """Check if user can use specified number of tokens"""
        return (self.token_usage_current_month + token_count) <= self.max_tokens_per_month
    
    def can_upload_file(self, file_size_bytes):
        """Check if user can upload file of specified size"""
        return (self.storage_used_bytes + file_size_bytes) <= self.max_storage_bytes
    
    def add_token_usage(self, token_count):
        """Add token usage to current month"""
        self.token_usage_current_month += token_count
        self.save(update_fields=['token_usage_current_month'])
    
    def add_storage_usage(self, bytes_count):
        """Add storage usage"""
        self.storage_used_bytes += bytes_count
        self.save(update_fields=['storage_used_bytes'])
    
    def remove_storage_usage(self, bytes_count):
        """Remove storage usage"""
        self.storage_used_bytes = max(0, self.storage_used_bytes - bytes_count)
        self.save(update_fields=['storage_used_bytes'])
    
    def reset_monthly_token_usage(self):
        """Reset monthly token usage (called by Celery task)"""
        self.token_usage_current_month = 0
        self.token_usage_last_reset = timezone.now()
        self.save(update_fields=['token_usage_current_month', 'token_usage_last_reset'])
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def get_storage_warning_threshold(self):
        """Get storage warning threshold (80% of max)"""
        return int(self.max_storage_bytes * 0.8)
    
    def should_send_storage_warning(self):
        """Check if storage warning should be sent"""
        return (
            self.storage_used_bytes >= self.get_storage_warning_threshold() 
            and not self.storage_warning_sent
        )
    
    def mark_storage_warning_sent(self):
        """Mark storage warning as sent"""
        self.storage_warning_sent = True
        self.save(update_fields=['storage_warning_sent'])
    
    def get_usage_summary(self):
        """Get comprehensive usage summary"""
        return {
            'tokens': {
                'used': self.token_usage_current_month,
                'max': self.max_tokens_per_month,
                'percentage': self.token_usage_percentage,
                'remaining': self.max_tokens_per_month - self.token_usage_current_month
            },
            'storage': {
                'used_mb': self.storage_used_mb,
                'max_mb': self.max_storage_mb,
                'used_bytes': self.storage_used_bytes,
                'max_bytes': self.max_storage_bytes,
                'percentage': self.storage_usage_percentage,
                'remaining_mb': self.max_storage_mb - self.storage_used_mb
            },
            'account': {
                'is_premium': self.is_premium,
                'suspended': self.account_suspended,
                'last_activity': self.last_activity
            }
        }


class Dataset(models.Model):
    """
    Dataset model with Parquet integration for analytical data storage
    """
    # Basic Information
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name of the dataset"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the dataset"
    )
    original_filename = models.CharField(
        max_length=255,
        help_text="Original filename when uploaded"
    )
    
    # File Information
    file_size_bytes = models.PositiveBigIntegerField(
        help_text="Size of the original file in bytes"
    )
    file_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of the original file for integrity verification"
    )
    original_format = models.CharField(
        max_length=10,
        choices=[
            ('csv', 'CSV'),
            ('xls', 'XLS'),
            ('xlsx', 'XLSX'),
            ('json', 'JSON'),
        ],
        help_text="Original file format"
    )
    
    # Parquet Integration
    parquet_path = models.CharField(
        max_length=500,
        help_text="Path to the Parquet file in media storage"
    )
    parquet_size_bytes = models.PositiveBigIntegerField(
        default=0,
        help_text="Size of the Parquet file in bytes"
    )
    parquet_created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the Parquet file was created"
    )
    
    # Data Information
    row_count = models.PositiveIntegerField(
        help_text="Number of rows in the dataset"
    )
    column_count = models.PositiveIntegerField(
        help_text="Number of columns in the dataset"
    )
    data_types = models.JSONField(
        default=dict,
        help_text="Column data types detected during processing"
    )
    
    # Processing Information
    processing_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        help_text="Current processing status"
    )
    processing_errors = models.JSONField(
        default=list,
        help_text="Any errors encountered during processing"
    )
    processing_warnings = models.JSONField(
        default=list,
        help_text="Warnings generated during processing"
    )
    
    # Security Information
    security_scan_passed = models.BooleanField(
        default=False,
        help_text="Whether security scan passed"
    )
    security_warnings = models.JSONField(
        default=list,
        help_text="Security warnings from scan"
    )
    sanitized = models.BooleanField(
        default=False,
        help_text="Whether data was sanitized (formulas/macros removed)"
    )
    
    # Data Quality
    data_quality_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Data quality score (0.0 to 1.0)"
    )
    completeness_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Data completeness score (0.0 to 1.0)"
    )
    consistency_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Data consistency score (0.0 to 1.0)"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata about the dataset"
    )
    tags = models.JSONField(
        default=list,
        help_text="User-defined tags for categorization"
    )
    
    # Access Control
    is_public = models.BooleanField(
        default=False,
        help_text="Whether dataset is publicly accessible"
    )
    access_level = models.CharField(
        max_length=20,
        default='private',
        choices=[
            ('private', 'Private'),
            ('shared', 'Shared'),
            ('public', 'Public'),
        ],
        help_text="Dataset access level"
    )
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='datasets',
        help_text="User who uploaded the dataset"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(
        default=timezone.now,
        help_text="When dataset was last accessed"
    )
    
    class Meta:
        db_table = 'analytics_dataset'
        verbose_name = 'Dataset'
        verbose_name_plural = 'Datasets'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['processing_status']),
            models.Index(fields=['file_hash']),
            models.Index(fields=['original_format']),
            models.Index(fields=['row_count']),
            models.Index(fields=['data_quality_score']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.original_filename})"
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size_bytes / (1024 * 1024), 2)
    
    @property
    def parquet_size_mb(self):
        """Return Parquet file size in MB"""
        return round(self.parquet_size_bytes / (1024 * 1024), 2)
    
    @property
    def compression_ratio(self):
        """Return compression ratio (original size / parquet size)"""
        if self.parquet_size_bytes == 0:
            return 0
        return round(self.file_size_bytes / self.parquet_size_bytes, 2)
    
    @property
    def is_processed(self):
        """Check if dataset is fully processed"""
        return self.processing_status == 'completed'
    
    @property
    def has_errors(self):
        """Check if dataset has processing errors"""
        return len(self.processing_errors) > 0
    
    @property
    def has_warnings(self):
        """Check if dataset has processing warnings"""
        return len(self.processing_warnings) > 0 or len(self.security_warnings) > 0
    
    def get_column_types_summary(self):
        """Get summary of column types"""
        if not self.data_types:
            return {}
        
        type_counts = {}
        for col_name, col_type in self.data_types.items():
            type_counts[col_type] = type_counts.get(col_type, 0) + 1
        
        return type_counts
    
    def get_numeric_columns(self):
        """Get list of numeric column names"""
        if not self.data_types:
            return []
        return [col for col, dtype in self.data_types.items() if dtype == 'numeric']
    
    def get_categorical_columns(self):
        """Get list of categorical column names"""
        if not self.data_types:
            return []
        return [col for col, dtype in self.data_types.items() if dtype == 'categorical']
    
    def get_datetime_columns(self):
        """Get list of datetime column names"""
        if not self.data_types:
            return []
        return [col for col, dtype in self.data_types.items() if dtype == 'datetime']
    
    def update_last_accessed(self):
        """Update last accessed timestamp"""
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])
    
    def add_processing_error(self, error_message, error_code=None):
        """Add a processing error"""
        error = {
            'message': error_message,
            'code': error_code,
            'timestamp': timezone.now().isoformat()
        }
        self.processing_errors.append(error)
        self.save(update_fields=['processing_errors'])
    
    def add_processing_warning(self, warning_message, warning_code=None):
        """Add a processing warning"""
        warning = {
            'message': warning_message,
            'code': warning_code,
            'timestamp': timezone.now().isoformat()
        }
        self.processing_warnings.append(warning)
        self.save(update_fields=['processing_warnings'])
    
    def add_security_warning(self, warning_message, warning_code=None):
        """Add a security warning"""
        warning = {
            'message': warning_message,
            'code': warning_code,
            'timestamp': timezone.now().isoformat()
        }
        self.security_warnings.append(warning)
        self.save(update_fields=['security_warnings'])
    
    def calculate_data_quality_scores(self):
        """Calculate and update data quality scores"""
        # This would be implemented with actual data analysis
        # For now, we'll set default values
        self.data_quality_score = 0.95
        self.completeness_score = 0.90
        self.consistency_score = 0.85
        self.save(update_fields=['data_quality_score', 'completeness_score', 'consistency_score'])
    
    def get_processing_summary(self):
        """Get comprehensive processing summary"""
        return {
            'status': self.processing_status,
            'file_info': {
                'original_size_mb': self.file_size_mb,
                'parquet_size_mb': self.parquet_size_mb,
                'compression_ratio': self.compression_ratio,
                'row_count': self.row_count,
                'column_count': self.column_count
            },
            'data_quality': {
                'overall_score': self.data_quality_score,
                'completeness': self.completeness_score,
                'consistency': self.consistency_score
            },
            'column_types': self.get_column_types_summary(),
            'errors': len(self.processing_errors),
            'warnings': len(self.processing_warnings) + len(self.security_warnings),
            'security': {
                'scan_passed': self.security_scan_passed,
                'sanitized': self.sanitized,
                'warnings': len(self.security_warnings)
            }
        }


class DatasetColumn(models.Model):
    """
    DatasetColumn model with type categorization for analytical data processing
    """
    # Basic Information
    name = models.CharField(
        max_length=255,
        help_text="Column name as it appears in the dataset"
    )
    display_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Human-readable display name for the column"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of what this column represents"
    )
    
    # Data Type Information
    detected_type = models.CharField(
        max_length=20,
        choices=[
            ('numeric', 'Numeric'),
            ('categorical', 'Categorical'),
            ('datetime', 'DateTime'),
            ('text', 'Text'),
            ('boolean', 'Boolean'),
            ('mixed', 'Mixed'),
            ('unknown', 'Unknown'),
        ],
        help_text="Automatically detected data type"
    )
    confirmed_type = models.CharField(
        max_length=20,
        choices=[
            ('numeric', 'Numeric'),
            ('categorical', 'Categorical'),
            ('datetime', 'DateTime'),
            ('text', 'Text'),
            ('boolean', 'Boolean'),
            ('mixed', 'Mixed'),
            ('unknown', 'Unknown'),
        ],
        blank=True,
        null=True,
        help_text="User-confirmed data type (overrides detected type)"
    )
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score for type detection (0.0 to 1.0)"
    )
    
    # Data Quality Information
    null_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of null/missing values"
    )
    null_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage of null values (0.0 to 100.0)"
    )
    unique_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of unique values"
    )
    unique_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage of unique values (0.0 to 100.0)"
    )
    
    # Statistical Information (for numeric columns)
    min_value = models.FloatField(
        blank=True,
        null=True,
        help_text="Minimum value (for numeric columns)"
    )
    max_value = models.FloatField(
        blank=True,
        null=True,
        help_text="Maximum value (for numeric columns)"
    )
    mean_value = models.FloatField(
        blank=True,
        null=True,
        help_text="Mean value (for numeric columns)"
    )
    median_value = models.FloatField(
        blank=True,
        null=True,
        help_text="Median value (for numeric columns)"
    )
    std_deviation = models.FloatField(
        blank=True,
        null=True,
        help_text="Standard deviation (for numeric columns)"
    )
    
    # Categorical Information
    top_values = models.JSONField(
        default=list,
        help_text="Most frequent values (for categorical columns)"
    )
    value_counts = models.JSONField(
        default=dict,
        help_text="Value frequency counts (for categorical columns)"
    )
    
    # DateTime Information
    date_format = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Detected date format (for datetime columns)"
    )
    timezone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Detected timezone (for datetime columns)"
    )
    
    # Data Quality Flags
    has_outliers = models.BooleanField(
        default=False,
        help_text="Whether column has statistical outliers"
    )
    has_duplicates = models.BooleanField(
        default=False,
        help_text="Whether column has duplicate values"
    )
    is_primary_key = models.BooleanField(
        default=False,
        help_text="Whether this column could be a primary key"
    )
    is_foreign_key = models.BooleanField(
        default=False,
        help_text="Whether this column could be a foreign key"
    )
    
    # Analysis Suitability
    suitable_for_correlation = models.BooleanField(
        default=False,
        help_text="Whether column is suitable for correlation analysis"
    )
    suitable_for_regression = models.BooleanField(
        default=False,
        help_text="Whether column is suitable for regression analysis"
    )
    suitable_for_clustering = models.BooleanField(
        default=False,
        help_text="Whether column is suitable for clustering analysis"
    )
    suitable_for_classification = models.BooleanField(
        default=False,
        help_text="Whether column is suitable for classification analysis"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata about the column"
    )
    tags = models.JSONField(
        default=list,
        help_text="User-defined tags for categorization"
    )
    
    # Relationships
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='columns',
        help_text="Dataset this column belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_dataset_column'
        verbose_name = 'Dataset Column'
        verbose_name_plural = 'Dataset Columns'
        unique_together = ['dataset', 'name']
        indexes = [
            models.Index(fields=['dataset', 'detected_type']),
            models.Index(fields=['detected_type']),
            models.Index(fields=['confidence_score']),
            models.Index(fields=['null_percentage']),
            models.Index(fields=['unique_percentage']),
        ]
        ordering = ['dataset', 'name']
    
    def __str__(self):
        return f"{self.dataset.name}.{self.name} ({self.get_effective_type()})"
    
    def get_effective_type(self):
        """Get the effective data type (confirmed or detected)"""
        return self.confirmed_type or self.detected_type
    
    @property
    def is_numeric(self):
        """Check if column is numeric type"""
        return self.get_effective_type() == 'numeric'
    
    @property
    def is_categorical(self):
        """Check if column is categorical type"""
        return self.get_effective_type() == 'categorical'
    
    @property
    def is_datetime(self):
        """Check if column is datetime type"""
        return self.get_effective_type() == 'datetime'
    
    @property
    def is_text(self):
        """Check if column is text type"""
        return self.get_effective_type() == 'text'
    
    @property
    def is_boolean(self):
        """Check if column is boolean type"""
        return self.get_effective_type() == 'boolean'
    
    @property
    def completeness_score(self):
        """Calculate data completeness score"""
        return 100.0 - self.null_percentage
    
    @property
    def cardinality_score(self):
        """Calculate cardinality score (uniqueness)"""
        return self.unique_percentage
    
    def get_statistical_summary(self):
        """Get statistical summary for the column"""
        summary = {
            'type': self.get_effective_type(),
            'confidence': self.confidence_score,
            'completeness': self.completeness_score,
            'cardinality': self.cardinality_score,
            'null_count': self.null_count,
            'unique_count': self.unique_count,
        }
        
        if self.is_numeric:
            summary.update({
                'min': self.min_value,
                'max': self.max_value,
                'mean': self.mean_value,
                'median': self.median_value,
                'std_dev': self.std_deviation,
                'has_outliers': self.has_outliers,
            })
        elif self.is_categorical:
            summary.update({
                'top_values': self.top_values,
                'value_counts': self.value_counts,
            })
        elif self.is_datetime:
            summary.update({
                'date_format': self.date_format,
                'timezone': self.timezone,
            })
        
        return summary
    
    def get_analysis_suitability(self):
        """Get analysis suitability flags"""
        return {
            'correlation': self.suitable_for_correlation,
            'regression': self.suitable_for_regression,
            'clustering': self.suitable_for_clustering,
            'classification': self.suitable_for_classification,
        }
    
    def update_statistics(self, stats_data):
        """Update column statistics from analysis"""
        self.null_count = stats_data.get('null_count', 0)
        self.null_percentage = stats_data.get('null_percentage', 0.0)
        self.unique_count = stats_data.get('unique_count', 0)
        self.unique_percentage = stats_data.get('unique_percentage', 0.0)
        
        if self.is_numeric:
            self.min_value = stats_data.get('min_value')
            self.max_value = stats_data.get('max_value')
            self.mean_value = stats_data.get('mean_value')
            self.median_value = stats_data.get('median_value')
            self.std_deviation = stats_data.get('std_deviation')
            self.has_outliers = stats_data.get('has_outliers', False)
        
        if self.is_categorical:
            self.top_values = stats_data.get('top_values', [])
            self.value_counts = stats_data.get('value_counts', {})
        
        if self.is_datetime:
            self.date_format = stats_data.get('date_format')
            self.timezone = stats_data.get('timezone')
        
        self.save()
    
    def confirm_type(self, new_type):
        """Confirm/override the detected type"""
        self.confirmed_type = new_type
        self.save(update_fields=['confirmed_type'])
    
    def add_tag(self, tag):
        """Add a tag to the column"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save(update_fields=['tags'])
    
    def remove_tag(self, tag):
        """Remove a tag from the column"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save(update_fields=['tags'])
    
    def get_quality_report(self):
        """Get comprehensive data quality report"""
        return {
            'column_info': {
                'name': self.name,
                'type': self.get_effective_type(),
                'confidence': self.confidence_score,
            },
            'completeness': {
                'null_count': self.null_count,
                'null_percentage': self.null_percentage,
                'completeness_score': self.completeness_score,
            },
            'uniqueness': {
                'unique_count': self.unique_count,
                'unique_percentage': self.unique_percentage,
                'cardinality_score': self.cardinality_score,
            },
            'statistics': self.get_statistical_summary(),
            'suitability': self.get_analysis_suitability(),
            'flags': {
                'has_outliers': self.has_outliers,
                'has_duplicates': self.has_duplicates,
                'is_primary_key': self.is_primary_key,
                'is_foreign_key': self.is_foreign_key,
            }
        }


class AnalysisTool(models.Model):
    """
    AnalysisTool model with LangChain integration for analytical operations
    """
    # Basic Information
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique name identifier for the tool"
    )
    display_name = models.CharField(
        max_length=255,
        help_text="Human-readable display name"
    )
    description = models.TextField(
        help_text="Detailed description of what the tool does"
    )
    category = models.CharField(
        max_length=50,
        choices=[
            ('descriptive', 'Descriptive Statistics'),
            ('inferential', 'Inferential Statistics'),
            ('regression', 'Regression Analysis'),
            ('clustering', 'Clustering'),
            ('classification', 'Classification'),
            ('time_series', 'Time Series'),
            ('visualization', 'Visualization'),
            ('data_quality', 'Data Quality'),
            ('custom', 'Custom'),
        ],
        help_text="Tool category for organization"
    )
    
    # LangChain Integration
    langchain_tool_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="LangChain tool identifier"
    )
    tool_class = models.CharField(
        max_length=255,
        help_text="Python class path for the tool implementation"
    )
    tool_function = models.CharField(
        max_length=255,
        help_text="Function name within the tool class"
    )
    
    # Parameters Schema
    parameters_schema = models.JSONField(
        default=dict,
        help_text="JSON schema defining tool parameters"
    )
    required_parameters = models.JSONField(
        default=list,
        help_text="List of required parameter names"
    )
    optional_parameters = models.JSONField(
        default=list,
        help_text="List of optional parameter names"
    )
    
    # Data Requirements
    required_column_types = models.JSONField(
        default=list,
        help_text="Required column types (numeric, categorical, etc.)"
    )
    min_columns = models.PositiveIntegerField(
        default=1,
        help_text="Minimum number of columns required"
    )
    max_columns = models.PositiveIntegerField(
        default=None,
        blank=True,
        null=True,
        help_text="Maximum number of columns allowed"
    )
    min_rows = models.PositiveIntegerField(
        default=1,
        help_text="Minimum number of rows required"
    )
    
    # Tool Configuration
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the tool is active and available"
    )
    is_premium = models.BooleanField(
        default=False,
        help_text="Whether the tool requires premium access"
    )
    execution_timeout = models.PositiveIntegerField(
        default=300,
        help_text="Maximum execution time in seconds"
    )
    memory_limit_mb = models.PositiveIntegerField(
        default=512,
        help_text="Maximum memory usage in MB"
    )
    
    # Output Configuration
    output_types = models.JSONField(
        default=list,
        help_text="Types of output this tool produces (table, chart, text, etc.)"
    )
    generates_images = models.BooleanField(
        default=False,
        help_text="Whether the tool generates images/charts"
    )
    generates_tables = models.BooleanField(
        default=False,
        help_text="Whether the tool generates data tables"
    )
    generates_text = models.BooleanField(
        default=True,
        help_text="Whether the tool generates text output"
    )
    
    # Usage Statistics
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this tool has been used"
    )
    success_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of successful executions"
    )
    error_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of failed executions"
    )
    average_execution_time = models.FloatField(
        default=0.0,
        help_text="Average execution time in seconds"
    )
    
    # Metadata
    version = models.CharField(
        max_length=20,
        default='1.0.0',
        help_text="Tool version"
    )
    author = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Tool author"
    )
    documentation_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to tool documentation"
    )
    tags = models.JSONField(
        default=list,
        help_text="Tags for categorization and search"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the tool was last used"
    )
    
    class Meta:
        db_table = 'analytics_analysis_tool'
        verbose_name = 'Analysis Tool'
        verbose_name_plural = 'Analysis Tools'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_premium']),
            models.Index(fields=['usage_count']),
        ]
        ordering = ['category', 'display_name']
    
    def __str__(self):
        return f"{self.display_name} ({self.name})"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.usage_count == 0:
            return 0.0
        return round((self.success_count / self.usage_count) * 100, 2)
    
    @property
    def error_rate(self):
        """Calculate error rate percentage"""
        if self.usage_count == 0:
            return 0.0
        return round((self.error_count / self.usage_count) * 100, 2)
    
    def can_use_with_dataset(self, dataset):
        """Check if tool can be used with given dataset"""
        # Check minimum requirements
        if dataset.column_count < self.min_columns:
            return False, f"Dataset has {dataset.column_count} columns, minimum required is {self.min_columns}"
        
        if self.max_columns and dataset.column_count > self.max_columns:
            return False, f"Dataset has {dataset.column_count} columns, maximum allowed is {self.max_columns}"
        
        if dataset.row_count < self.min_rows:
            return False, f"Dataset has {dataset.row_count} rows, minimum required is {self.min_rows}"
        
        # Check column type requirements
        if self.required_column_types:
            dataset_types = set(dataset.data_types.values())
            required_types = set(self.required_column_types)
            if not required_types.issubset(dataset_types):
                missing = required_types - dataset_types
                return False, f"Dataset missing required column types: {', '.join(missing)}"
        
        return True, "Tool can be used with this dataset"
    
    def record_usage(self, success=True, execution_time=None):
        """Record tool usage statistics"""
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        if execution_time is not None:
            # Update average execution time
            total_time = self.average_execution_time * (self.usage_count - 1) + execution_time
            self.average_execution_time = total_time / self.usage_count
        
        self.last_used = timezone.now()
        self.save(update_fields=[
            'usage_count', 'success_count', 'error_count', 
            'average_execution_time', 'last_used'
        ])
    
    def get_usage_summary(self):
        """Get comprehensive usage summary"""
        return {
            'usage_stats': {
                'total_uses': self.usage_count,
                'successful': self.success_count,
                'failed': self.error_count,
                'success_rate': self.success_rate,
                'error_rate': self.error_rate,
            },
            'performance': {
                'average_execution_time': self.average_execution_time,
                'execution_timeout': self.execution_timeout,
                'memory_limit_mb': self.memory_limit_mb,
            },
            'last_used': self.last_used,
            'requirements': {
                'min_columns': self.min_columns,
                'max_columns': self.max_columns,
                'min_rows': self.min_rows,
                'required_column_types': self.required_column_types,
            }
        }


class AnalysisSession(models.Model):
    """
    AnalysisSession model with dataset tagging for session management
    """
    # Basic Information
    name = models.CharField(
        max_length=255,
        help_text="Session name"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Session description"
    )
    
    # Session Configuration
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the session is currently active"
    )
    auto_save = models.BooleanField(
        default=True,
        help_text="Whether to automatically save analysis results"
    )
    
    # Dataset Association
    primary_dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='primary_sessions',
        help_text="Primary dataset for this session"
    )
    additional_datasets = models.ManyToManyField(
        Dataset,
        blank=True,
        related_name='additional_sessions',
        help_text="Additional datasets used in this session"
    )
    
    # Session State
    current_analysis_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="ID of the current analysis being performed"
    )
    session_data = models.JSONField(
        default=dict,
        help_text="Session-specific data and state"
    )
    user_preferences = models.JSONField(
        default=dict,
        help_text="User preferences for this session"
    )
    
    # Analysis History
    analysis_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of analyses performed in this session"
    )
    last_analysis_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the last analysis was performed"
    )
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analysis_sessions',
        help_text="User who owns this session"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(
        default=timezone.now,
        help_text="When the session was last accessed"
    )
    
    class Meta:
        db_table = 'analytics_analysis_session'
        verbose_name = 'Analysis Session'
        verbose_name_plural = 'Analysis Sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['primary_dataset']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_accessed']),
        ]
        ordering = ['-last_accessed']
    
    def __str__(self):
        return f"{self.name} ({self.primary_dataset.name})"
    
    def get_all_datasets(self):
        """Get all datasets associated with this session"""
        datasets = [self.primary_dataset]
        datasets.extend(self.additional_datasets.all())
        return datasets
    
    def add_dataset(self, dataset):
        """Add a dataset to the session"""
        if dataset != self.primary_dataset:
            self.additional_datasets.add(dataset)
    
    def remove_dataset(self, dataset):
        """Remove a dataset from the session"""
        if dataset != self.primary_dataset:
            self.additional_datasets.remove(dataset)
    
    def update_last_accessed(self):
        """Update last accessed timestamp"""
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])
    
    def increment_analysis_count(self):
        """Increment analysis count and update last analysis time"""
        self.analysis_count += 1
        self.last_analysis_at = timezone.now()
        self.save(update_fields=['analysis_count', 'last_analysis_at'])
    
    def get_session_summary(self):
        """Get comprehensive session summary"""
        return {
            'session_info': {
                'name': self.name,
                'description': self.description,
                'is_active': self.is_active,
                'auto_save': self.auto_save,
            },
            'datasets': {
                'primary': {
                    'id': self.primary_dataset.id,
                    'name': self.primary_dataset.name,
                    'row_count': self.primary_dataset.row_count,
                    'column_count': self.primary_dataset.column_count,
                },
                'additional': [
                    {
                        'id': dataset.id,
                        'name': dataset.name,
                        'row_count': dataset.row_count,
                        'column_count': dataset.column_count,
                    }
                    for dataset in self.additional_datasets.all()
                ]
            },
            'analysis_stats': {
                'count': self.analysis_count,
                'last_analysis': self.last_analysis_at,
            },
            'timestamps': {
                'created': self.created_at,
                'updated': self.updated_at,
                'last_accessed': self.last_accessed,
            }
        }


class AnalysisResult(models.Model):
    """
    AnalysisResult model with caching for analytical results storage
    """
    # Basic Information
    name = models.CharField(
        max_length=255,
        help_text="Result name"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Result description"
    )
    
    # Analysis Information
    tool_used = models.ForeignKey(
        AnalysisTool,
        on_delete=models.CASCADE,
        related_name='results',
        help_text="Tool used to generate this result"
    )
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name='results',
        help_text="Session this result belongs to"
    )
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='analysis_results',
        help_text="Dataset analyzed"
    )
    
    # Result Data
    result_data = models.JSONField(
        default=dict,
        help_text="Main result data (tables, statistics, etc.)"
    )
    parameters_used = models.JSONField(
        default=dict,
        help_text="Parameters used for the analysis"
    )
    execution_time_ms = models.PositiveIntegerField(
        default=0,
        help_text="Execution time in milliseconds"
    )
    
    # Caching Information
    cache_key = models.CharField(
        max_length=255,
        unique=True,
        help_text="Cache key for this result"
    )
    cache_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the cache expires"
    )
    is_cached = models.BooleanField(
        default=True,
        help_text="Whether this result is cached"
    )
    
    # Output Information
    output_type = models.CharField(
        max_length=50,
        choices=[
            ('table', 'Data Table'),
            ('chart', 'Chart/Graph'),
            ('text', 'Text Report'),
            ('mixed', 'Mixed Content'),
        ],
        help_text="Type of output generated"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to generated file (if any)"
    )
    file_size_bytes = models.PositiveBigIntegerField(
        default=0,
        help_text="Size of generated file in bytes"
    )
    
    # Quality Information
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score for the result"
    )
    quality_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Quality score for the result"
    )
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analysis_results',
        help_text="User who owns this result"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_analysis_result'
        verbose_name = 'Analysis Result'
        verbose_name_plural = 'Analysis Results'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['tool_used']),
            models.Index(fields=['session']),
            models.Index(fields=['dataset']),
            models.Index(fields=['cache_key']),
            models.Index(fields=['cache_expires_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.tool_used.display_name})"
    
    @property
    def is_expired(self):
        """Check if the cached result has expired"""
        if not self.cache_expires_at:
            return False
        return timezone.now() > self.cache_expires_at
    
    def get_cache_summary(self):
        """Get cache status summary"""
        return {
            'is_cached': self.is_cached,
            'cache_key': self.cache_key,
            'expires_at': self.cache_expires_at,
            'is_expired': self.is_expired,
        }


class ChatMessage(models.Model):
    """
    ChatMessage model with LLM context for AI chat functionality
    """
    # Message Information
    content = models.TextField(
        help_text="Message content"
    )
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('user', 'User Message'),
            ('assistant', 'Assistant Response'),
            ('system', 'System Message'),
            ('tool', 'Tool Output'),
        ],
        help_text="Type of message"
    )
    
    # LLM Context
    llm_model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="LLM model used for this message"
    )
    token_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of tokens in this message"
    )
    context_messages = models.JSONField(
        default=list,
        help_text="Previous messages for context (last 10)"
    )
    
    # Analysis Context
    analysis_result = models.ForeignKey(
        AnalysisResult,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='chat_messages',
        help_text="Analysis result this message relates to"
    )
    
    # Message Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional message metadata"
    )
    attachments = models.JSONField(
        default=list,
        help_text="File attachments (images, tables, etc.)"
    )
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        help_text="User who sent this message"
    )
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        help_text="Session this message belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_chat_message'
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['message_type']),
            models.Index(fields=['llm_model']),
        ]
        ordering = ['session', 'created_at']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."


class AuditTrail(models.Model):
    """
    AuditTrail model with comprehensive logging for compliance and security
    """
    # Basic Information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='audit_trails',
        help_text="User who performed the action (nullable for system events)"
    )
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='audit_trails',
        help_text="Analysis session (optional)"
    )
    
    # Action Information
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('login', 'Login'),
            ('logout', 'Logout'),
            ('upload', 'File Upload'),
            ('analysis', 'Analysis Execution'),
            ('delete', 'Data Deletion'),
            ('export', 'Data Export'),
            ('admin_action', 'Admin Action'),
            ('system_event', 'System Event'),
        ],
        help_text="Type of action performed"
    )
    action_category = models.CharField(
        max_length=50,
        choices=[
            ('authentication', 'Authentication'),
            ('data_management', 'Data Management'),
            ('analysis', 'Analysis'),
            ('system', 'System'),
            ('security', 'Security'),
            ('compliance', 'Compliance'),
        ],
        help_text="Category of the action"
    )
    
    # Resource Information
    resource_type = models.CharField(
        max_length=50,
        choices=[
            ('user', 'User'),
            ('dataset', 'Dataset'),
            ('analysis_result', 'Analysis Result'),
            ('report', 'Report'),
            ('image', 'Image'),
            ('session', 'Session'),
            ('system', 'System'),
        ],
        help_text="Type of resource affected"
    )
    resource_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="ID of the affected resource"
    )
    resource_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Human-readable name of the resource"
    )
    action_description = models.TextField(
        help_text="Detailed description of the action performed"
    )
    
    # State Information
    before_snapshot = models.JSONField(
        default=dict,
        help_text="Resource state before action (masked for sensitive data)"
    )
    after_snapshot = models.JSONField(
        default=dict,
        help_text="Resource state after action (masked for sensitive data)"
    )
    
    # Request Information
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="User agent string from HTTP request"
    )
    correlation_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique correlation ID for tracking related events"
    )
    request_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Unique request identifier"
    )
    http_session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="HTTP session identifier"
    )
    
    # Execution Information
    success = models.BooleanField(
        default=True,
        help_text="Whether the action was successful"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if action failed"
    )
    execution_time_ms = models.PositiveIntegerField(
        default=0,
        help_text="Time taken to perform the action in milliseconds"
    )
    
    # Data Information
    data_changed = models.BooleanField(
        default=False,
        help_text="Whether any data was modified"
    )
    sensitive_data_accessed = models.BooleanField(
        default=False,
        help_text="Whether sensitive data was accessed"
    )
    compliance_flags = models.JSONField(
        default=list,
        help_text="Array of compliance flags (gdpr, hipaa, sox, pci_dss)"
    )
    
    # Retention Information
    retention_status = models.CharField(
        max_length=20,
        default='active',
        choices=[
            ('active', 'Active'),
            ('archived', 'Archived'),
            ('purged', 'Purged'),
        ],
        help_text="Retention status of the audit record"
    )
    retention_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the audit record expires"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(
        max_length=100,
        default='system',
        help_text="Who created the record (user_id or 'system')"
    )
    
    class Meta:
        db_table = 'analytics_audit_trail'
        verbose_name = 'Audit Trail'
        verbose_name_plural = 'Audit Trails'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type']),
            models.Index(fields=['action_category']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['correlation_id']),
            models.Index(fields=['success']),
            models.Index(fields=['retention_status']),
            models.Index(fields=['retention_expires_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action_type} - {self.resource_name} ({self.created_at})"
    
    @property
    def is_expired(self):
        """Check if the audit record has expired"""
        if not self.retention_expires_at:
            return False
        return timezone.now() > self.retention_expires_at
    
    def get_summary(self):
        """Get audit trail summary"""
        return {
            'action': {
                'type': self.action_type,
                'category': self.action_category,
                'description': self.action_description,
            },
            'resource': {
                'type': self.resource_type,
                'id': self.resource_id,
                'name': self.resource_name,
            },
            'execution': {
                'success': self.success,
                'execution_time_ms': self.execution_time_ms,
                'error_message': self.error_message,
            },
            'data': {
                'changed': self.data_changed,
                'sensitive_accessed': self.sensitive_data_accessed,
                'compliance_flags': self.compliance_flags,
            },
            'retention': {
                'status': self.retention_status,
                'expires_at': self.retention_expires_at,
                'is_expired': self.is_expired,
            },
            'context': {
                'user_id': self.user.id if self.user else None,
                'session_id': self.session.id if self.session else None,
                'correlation_id': self.correlation_id,
                'ip_address': self.ip_address,
            }
        }


class AgentRun(models.Model):
    """
    AgentRun model for autonomous AI analysis sessions
    """
    # Basic Information
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='agent_runs',
        help_text="User who initiated the agent run"
    )
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='agent_runs',
        help_text="Dataset being analyzed"
    )
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='agent_runs',
        help_text="Analysis session (optional)"
    )
    
    # Agent Configuration
    goal = models.TextField(
        help_text="User-defined analysis goal or question"
    )
    plan_json = models.JSONField(
        default=dict,
        help_text="JSON object containing the agent's analysis plan"
    )
    
    # Execution Status
    status = models.CharField(
        max_length=20,
        default='planning',
        choices=[
            ('planning', 'Planning'),
            ('running', 'Running'),
            ('paused', 'Paused'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        help_text="Current status of the agent run"
    )
    current_step = models.PositiveIntegerField(
        default=0,
        help_text="Current step number in the plan"
    )
    total_steps = models.PositiveIntegerField(
        default=0,
        help_text="Total number of steps planned"
    )
    
    # Resource Constraints
    max_steps = models.PositiveIntegerField(
        default=20,
        help_text="Maximum steps allowed (resource constraint)"
    )
    max_cost = models.PositiveIntegerField(
        default=10000,
        help_text="Maximum cost allowed in tokens (resource constraint)"
    )
    max_time = models.PositiveIntegerField(
        default=1800,
        help_text="Maximum time allowed in seconds (resource constraint)"
    )
    
    # Resource Usage
    total_cost = models.PositiveIntegerField(
        default=0,
        help_text="Total cost incurred so far in tokens"
    )
    total_time = models.PositiveIntegerField(
        default=0,
        help_text="Total time elapsed in seconds"
    )
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progress percentage (0-100)"
    )
    
    # Agent Information
    agent_version = models.CharField(
        max_length=20,
        default='1.0',
        help_text="Version of the agent system used"
    )
    llm_model = models.CharField(
        max_length=100,
        default='gemini-1.5-flash',
        help_text="LLM model used for planning and execution"
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the agent run started"
    )
    finished_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the agent run completed"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if run failed"
    )
    
    # Tracking
    correlation_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique correlation ID for tracking"
    )
    parent_run = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='sub_runs',
        help_text="Parent agent run (for sub-runs)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_agent_run'
        verbose_name = 'Agent Run'
        verbose_name_plural = 'Agent Runs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['dataset']),
            models.Index(fields=['status']),
            models.Index(fields=['correlation_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Agent Run {self.id} - {self.goal[:50]}..."


class AgentStep(models.Model):
    """
    AgentStep model for individual agent actions
    """
    # Basic Information
    agent_run = models.ForeignKey(
        AgentRun,
        on_delete=models.CASCADE,
        related_name='steps',
        help_text="Agent run this step belongs to"
    )
    step_number = models.PositiveIntegerField(
        help_text="Step number in the agent run"
    )
    
    # Step Information
    thought = models.TextField(
        help_text="Agent's thought process for this step"
    )
    tool_name = models.CharField(
        max_length=100,
        help_text="Name of the tool used in this step"
    )
    parameters_json = models.JSONField(
        default=dict,
        help_text="Parameters passed to the tool"
    )
    observation_json = models.JSONField(
        default=dict,
        help_text="Observation/result from tool execution"
    )
    
    # Execution Status
    status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('skipped', 'Skipped'),
        ],
        help_text="Status of this step"
    )
    
    # Resource Usage
    token_usage = models.PositiveIntegerField(
        default=0,
        help_text="Token usage for this step"
    )
    execution_time_ms = models.PositiveIntegerField(
        default=0,
        help_text="Execution time in milliseconds"
    )
    memory_used_mb = models.FloatField(
        default=0.0,
        help_text="Memory used in MB"
    )
    
    # Quality Metrics
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score for this step (0.0 to 1.0)"
    )
    reasoning = models.TextField(
        blank=True,
        null=True,
        help_text="Reasoning behind this step"
    )
    next_action = models.TextField(
        blank=True,
        null=True,
        help_text="Planned next action"
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this step started"
    )
    finished_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this step completed"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if step failed"
    )
    
    # Retry Information
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retries for this step"
    )
    max_retries = models.PositiveIntegerField(
        default=3,
        help_text="Maximum retries allowed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_agent_step'
        verbose_name = 'Agent Step'
        verbose_name_plural = 'Agent Steps'
        unique_together = ['agent_run', 'step_number']
        indexes = [
            models.Index(fields=['agent_run', 'step_number']),
            models.Index(fields=['status']),
            models.Index(fields=['tool_name']),
        ]
        ordering = ['agent_run', 'step_number']
    
    def __str__(self):
        return f"Step {self.step_number} - {self.tool_name}"


class GeneratedImage(models.Model):
    """
    GeneratedImage model for visualization storage
    """
    # Basic Information
    name = models.CharField(
        max_length=255,
        help_text="Image name"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Image description"
    )
    
    # File Information
    file_path = models.CharField(
        max_length=500,
        help_text="Path to the image file"
    )
    file_size_bytes = models.PositiveBigIntegerField(
        help_text="Size of the image file in bytes"
    )
    image_format = models.CharField(
        max_length=10,
        choices=[
            ('png', 'PNG'),
            ('jpg', 'JPEG'),
            ('svg', 'SVG'),
            ('pdf', 'PDF'),
        ],
        help_text="Image format"
    )
    
    # Image Properties
    width = models.PositiveIntegerField(
        help_text="Image width in pixels"
    )
    height = models.PositiveIntegerField(
        help_text="Image height in pixels"
    )
    dpi = models.PositiveIntegerField(
        default=300,
        help_text="Image DPI"
    )
    
    # Generation Information
    tool_used = models.CharField(
        max_length=100,
        help_text="Tool used to generate the image"
    )
    parameters_used = models.JSONField(
        default=dict,
        help_text="Parameters used for generation"
    )
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='generated_images',
        help_text="User who owns this image"
    )
    analysis_result = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,
        related_name='generated_images',
        help_text="Analysis result this image belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_generated_image'
        verbose_name = 'Generated Image'
        verbose_name_plural = 'Generated Images'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['analysis_result']),
            models.Index(fields=['tool_used']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.image_format})"


class SandboxExecution(models.Model):
    """
    SandboxExecution model for secure code execution
    """
    # Basic Information
    code = models.TextField(
        help_text="Code to be executed"
    )
    language = models.CharField(
        max_length=20,
        default='python',
        choices=[
            ('python', 'Python'),
            ('r', 'R'),
            ('sql', 'SQL'),
        ],
        help_text="Programming language"
    )
    
    # Execution Information
    status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('timeout', 'Timeout'),
        ],
        help_text="Execution status"
    )
    output = models.TextField(
        blank=True,
        null=True,
        help_text="Execution output"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if execution failed"
    )
    
    # Resource Usage
    execution_time_ms = models.PositiveIntegerField(
        default=0,
        help_text="Execution time in milliseconds"
    )
    memory_used_mb = models.FloatField(
        default=0.0,
        help_text="Memory used in MB"
    )
    cpu_usage_percent = models.FloatField(
        default=0.0,
        help_text="CPU usage percentage"
    )
    
    # Security
    security_scan_passed = models.BooleanField(
        default=False,
        help_text="Whether security scan passed"
    )
    security_warnings = models.JSONField(
        default=list,
        help_text="Security warnings"
    )
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sandbox_executions',
        help_text="User who initiated the execution"
    )
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name='sandbox_executions',
        help_text="Session this execution belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When execution started"
    )
    finished_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When execution finished"
    )
    
    class Meta:
        db_table = 'analytics_sandbox_execution'
        verbose_name = 'Sandbox Execution'
        verbose_name_plural = 'Sandbox Executions'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session']),
            models.Index(fields=['status']),
            models.Index(fields=['language']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sandbox Execution {self.id} - {self.language}"


class ReportGeneration(models.Model):
    """
    ReportGeneration model for document export
    """
    # Basic Information
    name = models.CharField(
        max_length=255,
        help_text="Report name"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Report description"
    )
    
    # Report Configuration
    template_type = models.CharField(
        max_length=50,
        choices=[
            ('standard', 'Standard Report'),
            ('executive', 'Executive Summary'),
            ('technical', 'Technical Report'),
            ('custom', 'Custom Report'),
        ],
        help_text="Report template type"
    )
    content_sections = models.JSONField(
        default=list,
        help_text="Sections to include in the report"
    )
    custom_settings = models.JSONField(
        default=dict,
        help_text="Custom report settings"
    )
    
    # Generation Status
    status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('generating', 'Generating'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        help_text="Generation status"
    )
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Generation progress percentage"
    )
    
    # File Information
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to the generated report file"
    )
    file_size_bytes = models.PositiveBigIntegerField(
        default=0,
        help_text="Size of the report file in bytes"
    )
    file_format = models.CharField(
        max_length=10,
        default='docx',
        choices=[
            ('docx', 'Word Document'),
            ('pdf', 'PDF'),
            ('html', 'HTML'),
        ],
        help_text="Report file format"
    )
    
    # Generation Information
    generation_time_ms = models.PositiveIntegerField(
        default=0,
        help_text="Generation time in milliseconds"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if generation failed"
    )
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='report_generations',
        help_text="User who requested the report"
    )
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name='report_generations',
        help_text="Session this report belongs to"
    )
    analysis_results = models.ManyToManyField(
        AnalysisResult,
        blank=True,
        related_name='report_generations',
        help_text="Analysis results included in the report"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When generation started"
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When generation completed"
    )
    
    class Meta:
        db_table = 'analytics_report_generation'
        verbose_name = 'Report Generation'
        verbose_name_plural = 'Report Generations'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session']),
            models.Index(fields=['status']),
            models.Index(fields=['template_type']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
