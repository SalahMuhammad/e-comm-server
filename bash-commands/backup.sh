#!/bin/bash

# Generate timestamped filename
BACKUP_FILE="backup_$(date +"%Y-%m-%d_%H-%M-%S").sql"

# Run the pg_dump command with the dynamic filename
sudo -u postgres pg_dump e-commerce > "$BACKUP_FILE"

echo "Backup saved as $BACKUP_FILE"

