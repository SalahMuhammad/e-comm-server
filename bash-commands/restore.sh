# PGPASSWORD='BeWithAllah' sudo -u postgres psql -U postgres e-commerce < backup.sql
#!/bin/bash

# Find the latest backup file
LATEST_BACKUP=$(ls -t backup_*.sql | head -n 1)

# Check if a backup file exists
if [ -z "$LATEST_BACKUP" ]; then
    echo "No backup files found!"
    exit 1
fi

echo "Restoring from $LATEST_BACKUP..."
PGPASSWORD='BeWithAllah' sudo -u postgres psql -U postgres e-commerce < "$LATEST_BACKUP"
# echo "your_sudo_password" | sudo -S -u postgres PGPASSWORD='BeWithAllah' psql -U postgres e-commerce < "$LATEST_BACKUP"
echo "Restore completed."



# 2. Switch to md5 Authentication in pg_hba.conf
# Open the PostgreSQL authentication config file:
#
# sudo nano /etc/postgresql/14/main/pg_hba.conf
# (Replace 14 with your PostgreSQL version.)
#
# Find the line that looks like this:
#
# local   all             postgres                                peer
# Change peer to md5:
#
# local   all             postgres                                md5
# Save and exit (CTRL + X, then Y, then ENTER).
#
# Restart PostgreSQL:
#
# sudo systemctl restart postgresql
# Set a password for postgres (if you haven't already):
#
# sudo -u postgres psql
# ALTER USER postgres PASSWORD 'yourpassword';
# Now, try again:
#
# PGPASSWORD='yourpassword' sudo -u postgres psql -U postgres e-commerce < backup.sql

