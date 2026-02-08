# --- Configuration ---
export PGPASSWORD='BeWithAllah'
DB_NAME="e-commerce"
HOST="localhost"
NOW=$(date +"%Y%m%d_%H%M%S")
source env/bin/activate

echo "1. Backing up data only..."
pg_dump -U postgres -d $DB_NAME -h $HOST --data-only > $NOW

echo "2. Cleaning SQL dump (Removing all migration history)..."
sed -i '/-- Data for Name: django_migrations/,/^\\\.$/d' $NOW
sed -i "s/setval('public\.django_migrations_id_seq', [0-9]*, true)/setval('public.django_migrations_id_seq', 100, false)/" $NOW
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

echo "6. Restoring data..."
psql -U postgres -d $DB_NAME -h $HOST -a -f $NOW

# rm $NOW

echo "Done! Database has been fully reset and data re-imported."
