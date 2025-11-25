#!/bin/bash

# KitchenBook 数据库和媒体文件备份脚本

set -e

BACKUP_DIR=~/KitchenBook/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME=kitchenbook_db
MEDIA_DIR=~/KitchenBook/backend/media

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "🗄️  开始备份..."

# 备份数据库
echo "📊 备份数据库..."
sudo -u postgres pg_dump $DB_NAME | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz
echo "✓ 数据库备份完成: db_$TIMESTAMP.sql.gz"

# 备份媒体文件
echo "📸 备份媒体文件..."
tar -czf $BACKUP_DIR/media_$TIMESTAMP.tar.gz -C ~/KitchenBook/backend media/
echo "✓ 媒体文件备份完成: media_$TIMESTAMP.tar.gz"

# 清理 7 天前的备份
echo "🧹 清理旧备份（保留 7 天）..."
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete

echo "✅ 备份完成！"
echo "备份位置: $BACKUP_DIR"
ls -lh $BACKUP_DIR | tail -5

