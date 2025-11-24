#!/bin/bash

# KitchenBook 数据恢复脚本

set -e

if [ $# -eq 0 ]; then
    echo "使用方法: ./restore.sh <备份文件名>"
    echo ""
    echo "可用备份："
    ls -1 ~/KitchenBook/backups/db_*.sql.gz | tail -5
    exit 1
fi

BACKUP_FILE=$1
DB_NAME=kitchenbook_db

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 错误：找不到备份文件 $BACKUP_FILE"
    exit 1
fi

echo "⚠️  警告：此操作将覆盖当前数据库！"
read -p "确认继续？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消操作"
    exit 0
fi

echo "🔄 开始恢复数据库..."
gunzip -c $BACKUP_FILE | sudo -u postgres psql $DB_NAME

echo "✅ 数据恢复完成！"
echo "🔄 重启服务..."
sudo systemctl restart gunicorn

echo "🎉 完成！"

