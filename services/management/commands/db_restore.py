import os
import json
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    help = 'Restore database from backup'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the backup file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        # Validate file path
        if not os.path.exists(file_path):
            with open('media/config.json', 'r') as file:
                config = json.load(file)
            backup_dir = os.path.expanduser(config.get('db_backup_path', 'media/backups'))
            potential_path = os.path.join(backup_dir, file_path)
            if os.path.exists(potential_path):
                file_path = potential_path
            else:
                raise CommandError(f'File not found: {file_path}')

        is_zip = file_path.endswith('.zip')
        restore_source_sql = file_path
        temp_extract_dir = None

        try:
            if is_zip:
                import zipfile
                import shutil
                import tempfile

                self.stdout.write(f"Detected ZIP backup. Extracting...")
                
                # Create a temporary directory for extraction
                temp_extract_dir = tempfile.mkdtemp()
                
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_dir)
                
                # Find the SQL file
                sql_files = [f for f in os.listdir(temp_extract_dir) if f.endswith('.sql')]
                if not sql_files:
                    raise CommandError("No SQL file found in the ZIP archive.")
                
                restore_source_sql = os.path.join(temp_extract_dir, sql_files[0])
                
                # Check for media directory in extracted files
                extracted_media_dir = os.path.join(temp_extract_dir, 'media')
                if os.path.exists(extracted_media_dir):
                    self.stdout.write("Restoring media files...")
                    target_media_root = settings.MEDIA_ROOT
                    
                    # Merge/Overlay extracted media onto current media root
                    # shutil.copytree(extracted_media_dir, target_media_root, dirs_exist_ok=True) 
                    # Use a safer copy method loop to inspect/log
                    for root, dirs, files in os.walk(extracted_media_dir):
                        # Construct corresponding destination path
                        rel_path = os.path.relpath(root, extracted_media_dir)
                        dest_path = os.path.join(target_media_root, rel_path)
                        
                        os.makedirs(dest_path, exist_ok=True)
                        
                        for file in files:
                            src_file = os.path.join(root, file)
                            dst_file = os.path.join(dest_path, file)
                            shutil.copy2(src_file, dst_file)
                            
                    self.stdout.write(self.style.SUCCESS("Media files restored."))

            # Validate SQL file (whether raw or extracted)
            if not self.is_valid_backup(restore_source_sql):
                 raise CommandError('Invalid backup file. It does not appear to be a valid PostgreSQL dump for this application.')
    
            db_host = settings.DATABASES['default']['HOST']
            db_port = settings.DATABASES['default']['PORT']
            db_user = settings.DATABASES['default']['USER']
            db_password = settings.DATABASES['default']['PASSWORD']
            db_name = settings.DATABASES['default']['NAME']
    
            # Construct psql command
            command = [
                'psql',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '-f', restore_source_sql,
            ]
    
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password
            
            # Step 1: Clean database schema to ensure full restore (handles deletions)
            self.stdout.write("Cleaning database schema...")
            clean_command = [
                'psql',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '-c', 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
            ]
            subprocess.run(
                clean_command,
                env=env,
                check=True,
                capture_output=True,
                text=True
            )

            self.stdout.write(f"Executing restore from: {restore_source_sql}")
            
            # Use subprocess run
            subprocess.run(
                command,
                env=env,
                check=True,
                capture_output=True,
                text=True
            )
            
            self.stdout.write(self.style.SUCCESS(f'Database restored successfully from {file_path}'))
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Restore failed with return code {e.returncode}'))
            self.stdout.write(self.style.ERROR(f'Stderr: {e.stderr}'))
            raise CommandError(f'Restore failed: {e.stderr}')
        except Exception as e:
            raise CommandError(f'Restore failed: {e}')
        finally:
            # Cleanup temp dir
            if temp_extract_dir and os.path.exists(temp_extract_dir):
                import shutil
                shutil.rmtree(temp_extract_dir)

    def is_valid_backup(self, file_path):
        """
        Check if the file looks like a valid PostgreSQL dump and contains expected tables.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first 50 lines for header check
                header_valid = False
                app_specific_valid = False
                
                # Check first few lines for pg_dump signature
                for i in range(50):
                    line = f.readline()
                    if 'PostgreSQL database dump' in line:
                        header_valid = True
                        break
                
                # If header not found in first 50 lines, it might not be a valid dump
                if not header_valid:
                    # Fallback: maybe it's just SQL statements without the standard header comment?
                    # But pg_dump usually includes it. Let's be strict for now to avoid restoring garbage.
                    # Or maybe checking for specific tables is enough.
                    pass

                # Reset pointer to search for content validation (scan a bit more if needed, or just rely on finding keywords anywhere)
                # But reading valid large files is expensive. 
                # Let's read chunks looking for critical table names.
                # Valid tables for this app: auth_user, users_user, items_item, etc.
                
                f.seek(0)
                content_sample = f.read(100000) # Read first 100KB which should contain structure or data for start
                
                if 'PostgreSQL database dump' in content_sample:
                     header_valid = True

                # Check for some core app tables to ensure it matches THIS app
                # We check for 'users_user' (custom user model) or 'items_item' (core inventory)
                critical_markers = ['users_user', 'items_item', 'django_migrations']
                
                for marker in critical_markers:
                    if marker in content_sample:
                        app_specific_valid = True
                        break
                
                return header_valid and app_specific_valid
        except Exception as e:
            # If we can't read the file, it's invalid
            return False
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Restore failed with return code {e.returncode}'))
            self.stdout.write(self.style.ERROR(f'Stderr: {e.stderr}'))
            raise CommandError(f'Restore failed: {e.stderr}')
        except Exception as e:
            raise CommandError(f'Restore failed: {e}')
