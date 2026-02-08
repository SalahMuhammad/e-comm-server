import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings # Import settings to get the password
import subprocess
import os
import json
import zipfile
import shutil



class Command(BaseCommand):
    help = 'take database backup'

    def add_arguments(self, parser):
        # Optional: Define command-line arguments for your command
        parser.add_argument(
            '--data_only',
            action='store_true',
            help='only data.',
        )
        parser.add_argument(
            '--media',
            action='store_true',
            help='include media directory.',
        )
        parser.add_argument(
            '--notes',
            type=str,
            help='Backup notes',
            default=''
        )
        parser.add_argument(
            '--user',
            type=str,
            help='User who triggered backup',
            default='System'
        )

    def handle(self, *args, **options):
        data_only = options['data_only']
        include_media = options['media']
        notes = options['notes']
        user = options['user']
        
        pg_data_only_flag = '-a' if data_only else ''

        db_host = settings.DATABASES['default']['HOST']
        db_port = settings.DATABASES['default']['PORT'] 
        db_user = settings.DATABASES['default']['USER']
        db_password = settings.DATABASES['default']['PASSWORD'] 
        # db_name = settings.DATABASES['default']['NAME'] # Not used in pg_dump args below directly but good to have

        # Create backup directory if it doesn't exist
        # Load config, create if missing
        config_path = 'media/config.json'
        if not os.path.exists(config_path):
             os.makedirs(os.path.dirname(config_path), exist_ok=True)
             default_config = {
                "db_backup_path": "media/backups",
                "max_backups": 15
             }
             with open(config_path, 'w') as file:
                 json.dump(default_config, file, indent=4)
        
        with open(config_path, 'r') as file:
            config = json.load(file)

        backup_dir = os.path.expanduser(config.get('db_backup_path', 'media/backups'))
        max_backups = config.get('max_backups', 15)
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
        created_at_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        config_suffix = ""
        if data_only: config_suffix += "_data-only"
        if include_media: config_suffix += "_with-media"
        
        file_name = f'{timestamp}{config_suffix}'
        sql_file_name = f'{file_name}.sql'
        sql_file_path = os.path.join(backup_dir, sql_file_name)
        
        # 2. Construct the pg_dump command
        command = [
            'pg_dump', 
            '-h', db_host, 
            '-p', str(db_port), # Ensure port is a string for the list of arguments
            '-U', db_user, 
            '-d', 'e-commerce', 
            '--clean',
            '--if-exists',
            '-f', sql_file_path,
        ]
        if pg_data_only_flag:
            command.append(pg_data_only_flag)

        # 3. Create a clean environment dictionary
        env = os.environ.copy()
        # # Set the PGPASSWORD environment variable for the subprocess
        env['PGPASSWORD'] = db_password 

        try:
            self.stdout.write(f"Executing: {self.style.SUCCESS(' '.join(command))}")
    
            subprocess.run(
                command,
                shell=False,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            final_backup_path = sql_file_path

            if include_media:
                zip_file_name = f'{file_name}.zip'
                zip_file_path = os.path.join(backup_dir, zip_file_name)
                
                self.stdout.write(f"Zipping database and media files to {zip_file_path}...")
                
                with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add SQL dump
                    zipf.write(sql_file_path, arcname=sql_file_name)
                    
                    # Add Media files
                    media_root = settings.MEDIA_ROOT
                    page_path_len = len(str(media_root).rstrip(os.sep)) + 1 
                    
                    for root, dirs, files in os.walk(media_root):
                        # Avoid including the backups directory itself if it's inside media/
                        if 'backups' in root:
                             continue
                             
                        for file in files:
                            file_path = os.path.join(root, file)
                            # relative path for zip
                            rel_path = os.path.join('media', file_path[page_path_len:])
                            zipf.write(file_path, arcname=rel_path)
                
                # Remove the raw SQL file after zipping
                os.remove(sql_file_path)
                final_backup_path = zip_file_path
                self.stdout.write(self.style.SUCCESS(f'Created ZIP backup with media.'))

            # Create metadata JSON file
            metadata = {
                "notes": notes,
                "created_at": created_at_str,
                "user": user,
                "file_name": os.path.basename(final_backup_path) # Link to the actual backup file
            }
            # The metadata file should have the same base name as the backup file
            metadata_file_name = f'{file_name}.json'
            metadata_file_path = os.path.join(backup_dir, metadata_file_name)
            
            with open(metadata_file_path, 'w') as f:
                json.dump(metadata, f, indent=4)
                
            self.stdout.write(self.style.SUCCESS(f'Created backup metadata: {metadata_file_path}'))

            self.stdout.write(self.style.SUCCESS(f'Database backup completed successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Backup saved to: {final_backup_path}'))
            
            # -------------------------------------------------------------
            # Cleanup: Keep only the last N backups (configured in config.json)
            # -------------------------------------------------------------
            try:
                # Include .sql, .dump, .json, .zip
                all_backups = []
                # We group by basename (timestamp) to delete pairs (.zip+.json) together ideally
                # But simple retention by file count works if we count main backup files (.sql/.zip/.dump)
                
                main_backup_files = []
                for f in os.listdir(backup_dir):
                    if f.endswith(('.sql', '.dump', '.zip')) and not f.endswith('.json'):
                         full_path = os.path.join(backup_dir, f)
                         main_backup_files.append(full_path)

                # Sort by modification time (descending: newest first)
                main_backup_files.sort(key=os.path.getmtime, reverse=True)
                
                # If more than max_backups, delete the excess
                if len(main_backup_files) > max_backups:
                    backups_to_delete = main_backup_files[max_backups:]
                    self.stdout.write(f"Cleaning up old backups (limit: {max_backups}). Deleting {len(backups_to_delete)} backup(s)...")
                    
                    for backup_path in backups_to_delete:
                        try:
                            # Delete the main backup file
                            os.remove(backup_path)
                            self.stdout.write(f"Deleted old backup: {os.path.basename(backup_path)}")
                            
                            # Try to delete associated JSON metadata file
                            # Assumes naming: backup_name.ext -> backup_name.json
                            base_name = os.path.splitext(backup_path)[0]
                            possible_json = f"{base_name}.json"
                            
                            if os.path.exists(possible_json):
                                os.remove(possible_json)
                                self.stdout.write(f"Deleted old metadata: {os.path.basename(possible_json)}")
                                
                        except OSError as e:
                            self.stdout.write(self.style.WARNING(f"Failed to delete {backup_path}: {e}"))
            except Exception as e:
                 self.stdout.write(self.style.WARNING(f"Error during backup cleanup: {e}"))
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'pg_dump failed with return code {e.returncode}'))
            self.stdout.write(self.style.ERROR(f'Stderr: {e.stderr}'))
            raise CommandError(f'Backup failed: {e.stderr}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'take database backup command() error: {e}'))
            raise CommandError(f'Backup failed: {e}')
