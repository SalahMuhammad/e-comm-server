import subprocess
import datetime
import os

def run_sudo_command(command, sudo_password):
    process = subprocess.Popen(
        ['sudo', '-S'] + command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = process.communicate(sudo_password + '\n')
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command, stderr)
    return stdout

def backup_database(sudo_password):
    # Create backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = f"backup_{timestamp}.sql"
    
    try:
        # Execute pg_dump command
        run_sudo_command([
            '-u',
            'postgres',
            'pg_dump',
            'e-commerce',
            '-f',
            backup_file
        ], sudo_password)
        
        print(f"Backup saved successfully as {backup_file}")
        return backup_file
    
    except subprocess.CalledProcessError as e:
        print(f"Error creating backup: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def clone_database(backup_file, sudo_password):
    if not backup_file or not os.path.exists(backup_file):
        print("Backup file not found")
        return False
        
    try:
        # Drop existing test database if it exists
        run_sudo_command([
            '-u', 
            'postgres',
            'dropdb',
            '--if-exists',
            'e-commerce-test'
        ], sudo_password)
        
        # Create new test database
        run_sudo_command([
            '-u',
            'postgres',
            'createdb',
            'e-commerce-test'
        ], sudo_password)
        
        # Restore backup to test database
        run_sudo_command([
            '-u',
            'postgres',
            'psql',
            'e-commerce-test',
            '-f',
            backup_file
        ], sudo_password)
        
        print("Test database created successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error cloning database: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Get sudo password from environment variable
    sudo_password = os.environ.get('DB_SUDO_PASSWORD')
    
    if not sudo_password:
        print("Error: DB_SUDO_PASSWORD environment variable not set")
        exit(1)
    
    # Create backup
    backup_file = backup_database(sudo_password)
    
    if backup_file:
        # Clone database using backup
        if clone_database(backup_file, sudo_password):
            print("Database cloning completed successfully")
        else:
            print("Database cloning failed")