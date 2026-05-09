#!/bin/bash
# Бэкап PostgreSQL базы данных

BACKUP_DIR="/Users/skvorcmen/PycharmProjects/iSwim_Django/backups"
DB_NAME="iswim_stats_db"
DB_USER="iswim_user"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# Создаём директорию если её нет
mkdir -p $BACKUP_DIR

# Создаём бэкап
PGPASSWORD="iSwim123" pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_FILE

# Сжимаем
gzip $BACKUP_FILE

# Удаляем бэкапы старше 30 дней
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "✅ Бэкап создан: ${BACKUP_FILE}.gz"
echo "📁 Размер: $(du -h ${BACKUP_FILE}.gz | cut -f1)"
