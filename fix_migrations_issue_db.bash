# --- Configuration ---
export PGPASSWORD='BeWithAllah'
DB_NAME="e-commerce"
NOW=$(date +"%Y%m%d_%H%M%S")
source env/bin/activate

pg_dump -U postgres -d $DB_NAME --data-only > $NOW.sql
sed -i '/-- Data for Name: django_migrations/,/^\\\.$/d' $NOW.sql
sed -i "s/setval('public\.django_migrations_id_seq', [0-9]*, true)/setval('public.django_migrations_id_seq', 100, false)/" $NOW.sql
# above line causes issues cuz it has static migrations sequance id 

dropdb -U postgres $DB_NAME
createdb -U postgres $DB_NAME

# +: Allows find to pass multiple directory names to a single rm -rf command for efficiency. 
find . -type d -name "migrations" -not -regex '.*\/env\/lib\/.*' -prune -exec rm -rf {} +

python3 manage.py makemigrations items employees debt_settlement expenses payment reverse_payment transfer vault_and_methods buyer_supplier_party purchase sales refillable_items_system repositories transfer_items users
python3 manage.py migrate

psql -U postgres -d $DB_NAME -a -f $NOW.sql

rm $NOW.sql
