#!/usr/bin/env python3
"""
Database backup script
"""
import os
import sys
import click
import gzip
import shutil
from datetime import datetime, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.database import db_manager
from config.settings import Config
from utils.logger import setup_logger
from utils.email_notifier import email_notifier

logger = setup_logger(__name__)


@click.command()
@click.option('--output-dir', help='Backup output directory')
@click.option('--compress', is_flag=True, default=True, help='Compress backup files')
@click.option('--cleanup-old', is_flag=True, default=True, help='Clean up old backups')
@click.option('--retention-days', type=int, default=30, help='Days to retain backups')
@click.option('--notify', is_flag=True, default=True, help='Send email notifications')
def main(output_dir, compress, cleanup_old, retention_days, notify):
    """Create database backup"""
    
    config = Config()
    start_time = datetime.utcnow()
    
    # Set output directory
    if not output_dir:
        output_dir = config.BACKUP_PATH
    
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Starting database backup to: {output_dir}")
    
    try:
        # Generate backup filename
        timestamp = start_time.strftime('%Y%m%d_%H%M%S')
        backup_filename = f"automotive_prices_backup_{timestamp}.sql"
        backup_path = os.path.join(output_dir, backup_filename)
        
        # Create backup
        logger.info("Creating database backup...")
        success = db_manager.backup_database(backup_path)
        
        if not success:
            raise Exception("Database backup failed")
        
        # Get backup file size
        backup_size = os.path.getsize(backup_path)
        logger.info(f"Backup created: {backup_path} ({backup_size / 1024 / 1024:.2f} MB)")
        
        # Compress backup if requested
        if compress:
            logger.info("Compressing backup file...")
            compressed_path = f"{backup_path}.gz"
            
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            os.remove(backup_path)
            backup_path = compressed_path
            
            compressed_size = os.path.getsize(backup_path)
            compression_ratio = (backup_size - compressed_size) / backup_size * 100
            logger.info(f"Backup compressed: {compressed_path} ({compressed_size / 1024 / 1024:.2f} MB, {compression_ratio:.1f}% reduction)")
        
        # Cleanup old backups
        if cleanup_old:
            _cleanup_old_backups(output_dir, retention_days)
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Send success notification
        if notify:
            _send_backup_notification(True, backup_path, duration, backup_size if not compress else compressed_size)
        
        logger.info(f"Database backup completed successfully in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        
        # Send error notification
        if notify:
            email_notifier.send_error_alert(
                'Database Backup Failed',
                f"Database backup failed: {str(e)}"
            )
        
        sys.exit(1)


def _cleanup_old_backups(backup_dir: str, retention_days: int):
    """Clean up backup files older than retention period"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        removed_count = 0
        total_size_removed = 0
        
        for filename in os.listdir(backup_dir):
            if filename.startswith('automotive_prices_backup_'):
                filepath = os.path.join(backup_dir, filename)
                
                # Check file modification time
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_mtime < cutoff_date:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    removed_count += 1
                    total_size_removed += file_size
                    logger.info(f"Removed old backup: {filename}")
        
        if removed_count > 0:
            logger.info(f"Cleanup completed: {removed_count} files removed ({total_size_removed / 1024 / 1024:.2f} MB freed)")
        else:
            logger.info("No old backups to clean up")
            
    except Exception as e:
        logger.error(f"Error during backup cleanup: {e}")


def _send_backup_notification(success: bool, backup_path: str, duration: float, file_size: int):
    """Send backup completion notification"""
    try:
        if success:
            subject = "✅ Database Backup Completed"
            message = f"""
Database Backup Completed
========================

Backup Details:
- File: {os.path.basename(backup_path)}
- Size: {file_size / 1024 / 1024:.2f} MB
- Duration: {duration:.2f} seconds
- Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

The backup has been stored securely and is ready for use if needed.
"""
        else:
            subject = "❌ Database Backup Failed"
            message = f"""
Database Backup Failed
=====================

The scheduled database backup has failed. Please check the system logs for more details.

Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        email_notifier.send_notification(subject, message)
        
    except Exception as e:
        logger.error(f"Error sending backup notification: {e}")


@click.command()
@click.option('--backup-file', required=True, help='Backup file to restore from')
@click.option('--confirm', is_flag=True, help='Confirm the restoration')
def restore_backup(backup_file, confirm):
    """Restore database from backup file"""
    
    if not confirm:
        click.echo("This will overwrite the current database!")
        click.echo("Use --confirm flag to proceed with restoration.")
        sys.exit(1)
    
    if not os.path.exists(backup_file):
        click.echo(f"Backup file not found: {backup_file}")
        sys.exit(1)
    
    logger.info(f"Starting database restore from: {backup_file}")
    
    try:
        config = Config()
        
        # Prepare restore command
        if backup_file.endswith('.gz'):
            # Compressed backup
            restore_cmd = f"gunzip -c {backup_file} | mysql -h{config.DB_HOST} -P{config.DB_PORT} -u{config.DB_USER} -p{config.DB_PASSWORD} {config.DB_NAME}"
        else:
            # Uncompressed backup
            restore_cmd = f"mysql -h{config.DB_HOST} -P{config.DB_PORT} -u{config.DB_USER} -p{config.DB_PASSWORD} {config.DB_NAME} < {backup_file}"
        
        # Execute restore
        import subprocess
        result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Database restore completed successfully")
            click.echo("✅ Database restore completed successfully")
        else:
            logger.error(f"Database restore failed: {result.stderr}")
            click.echo(f"❌ Database restore failed: {result.stderr}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Database restore failed: {e}")
        click.echo(f"❌ Database restore failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        # Remove 'restore' from argv to let click handle the rest
        sys.argv.pop(1)
        restore_backup()
    else:
        main()
