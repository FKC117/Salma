"""
Backup Manager Service for Database Backup Procedures

This service handles automated database backup scheduling, monitoring, and management.
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.core.management import call_command

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Service for managing database backup procedures
    """
    
    def __init__(self):
        self.backup_dir = Path(getattr(settings, 'BACKUP_DIR', 'backups'))
        self.retention_days = getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
        self.compression_enabled = getattr(settings, 'BACKUP_COMPRESSION', True)
        self.backup_format = getattr(settings, 'BACKUP_FORMAT', 'custom')
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, backup_type: str = 'scheduled') -> Dict:
        """
        Create a new database backup
        
        Args:
            backup_type: Type of backup ('scheduled', 'manual', 'emergency')
            
        Returns:
            Dict with backup information
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            db_name = settings.DATABASES['default']['NAME']
            
            # Generate backup filename
            if self.backup_format == 'sql':
                backup_file = self.backup_dir / f"{db_name}_{backup_type}_{timestamp}.sql"
            elif self.backup_format == 'custom':
                backup_file = self.backup_dir / f"{db_name}_{backup_type}_{timestamp}.dump"
            else:  # directory
                backup_file = self.backup_dir / f"{db_name}_{backup_type}_{timestamp}"
            
            # Execute backup command
            call_command(
                'backup_database',
                backup_dir=str(self.backup_dir),
                compress=self.compression_enabled,
                retention_days=self.retention_days,
                format=self.backup_format
            )
            
            # Get backup file info
            backup_info = {
                'backup_file': str(backup_file),
                'backup_type': backup_type,
                'timestamp': timestamp,
                'size_bytes': backup_file.stat().st_size if backup_file.exists() else 0,
                'format': self.backup_format,
                'compressed': self.compression_enabled,
                'status': 'success'
            }
            
            # Log backup creation
            self._log_backup_creation(backup_info)
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return {
                'backup_type': backup_type,
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'status': 'failed',
                'error': str(e)
            }
    
    def list_backups(self, limit: int = 50) -> List[Dict]:
        """
        List available backups
        
        Args:
            limit: Maximum number of backups to return
            
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            for backup_file in self.backup_dir.iterdir():
                if backup_file.is_file() and self._is_backup_file(backup_file):
                    backup_info = self._get_backup_info(backup_file)
                    if backup_info:
                        backups.append(backup_info)
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return backups[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    def get_backup_status(self) -> Dict:
        """
        Get backup system status
        
        Returns:
            Dict with backup system status information
        """
        try:
            backups = self.list_backups()
            
            # Calculate statistics
            total_backups = len(backups)
            total_size = sum(b['size_bytes'] for b in backups)
            
            # Check for recent backups (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_backups = [
                b for b in backups 
                if datetime.strptime(b['timestamp'], '%Y%m%d_%H%M%S') > recent_cutoff
            ]
            
            # Check backup directory health
            backup_dir_exists = self.backup_dir.exists()
            backup_dir_writable = os.access(self.backup_dir, os.W_OK)
            
            return {
                'status': 'healthy' if recent_backups else 'warning',
                'total_backups': total_backups,
                'recent_backups': len(recent_backups),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'backup_dir_exists': backup_dir_exists,
                'backup_dir_writable': backup_dir_writable,
                'retention_days': self.retention_days,
                'compression_enabled': self.compression_enabled,
                'backup_format': self.backup_format,
                'last_backup': backups[0]['timestamp'] if backups else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def cleanup_old_backups(self) -> Dict:
        """
        Clean up old backups based on retention policy
        
        Returns:
            Dict with cleanup results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            removed_size = 0
            
            for backup_file in self.backup_dir.iterdir():
                if backup_file.is_file() and self._is_backup_file(backup_file):
                    try:
                        # Extract timestamp from filename
                        timestamp_str = self._extract_timestamp_from_filename(backup_file.name)
                        if timestamp_str:
                            file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                            
                            if file_date < cutoff_date:
                                file_size = backup_file.stat().st_size
                                backup_file.unlink()
                                removed_count += 1
                                removed_size += file_size
                    except (ValueError, IndexError):
                        continue
            
            return {
                'removed_count': removed_count,
                'removed_size_bytes': removed_size,
                'removed_size_mb': round(removed_size / (1024 * 1024), 2),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def restore_backup(self, backup_file: str, force: bool = False) -> Dict:
        """
        Restore database from backup
        
        Args:
            backup_file: Path to backup file
            force: Force restore without confirmation
            
        Returns:
            Dict with restore results
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                return {
                    'status': 'failed',
                    'error': f'Backup file not found: {backup_file}'
                }
            
            # Execute restore command
            call_command(
                'restore_database',
                backup_file,
                force=force,
                clean=True,
                create_db=True
            )
            
            return {
                'status': 'success',
                'backup_file': backup_file,
                'restore_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Backup restore failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _is_backup_file(self, file_path: Path) -> bool:
        """Check if file is a backup file"""
        return (
            file_path.suffix in ['.sql', '.dump'] or
            file_path.is_dir() or
            '_backup_' in file_path.name
        )
    
    def _get_backup_info(self, backup_file: Path) -> Optional[Dict]:
        """Extract backup information from file"""
        try:
            timestamp_str = self._extract_timestamp_from_filename(backup_file.name)
            if not timestamp_str:
                return None
            
            file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            
            return {
                'filename': backup_file.name,
                'file_path': str(backup_file),
                'timestamp': timestamp_str,
                'created_at': file_date.isoformat(),
                'size_bytes': backup_file.stat().st_size,
                'size_mb': round(backup_file.stat().st_size / (1024 * 1024), 2),
                'format': backup_file.suffix[1:] if backup_file.suffix else 'directory',
                'is_directory': backup_file.is_dir(),
            }
            
        except Exception as e:
            logger.warning(f"Failed to get backup info for {backup_file}: {str(e)}")
            return None
    
    def _extract_timestamp_from_filename(self, filename: str) -> Optional[str]:
        """Extract timestamp from backup filename"""
        try:
            # Handle different filename formats
            if '_backup_' in filename:
                return filename.split('_backup_')[1].split('.')[0]
            elif '_' in filename and len(filename.split('_')) >= 3:
                parts = filename.split('_')
                if len(parts) >= 3:
                    return f"{parts[-2]}_{parts[-1].split('.')[0]}"
            return None
        except (ValueError, IndexError):
            return None
    
    def _log_backup_creation(self, backup_info: Dict):
        """Log backup creation to audit trail"""
        try:
            from analytics.services.audit_trail_manager import AuditTrailManager
            
            audit_manager = AuditTrailManager()
            audit_manager.log_action(
                user_id=None,  # System action
                action_type='system_event',
                action_category='system',
                resource_type='system',
                resource_id=None,
                resource_name='database_backup',
                action_description=f'Database backup created: {backup_info["backup_file"]}',
                success=True,
                additional_details=backup_info
            )
        except Exception as e:
            logger.warning(f"Failed to log backup creation: {str(e)}")
