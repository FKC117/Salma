"""
Django management command for database backup procedures
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backup PostgreSQL database with compression and rotation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='backups',
            help='Directory to store backup files (default: backups)'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress backup files using gzip'
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            default=30,
            help='Number of days to retain backups (default: 30)'
        )
        parser.add_argument(
            '--format',
            choices=['sql', 'custom', 'directory'],
            default='custom',
            help='Backup format (default: custom)'
        )

    def handle(self, *args, **options):
        """Execute database backup"""
        try:
            self.stdout.write(
                self.style.SUCCESS('🔄 Starting database backup procedure...')
            )
            
            # Get database configuration
            db_config = settings.DATABASES['default']
            
            # Create backup directory
            backup_dir = Path(options['backup_dir'])
            backup_dir.mkdir(exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            db_name = db_config['NAME']
            
            if options['format'] == 'sql':
                backup_file = backup_dir / f"{db_name}_backup_{timestamp}.sql"
                self._create_sql_backup(db_config, backup_file, options['compress'])
            elif options['format'] == 'custom':
                backup_file = backup_dir / f"{db_name}_backup_{timestamp}.dump"
                self._create_custom_backup(db_config, backup_file, options['compress'])
            elif options['format'] == 'directory':
                backup_file = backup_dir / f"{db_name}_backup_{timestamp}"
                self._create_directory_backup(db_config, backup_file)
            
            # Cleanup old backups
            self._cleanup_old_backups(backup_dir, options['retention_days'])
            
            # Log backup completion
            self._log_backup_completion(backup_file, options['format'])
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Database backup completed: {backup_file}')
            )
            
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise CommandError(f"Database backup failed: {str(e)}")

    def _create_sql_backup(self, db_config, backup_file, compress):
        """Create SQL format backup"""
        cmd = [
            'pg_dump',
            '-h', db_config['HOST'],
            '-p', str(db_config['PORT']),
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '--no-password',
            '--verbose',
            '--clean',
            '--create',
            '--if-exists',
            '--format=plain'
        ]
        
        if compress:
            cmd.extend(['--compress=9'])
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env)
        
        if result.returncode != 0:
            raise CommandError(f"pg_dump failed: {result.stderr.decode()}")
        
        self.stdout.write(f"📄 SQL backup created: {backup_file}")

    def _create_custom_backup(self, db_config, backup_file, compress):
        """Create custom format backup (recommended)"""
        cmd = [
            'pg_dump',
            '-h', db_config['HOST'],
            '-p', str(db_config['PORT']),
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '--no-password',
            '--verbose',
            '--format=custom',
            '--compress=9' if compress else '--compress=0',
            '--file', str(backup_file)
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE, env=env)
        
        if result.returncode != 0:
            raise CommandError(f"pg_dump failed: {result.stderr.decode()}")
        
        self.stdout.write(f"📦 Custom backup created: {backup_file}")

    def _create_directory_backup(self, db_config, backup_dir):
        """Create directory format backup"""
        cmd = [
            'pg_dump',
            '-h', db_config['HOST'],
            '-p', str(db_config['PORT']),
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '--no-password',
            '--verbose',
            '--format=directory',
            '--file', str(backup_dir)
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE, env=env)
        
        if result.returncode != 0:
            raise CommandError(f"pg_dump failed: {result.stderr.decode()}")
        
        self.stdout.write(f"📁 Directory backup created: {backup_dir}")

    def _cleanup_old_backups(self, backup_dir, retention_days):
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        removed_count = 0
        
        for backup_file in backup_dir.iterdir():
            if backup_file.is_file():
                # Extract timestamp from filename
                try:
                    # Handle different filename formats
                    if '_backup_' in backup_file.name:
                        timestamp_str = backup_file.name.split('_backup_')[1].split('.')[0]
                        file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        
                        if file_date < cutoff_date:
                            backup_file.unlink()
                            removed_count += 1
                            self.stdout.write(f"🗑️  Removed old backup: {backup_file.name}")
                except (ValueError, IndexError):
                    # Skip files that don't match expected format
                    continue
        
        if removed_count > 0:
            self.stdout.write(
                self.style.WARNING(f'🧹 Cleaned up {removed_count} old backup files')
            )

    def _log_backup_completion(self, backup_file, backup_format):
        """Log backup completion to audit trail"""
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
                action_description=f'Database backup completed: {backup_file.name} ({backup_format} format)',
                success=True,
                additional_details={
                    'backup_file': str(backup_file),
                    'backup_format': backup_format,
                    'file_size_bytes': backup_file.stat().st_size if backup_file.exists() else 0,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log backup completion: {str(e)}")
