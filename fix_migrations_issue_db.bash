# Function to prompt for yes/no confirmation
yes_or_no () {
    while true; do
        read -p "$* (y/n): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) echo "Aborted"; return 1;;
            * ) echo "Invalid response. Please answer y or n.";;
        esac
    done
}

# --- Configuration ---
export PGPASSWORD='BeWithAllah'
DB_NAME="e-commerce"
HOST="localhost"
# NOW=$(date +"%Y%m%d_%H%M%S")
NOW="tem.sql"
source env/bin/activate

echo "1. Backing up data only..."
pg_dump -U postgres -d $DB_NAME -h $HOST --data-only > $NOW

echo "2. Cleaning SQL dump (Removing all migration history)..."
# Extract and save initial migrations
# grep "0001_initial" $NOW | awk 'BEGIN { print "COPY public.django_migrations (id, app, name, applied) FROM stdin;" } { print } END { print "\." }' >> /tmp/initial_migrations.sql
# Remove all migration data
sed -i '/-- Data for Name: django_migrations/,/^\\\.$/d' $NOW
# Restore only initial migrations
# cat /tmp/initial_migrations.sql >> $NOW
# Reset sequence ID (set to safe value)
# sed -i "s/setval('public\.django_migrations_id_seq', [0-9]*, true)/setval('public.django_migrations_id_seq', 100, false)/" $NOW
# above line causes issues cuz it has static migrations sequance id 

echo "3. Terminating connections and dropping database..."
dropdb -U postgres -h $HOST $DB_NAME
createdb -U postgres -h $HOST $DB_NAME

# +: Allows find to pass multiple directory names to a single rm -rf command for efficiency. 
echo "4. Resetting migration files..."
find . -type d -name "migrations" -not -regex '.*\/env\/lib\/.*' -prune -exec rm -rf {} +

echo "5. Creating new migration schema..."
python3 manage.py makemigrations items employees debt_settlement expenses payment reverse_payment transfer vault_and_methods buyer_supplier_party purchase sales refillable_items_system repositories transfer_items users
python3 manage.py migrate

if yes_or_no "group permissions may causes an issue, whould you like to remove table content?"; then
    sed -i '/-- Data for Name: auth_group_permissions/,/^\\\.$/d' $NOW
fi

echo "BeWithAllah" | sudo -S -u postgres psql -d e-commerce -c "delete from auth_permission"
echo "BeWithAllah" | sudo -S -u postgres psql -d e-commerce -c "delete from django_content_type"

echo "6. Restoring data..."
psql -U postgres -d $DB_NAME -h $HOST -a -f $NOW

rm $NOW

echo "Done! Database has been fully reset and data re-imported."
