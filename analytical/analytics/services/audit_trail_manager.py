"""
Audit Trail Manager for Comprehensive Logging

This service handles comprehensive audit trail logging for compliance and security.
It provides methods for logging user actions, system events, and data access.
"""

import uuid
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from analytics.models import AuditTrail

logger = logging.getLogger(__name__)
User = get_user_model()


class AuditTrailManager:
    """
    Service for comprehensive audit trail management
    """
    
    def __init__(self):
        self.retention_days = getattr(settings, 'AUDIT_RETENTION_DAYS', 365)
        self.mask_sensitive_data = getattr(settings, 'AUDIT_MASK_SENSITIVE_DATA', True)
        self.sensitive_fields = [
            'password', 'token', 'key', 'secret', 'ssn', 'credit_card',
            'phone', 'email', 'address', 'ip_address'
        ]
    
    def log_action(self, user_id: Optional[int], action_type: str, action_category: str,
                   resource_type: str, resource_id: Optional[int] = None,
                   resource_name: Optional[str] = None, action_description: Optional[str] = None,
                   before_snapshot: Optional[Dict] = None, after_snapshot: Optional[Dict] = None,
                   request: Optional[Any] = None, success: bool = True,
                   error_message: Optional[str] = None, execution_time_ms: Optional[int] = None,
                   data_changed: bool = False, sensitive_data_accessed: bool = False,
                   compliance_flags: Optional[List[str]] = None,
                   additional_details: Optional[Dict] = None,
                   correlation_id: Optional[str] = None) -> AuditTrail:
        """
        Log a comprehensive audit trail entry
        
        Args:
            user_id: ID of the user performing the action (None for system events)
            action_type: Type of action (login, logout, upload, analysis, delete, export, admin_action, system_event)
            action_category: Category (authentication, data_management, analysis, system, security, compliance)
            resource_type: Type of resource affected (user, dataset, analysis_result, report, image, session, system)
            resource_id: ID of the affected resource
            resource_name: Human-readable name of the resource
            action_description: Detailed description of the action performed
            before_snapshot: JSON snapshot of resource state before action (masked for sensitive data)
            after_snapshot: JSON snapshot of resource state after action (masked for sensitive data)
            request: Django request object (for extracting IP, user agent, etc.)
            success: Whether the action was successful
            error_message: Error message if action failed
            execution_time_ms: Time taken to perform the action in milliseconds
            data_changed: Whether any data was modified
            sensitive_data_accessed: Whether sensitive data was accessed
            compliance_flags: Array of compliance flags (gdpr, hipaa, sox, pci_dss)
            additional_details: Additional details to log
            correlation_id: Unique correlation ID for tracking related events
            
        Returns:
            AuditTrail object
        """
        try:
            # Generate correlation ID if not provided
            if not correlation_id:
                correlation_id = str(uuid.uuid4())
            
            # Extract request information
            ip_address = None
            user_agent = None
            request_id = None
            http_session_id = None
            
            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                request_id = getattr(request, 'correlation_id', None)
                http_session_id = request.session.session_key
            
            # Mask sensitive data in snapshots
            if before_snapshot and self.mask_sensitive_data:
                before_snapshot = self._mask_sensitive_data(before_snapshot)
            
            if after_snapshot and self.mask_sensitive_data:
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
                    action_description=action_description,
                    before_snapshot=before_snapshot,
                    after_snapshot=after_snapshot,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    correlation_id=correlation_id,
                    request_id=request_id,
                    http_session_id=http_session_id,
                    success=success,
                    error_message=error_message,
                    execution_time_ms=execution_time_ms,
                    data_changed=data_changed,
                    sensitive_data_accessed=sensitive_data_accessed,
                    compliance_flags=compliance_flags or [],
                    retention_status='active',
                    retention_expires_at=timezone.now() + timedelta(days=self.retention_days),
                    created_by='system' if user_id is None else str(user_id)
                )
                
                # Add additional details as separate records
                if additional_details:
                    self._add_audit_details(audit_entry, additional_details)
                
                logger.info(f"Audit trail logged: {action_type} - {action_description}")
                
                return audit_entry
                
        except Exception as e:
            logger.error(f"Failed to log audit trail: {str(e)}", exc_info=True)
            # Return a minimal audit entry to prevent system failure
            return self._create_minimal_audit_entry(
                user_id, action_type, action_category, resource_type, str(e)
            )
    
    def log_user_action(self, user_id: int, action_type: str, resource_type: str,
                       resource_id: Optional[int] = None, resource_name: Optional[str] = None,
                       action_description: Optional[str] = None, request: Optional[Any] = None,
                       **kwargs) -> AuditTrail:
        """Log a user action with standard parameters"""
        return self.log_action(
            user_id=user_id,
            action_type=action_type,
            action_category='user_action',
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            action_description=action_description,
            request=request,
            **kwargs
        )
    
    def log_system_event(self, event_type: str, event_description: str,
                        resource_type: str = 'system', resource_id: Optional[int] = None,
                        **kwargs) -> AuditTrail:
        """Log a system event"""
        return self.log_action(
            user_id=None,
            action_type='system_event',
            action_category='system',
            resource_type=resource_type,
            resource_id=resource_id,
            action_description=event_description,
            **kwargs
        )
    
    def log_data_access(self, user_id: int, resource_type: str, resource_id: int,
                       resource_name: str, access_type: str, request: Optional[Any] = None,
                       **kwargs) -> AuditTrail:
        """Log data access event"""
        return self.log_action(
            user_id=user_id,
            action_type='data_access',
            action_category='data_management',
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            action_description=f"{access_type} access to {resource_type}",
            request=request,
            sensitive_data_accessed=True,
            **kwargs
        )
    
    def log_security_event(self, user_id: Optional[int], event_type: str,
                          event_description: str, severity: str = 'medium',
                          request: Optional[Any] = None, **kwargs) -> AuditTrail:
        """Log a security event"""
        return self.log_action(
            user_id=user_id,
            action_type='security_event',
            action_category='security',
            resource_type='security',
            action_description=f"[{severity.upper()}] {event_description}",
            request=request,
            compliance_flags=['security'],
            **kwargs
        )
    
    def get_audit_trail(self, user_id: Optional[int] = None, action_type: Optional[str] = None,
                       resource_type: Optional[str] = None, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None, limit: int = 100) -> List[AuditTrail]:
        """Retrieve audit trail records with filtering"""
        queryset = AuditTrail.objects.all()
        
        if user_id is not None:
            queryset = queryset.filter(user_id=user_id)
        
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset.order_by('-created_at')[:limit]
    
    def export_audit_data(self, start_date: datetime, end_date: datetime,
                         format: str = 'json') -> str:
        """Export audit data for compliance reporting"""
        try:
            audit_records = self.get_audit_trail(
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )
            
            if format == 'json':
                return self._export_to_json(audit_records)
            elif format == 'csv':
                return self._export_to_csv(audit_records)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export audit data: {str(e)}")
            raise
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime,
                                 compliance_standard: str = 'gdpr') -> Dict[str, Any]:
        """Generate compliance report for specified standard"""
        try:
            audit_records = self.get_audit_trail(
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )
            
            report = {
                'standard': compliance_standard,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_events': len(audit_records),
                'summary': self._generate_compliance_summary(audit_records, compliance_standard),
                'events': self._format_events_for_compliance(audit_records)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {str(e)}")
            raise
    
    def cleanup_expired_records(self) -> int:
        """Clean up expired audit records"""
        try:
            expired_records = AuditTrail.objects.filter(
                retention_expires_at__lt=timezone.now(),
                retention_status='active'
            )
            
            count = expired_records.count()
            expired_records.update(retention_status='purged')
            
            logger.info(f"Cleaned up {count} expired audit records")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired audit records: {str(e)}")
            return 0
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Mask sensitive data in the given data structure"""
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(sensitive_field in key.lower() for sensitive_field in self.sensitive_fields):
                    masked_data[key] = "***MASKED***"
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data
    
    def _add_audit_details(self, audit_entry: AuditTrail, details: Dict[str, Any]) -> None:
        """Add additional details to the audit trail's after_snapshot field"""
        # Store additional details in the after_snapshot field
        current_snapshot = audit_entry.after_snapshot or {}
        current_snapshot['additional_details'] = details
        audit_entry.after_snapshot = current_snapshot
        audit_entry.save(update_fields=['after_snapshot'])
    
    def _create_minimal_audit_entry(self, user_id: Optional[int], action_type: str,
                                   action_category: str, resource_type: str,
                                   error_message: str) -> AuditTrail:
        """Create a minimal audit entry when logging fails"""
        try:
            return AuditTrail.objects.create(
                user_id=user_id,
                action_type=action_type,
                action_category=action_category,
                resource_type=resource_type,
                action_description=f"Audit logging failed: {error_message}",
                success=False,
                error_message=error_message,
                retention_status='active',
                retention_expires_at=timezone.now() + timedelta(days=self.retention_days),
                created_by='system'
            )
        except Exception:
            # If even minimal logging fails, return None
            return None
    
    def _export_to_json(self, audit_records: List[AuditTrail]) -> str:
        """Export audit records to JSON format"""
        data = []
        for record in audit_records:
            data.append({
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
            })
        
        return json.dumps(data, indent=2)
    
    def _export_to_csv(self, audit_records: List[AuditTrail]) -> str:
        """Export audit records to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'User ID', 'Action Type', 'Action Category', 'Resource Type',
            'Resource ID', 'Resource Name', 'Action Description', 'IP Address',
            'User Agent', 'Correlation ID', 'Success', 'Error Message',
            'Execution Time (ms)', 'Data Changed', 'Sensitive Data Accessed',
            'Compliance Flags', 'Created At'
        ])
        
        # Write data
        for record in audit_records:
            writer.writerow([
                record.id, record.user_id, record.action_type, record.action_category,
                record.resource_type, record.resource_id, record.resource_name,
                record.action_description, record.ip_address, record.user_agent,
                record.correlation_id, record.success, record.error_message,
                record.execution_time_ms, record.data_changed, record.sensitive_data_accessed,
                ','.join(record.compliance_flags) if record.compliance_flags else '',
                record.created_at.isoformat()
            ])
        
        return output.getvalue()
    
    def _generate_compliance_summary(self, audit_records: List[AuditTrail], 
                                   compliance_standard: str) -> Dict[str, Any]:
        """Generate compliance summary for audit records"""
        summary = {
            'total_events': len(audit_records),
            'successful_events': sum(1 for r in audit_records if r.success),
            'failed_events': sum(1 for r in audit_records if not r.success),
            'data_access_events': sum(1 for r in audit_records if r.sensitive_data_accessed),
            'data_modification_events': sum(1 for r in audit_records if r.data_changed),
            'unique_users': len(set(r.user_id for r in audit_records if r.user_id)),
            'action_types': {}
        }
        
        # Count action types
        for record in audit_records:
            action_type = record.action_type
            summary['action_types'][action_type] = summary['action_types'].get(action_type, 0) + 1
        
        return summary
    
    def _format_events_for_compliance(self, audit_records: List[AuditTrail]) -> List[Dict[str, Any]]:
        """Format events for compliance reporting"""
        events = []
        for record in audit_records:
            events.append({
                'timestamp': record.created_at.isoformat(),
                'user_id': record.user_id,
                'action': record.action_type,
                'resource': f"{record.resource_type}:{record.resource_id or 'N/A'}",
                'description': record.action_description,
                'success': record.success,
                'data_accessed': record.sensitive_data_accessed,
                'data_changed': record.data_changed,
                'ip_address': record.ip_address,
                'correlation_id': record.correlation_id
            })
        
        return events
