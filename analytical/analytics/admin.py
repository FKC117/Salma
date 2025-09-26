from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, Dataset, DatasetColumn, AnalysisTool, AnalysisSession, 
    AnalysisResult, ChatMessage, AuditTrail, AgentRun, AgentStep,
    GeneratedImage, SandboxExecution, ReportGeneration, VectorNote
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'last_login']
    fieldsets = (
        ('Authentication', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Token Limits', {
            'fields': ('token_limit_per_month', 'token_usage_current_month', 'storage_limit_gb')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login')
        })
    )


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'row_count', 'column_count', 'file_size_mb', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'description', 'original_filename']
    readonly_fields = ['created_at', 'updated_at', 'file_hash', 'parquet_path']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'user')
        }),
        ('File Info', {
            'fields': ('original_filename', 'file_size_bytes', 'file_hash', 'parquet_path')
        }),
        ('Data Info', {
            'fields': ('row_count', 'column_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(DatasetColumn)
class DatasetColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'dataset', 'detected_type', 'confirmed_type', 'null_count', 'unique_count']
    list_filter = ['detected_type', 'confirmed_type', 'dataset']
    search_fields = ['name', 'dataset__name']
    readonly_fields = ['detected_type', 'null_count', 'unique_count']


@admin.register(AnalysisTool)
class AnalysisToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'display_name', 'description', 'category')
        }),
        ('Configuration', {
            'fields': ('required_column_types', 'parameters_schema', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'primary_dataset', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['user__username', 'primary_dataset__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'tool_used', 'user', 'session', 'output_type', 'execution_time_ms', 'created_at']
    list_filter = ['output_type', 'created_at', 'tool_used']
    search_fields = ['tool_used__name', 'user__username']
    readonly_fields = ['created_at', 'execution_time_ms']
    fieldsets = (
        ('Basic Info', {
            'fields': ('tool_used', 'user', 'session')
        }),
        ('Execution', {
            'fields': ('parameters_json', 'result_data', 'output_type', 'execution_time_ms')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'message_type', 'session', 'token_count', 'created_at']
    list_filter = ['message_type', 'created_at', 'user']
    search_fields = ['user__username', 'content']
    readonly_fields = ['created_at', 'token_count']
    fieldsets = (
        ('Message Info', {
            'fields': ('user', 'session', 'message_type', 'content')
        }),
        ('Metadata', {
            'fields': ('token_count', 'created_at')
        })
    )


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'action_type', 'action_category', 'resource_type', 'success', 'created_at']
    list_filter = ['action_type', 'action_category', 'success', 'created_at', 'user']
    search_fields = ['user__username', 'action_description', 'resource_name']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Action Info', {
            'fields': ('user', 'action_type', 'action_category', 'action_description')
        }),
        ('Resource Info', {
            'fields': ('resource_type', 'resource_id', 'resource_name')
        }),
        ('Execution Info', {
            'fields': ('success', 'error_message', 'execution_time_ms', 'correlation_id')
        }),
        ('Metadata', {
            'fields': ('metadata_json', 'data_changed', 'created_at')
        })
    )


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'goal', 'status', 'progress_percentage', 'created_at']
    list_filter = ['status', 'created_at', 'user']
    search_fields = ['user__username', 'goal']
    readonly_fields = ['created_at', 'started_at', 'finished_at', 'progress_percentage']
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'session', 'goal', 'status')
        }),
        ('Configuration', {
            'fields': ('agent_config_json', 'constraints_json')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'current_step', 'total_steps')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'finished_at')
        }),
        ('Results', {
            'fields': ('final_result_json', 'error_message')
        })
    )


@admin.register(AgentStep)
class AgentStepAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent_run', 'step_number', 'tool_name', 'status', 'confidence_score', 'started_at']
    list_filter = ['status', 'tool_name', 'started_at']
    search_fields = ['agent_run__goal', 'tool_name', 'thought']
    readonly_fields = ['started_at', 'finished_at', 'execution_time_ms']
    fieldsets = (
        ('Step Info', {
            'fields': ('agent_run', 'step_number', 'tool_name', 'thought')
        }),
        ('Execution', {
            'fields': ('parameters_json', 'observation_json', 'status', 'confidence_score')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'finished_at', 'execution_time_ms')
        })
    )


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'image_format', 'file_size_kb', 'created_at']
    list_filter = ['image_format', 'created_at', 'user']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'file_size_bytes']
    
    def file_size_kb(self, obj):
        return f"{obj.file_size_bytes / 1024:.1f} KB"
    file_size_kb.short_description = 'File Size'


@admin.register(SandboxExecution)
class SandboxExecutionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'language', 'status', 'execution_time_ms', 'created_at']
    list_filter = ['status', 'language', 'created_at', 'user']
    search_fields = ['user__username', 'code']
    readonly_fields = ['created_at', 'started_at', 'finished_at', 'execution_time_ms']
    fieldsets = (
        ('Execution Info', {
            'fields': ('user', 'session', 'language', 'code', 'status')
        }),
        ('Results', {
            'fields': ('output', 'error_message')
        }),
        ('Performance', {
            'fields': ('execution_time_ms', 'memory_used_mb', 'cpu_usage_percent')
        }),
        ('Security', {
            'fields': ('security_scan_passed', 'security_warnings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'finished_at')
        })
    )


@admin.register(ReportGeneration)
class ReportGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'template_type', 'status', 'created_at']
    list_filter = ['template_type', 'status', 'created_at', 'user']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'completed_at']
    fieldsets = (
        ('Report Info', {
            'fields': ('name', 'user', 'session', 'template_type', 'status')
        }),
        ('Content', {
            'fields': ('content_sections', 'custom_settings')
        }),
        ('Output', {
            'fields': ('file_path', 'file_size_bytes', 'file_format')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at')
        })
    )


@admin.register(VectorNote)
class VectorNoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'scope', 'content_type', 'confidence_score', 'usage_count', 'created_at']
    list_filter = ['scope', 'content_type', 'created_at', 'user']
    search_fields = ['title', 'text', 'user__username']
    readonly_fields = ['created_at', 'last_accessed', 'usage_count']
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'text', 'user', 'dataset')
        }),
        ('Scope & Type', {
            'fields': ('scope', 'content_type', 'confidence_score')
        }),
        ('Embedding Info', {
            'fields': ('embedding_model', 'embedding_dimension')
        }),
        ('Usage Stats', {
            'fields': ('usage_count', 'last_accessed')
        }),
        ('Metadata', {
            'fields': ('metadata_json', 'created_at')
        })
    )
    
    def get_queryset(self, request):
        """Optimize queries for admin interface"""
        return super().get_queryset(request).select_related('user', 'dataset')


# Customize admin site header and title
admin.site.site_header = "Analytical System Administration"
admin.site.site_title = "Analytical Admin"
admin.site.index_title = "Welcome to Analytical System Administration"
