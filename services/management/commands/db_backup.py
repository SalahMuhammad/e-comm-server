import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings # Import settings to get the password
import subprocess
import os
import json
# import shlex



class Command(BaseCommand):
    help = 'take database backup'

    def add_arguments(self, parser):
        # Optional: Define command-line arguments for your command
        parser.add_argument(
            '--data_only',
            action='store_true',
            help='only data.',
        )

    def handle(self, *args, **options):
        data_only = options['data_only']
        data_only = '-a' if data_only else ''

        db_host = settings.DATABASES['default']['HOST']
        db_port = settings.DATABASES['default']['PORT'] 
        db_user = settings.DATABASES['default']['USER']
        db_password = settings.DATABASES['default']['PASSWORD'] 

        # Create backup directory if it doesn't exist
        with open('media/config.json', 'r') as file:
            config = json.load(file)
        
        backup_dir = os.path.expanduser(config['db_backup_path'])
        os.makedirs(backup_dir, exist_ok=True)

        # Full path to backup file
        backup_file = os.path.join(
            backup_dir,
            f'{datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")} {"--data-only" if data_only else ""}.sql'
        )
        
        # 2. Construct the pg_dump command
        command = [
            'pg_dump', 
            '-h', db_host, 
            '-p', db_port, # Ensure port is a string for the list of arguments
            '-U', db_user, 
            '-d', 'e-commerce', 
            '-f', backup_file,
        ]
        command.append(data_only) if data_only else None 

        # 3. Create a clean environment dictionary
        env = os.environ.copy()
        # # Set the PGPASSWORD environment variable for the subprocess
        env['PGPASSWORD'] = db_password 

        try:
            self.stdout.write(f"Executing: {self.style.SUCCESS(' '.join(command))}")
    
            # build a safe shell command that runs pg_dump then prints the backup path
            # cmd_str = ' '.join(shlex.quote(c) for c in command)
            # full_cmd = f'{cmd_str} && printf "BACKUP_FILE:%s\\n" {shlex.quote(backup_file)}'
            subprocess.run(
                # ['/bin/sh', '-c', full_cmd],
                command,
                shell=False,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )

            # Extract the backup file path from the output
            # backup_file_path = result.stdout.split("BACKUP_FILE:")[1].strip()
            self.stdout.write(self.style.SUCCESS(f'Database backup completed successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Backup saved to: {backup_file}'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'pg_dump failed with return code {e.returncode}'))
            self.stdout.write(self.style.ERROR(f'Stderr: {e.stderr}'))
            raise CommandError(f'Backup failed: {e.stderr}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'take database backup command() error: {e}'))
            raise CommandError(f'Backup failed: {e}')
            
        # self.stdout.write(self.style.SUCCESS('Command finished successfully!'))
