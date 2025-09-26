"""
Django management command for database restore procedures
"""

import os
import subprocess
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Restore PostgreSQL database from backup'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to the backup file to restore'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restore without confirmation'
        )
        parser.add_argument(
            '--create-db',
            action='store_true',
            help='Create database if it does not exist'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean (drop) existing database before restore'
        )

    def handle(self, *args, **options):
        """Execute database restore"""
        try:
            backup_file = Path(options['backup_file'])
            
            if not backup_file.exists():
                raise CommandError(f"Backup file not found: {backup_file}")
            
            # Get database configuration
            db_config = settings.DATABASES['default']
            
            # Confirm restore operation
            if not options['force']:
                confirm = input(
                    f"⚠️  This will restore database '{db_config['NAME']}' from {backup_file.name}. "
                    f"Are you sure? (yes/no): "
                )
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.WARNING('Restore operation cancelled.'))
                    return
            
            self.stdout.write(
                self.style.SUCCESS('🔄 Starting database restore procedure...')
            )
            
            # Determine backup format and restore method
            if backup_file.suffix == '.sql':
                self._restore_sql_backup(db_config, backup_file, options)
            elif backup_file.suffix == '.dump':
                self._restore_custom_backup(db_config, backup_file, options)
            elif backup_file.is_dir():
                self._restore_directory_backup(db_config, backup_file, options)
            else:
                raise CommandError(f"Unsupported backup format: {backup_file.suffix}")
            
            # Log restore completion
            self._log_restore_completion(backup_file)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Database restore completed from: {backup_file}')
            )
            
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            raise CommandError(f"Database restore failed: {str(e)}")

    def _restore_sql_backup(self, db_config, backup_file, options):
        """Restore from SQL format backup"""
        cmd = [
            'psql',
            '-h', db_config['HOST'],
            '-p', str(db_config['PORT']),
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '--no-password',
            '--verbose'
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        with open(backup_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, env=env)
        
        if result.returncode != 0:
            raise CommandError(f"psql restore failed: {result.stderr.decode()}")
        
        self.stdout.write(f"📄 SQL backup restored from: {backup_file}")

    def _restore_custom_backup(self, db_config, backup_file, options):
        """Restore from custom format backup"""
        cmd = [
            'pg_restore',
            '-h', db_config['HOST'],
            '-p', str(db_config['PORT']),
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '--no-password',
            '--verbose',
            '--clean' if options['clean'] else '--if-exists',
            '--create' if options['create_db'] else '--no-create',
            str(backup_file)
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE, env=env)
        
        if result.returncode != 0:
            raise CommandError(f"pg_restore failed: {result.stderr.decode()}")
        
        self.stdout.write(f"📦 Custom backup restored from: {backup_file}")

    def _restore_directory_backup(self, db_config, backup_dir, options):
        """Restore from directory format backup"""
        cmd = [
            'pg_restore',
            '-h', db_config['HOST'],
            '-p', str(db_config['PORT']),
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '--no-password',
            '--verbose',
            '--clean' if options['clean'] else '--if-exists',
            '--create' if options['create_db'] else '--no-create',
            str(backup_dir)
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE, env=env)
        
        if result.returncode != 0:
            raise CommandError(f"pg_restore failed: {result.stderr.decode()}")
        
        self.stdout.write(f"📁 Directory backup restored from: {backup_dir}")

    def _log_restore_completion(self, backup_file):
        """Log restore completion to audit trail"""
        try:
            from analytics.services.audit_trail_manager import AuditTrailManager
            
            audit_manager = AuditTrailManager()
            audit_manager.log_action(
                user_id=None,  # System action
                action_type='system_event',
                action_category='system',
                resource_type='system',
                resource_id=None,
                resource_name='database_restore',
                action_description=f'Database restore completed from: {backup_file.name}',
                success=True,
                additional_details={
                    'backup_file': str(backup_file),
                    'restore_timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log restore completion: {str(e)}")
