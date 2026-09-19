#!/usr/bin/env bash
set -Eeuo pipefail

backup_dir="${BACKUP_DIR:-backups}"
backup_file="${backup_dir}/messages-$(date -u +%Y%m%dT%H%M%SZ).dump"

mkdir -p "$backup_dir"

echo "Creating PostgreSQL backup at ${backup_file}" >&2
docker compose exec -T postgres sh -ec '
  pg_dump \
    --username="$POSTGRES_USER" \
    --format=custom \
    --no-owner \
    --no-privileges \
    "$POSTGRES_DB"
' >"$backup_file"

if [[ ! -s "$backup_file" ]]; then
  echo "Backup file is empty: ${backup_file}" >&2
  exit 1
fi

printf '%s\n' "$backup_file"
