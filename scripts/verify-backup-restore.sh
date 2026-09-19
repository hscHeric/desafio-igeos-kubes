#!/usr/bin/env bash
set -Eeuo pipefail

restore_db="ci_messages_restore"
backup_file="$(BACKUP_DIR=/tmp/postgres-backups bash scripts/backup-postgres.sh)"

source_count="$(docker compose exec -T postgres sh -ec '
  psql --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --tuples-only --no-align \
    --command "SELECT count(*) FROM messages"
')"
restored_count="$(RESTORE_DB="$restore_db" bash scripts/restore-postgres-backup.sh "$backup_file")"

if [[ "$source_count" != "$restored_count" ]]; then
  echo "Restored row count (${restored_count}) differs from source (${source_count})" >&2
  exit 1
fi

echo "Backup and restore verified: ${restored_count} message(s) restored into ${restore_db}"
