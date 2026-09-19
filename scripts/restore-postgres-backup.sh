#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 PATH_TO_BACKUP" >&2
  exit 2
fi

backup_file="$1"
restore_db="${RESTORE_DB:-messages_restore}"

if [[ ! -f "$backup_file" ]]; then
  echo "Backup file not found: ${backup_file}" >&2
  exit 2
fi

echo "Restoring ${backup_file} into database ${restore_db}" >&2
docker compose exec -T postgres sh -ec '
  dropdb --if-exists --username="$POSTGRES_USER" "$1"
  createdb --username="$POSTGRES_USER" "$1"
' sh "$restore_db"

docker compose exec -T postgres sh -ec '
  pg_restore \
    --username="$POSTGRES_USER" \
    --dbname="$1" \
    --exit-on-error \
    --no-owner \
    --no-privileges
' sh "$restore_db" <"$backup_file"

docker compose exec -T postgres sh -ec '
  psql --username="$POSTGRES_USER" --dbname="$1" --tuples-only --no-align \
    --command "SELECT count(*) FROM messages"
' sh "$restore_db"
