docker exec -it 082dd7db399f pg_dump -U postgres -d e-commerce > ../db/backup_$(date +"%Y%m%d_%H%M%S").sql
