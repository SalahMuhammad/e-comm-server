#!/bin/bash

# Directory containing backup files
BACKUP_DIR="db"

# Check if directory exists and has files
if [ ! -d "$BACKUP_DIR" ]; then
  echo "Directory $BACKUP_DIR does not exist!"
  exit 1
fi

FILES=($(ls "$BACKUP_DIR")) # List files in the directory
if [ ${#FILES[@]} -eq 0 ]; then
  echo "No files found in $BACKUP_DIR!"
  exit 1
fi

# Display files for the user to choose
echo "Available files in $BACKUP_DIR:"
for i in "${!FILES[@]}"; do
  echo "$((i+1)). ${FILES[$i]}"
done

# Prompt user for choice
read -p "Enter the number of the file you want to use: " CHOICE

# Validate user input
if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "${#FILES[@]}" ]; then
  echo "Invalid choice. Exiting."
  exit 1
fi

# Get the chosen file
CHOSEN_FILE="${FILES[$((CHOICE-1))]}"
echo "You selected: $CHOSEN_FILE"

# Perform the restoration
docker exec -i 082dd7db399f psql -U postgres -d postgres -c "CREATE DATABASE \"e-commerce\"";
docker exec -i 082dd7db399f psql -U postgres -d e-commerce < "$BACKUP_DIR/$CHOSEN_FILE"
