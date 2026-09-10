#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="${GI_ENTERPRISE_DB:-gi_enterprise_demo}"
ADDON="bl_gi_enterprise_demo"
ODOO_BIN="/opt/odoo/odoo/odoo-bin"
ODOO_CONF="/etc/odoo/odoo.conf"
HOST_BACKUP="${ROOT}/backups/${DB}_golden.zip"

cd "$ROOT"

shell_script() {
  docker compose exec -T odoo python3 "$ODOO_BIN" shell \
    -c "$ODOO_CONF" -d "$DB" --no-http < "$1"
}

mutating_shell_script() {
  docker compose stop odoo >/dev/null
  set +e
  docker compose run --rm --no-deps -T odoo python3 "$ODOO_BIN" shell \
    -c "$ODOO_CONF" -d "$DB" --no-http < "$1"
  status=$?
  set -e
  docker compose up -d odoo >/dev/null
  return "$status"
}

case "${1:-help}" in
  create)
    exists="$(docker compose exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${DB}'")"
    if [[ "$exists" == "1" ]]; then
      echo "Database ${DB} already exists; initializing/updating module ${ADDON}..."
      docker compose exec -T odoo python3 "$ODOO_BIN" server \
        -c "$ODOO_CONF" -d "$DB" -u "$ADDON" --without-demo=True --stop-after-init --no-http
    else
      echo "Creating new database ${DB} and installing ${ADDON}..."
      docker compose exec -T odoo python3 "$ODOO_BIN" server \
        -c "$ODOO_CONF" -d "$DB" -i "$ADDON" --without-demo=True --stop-after-init --no-http
    fi
    echo "Seeding GI Enterprises demo data..."
    mutating_shell_script "${ROOT}/custom-addons/${ADDON}/scripts/seed_gi_enterprise_demo.py"
    echo "Verifying setup..."
    shell_script "${ROOT}/custom-addons/${ADDON}/scripts/verify_gi_enterprise_demo.py"
    ;;
  seed)
    mutating_shell_script "${ROOT}/custom-addons/${ADDON}/scripts/seed_gi_enterprise_demo.py"
    ;;
  verify)
    shell_script "${ROOT}/custom-addons/${ADDON}/scripts/verify_gi_enterprise_demo.py"
    ;;
  backup)
    mkdir -p "${ROOT}/backups"
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT
    docker compose exec -T db pg_dump -U odoo --no-owner "$DB" > "${tmp}/dump.sql"
    printf '{\n  "odoo_dump": "1",\n  "db_name": "%s",\n  "version": "19.0",\n  "major_version": "19.0",\n  "pg_version": "16"\n}\n' "$DB" > "${tmp}/manifest.json"
    if docker compose exec -T odoo test -d "/var/lib/odoo/filestore/${DB}"; then
      docker compose cp "odoo:/var/lib/odoo/filestore/${DB}" "${tmp}/filestore" >/dev/null
    fi
    rm -f "$HOST_BACKUP"
    (cd "$tmp" && zip -qr "$HOST_BACKUP" dump.sql manifest.json filestore)
    trap - EXIT
    rm -rf "$tmp"
    echo "Golden backup written to ${HOST_BACKUP}"
    ;;
  restore)
    backup="${2:-$HOST_BACKUP}"
    target="${3:-${DB}_restore_test}"
    [[ -f "$backup" ]] || { echo "Backup not found: $backup" >&2; exit 1; }
    [[ "$target" =~ ^[a-z0-9_]+$ ]] || { echo "Unsafe database name: $target" >&2; exit 1; }
    tmp="$(mktemp -d)"
    trap 'docker compose up -d odoo >/dev/null; rm -rf "$tmp"' EXIT
    unzip -q "$backup" -d "$tmp"
    [[ -f "${tmp}/dump.sql" ]] || { echo "Backup has no dump.sql" >&2; exit 1; }
    docker compose stop odoo >/dev/null
    docker compose exec -T db dropdb -U odoo --if-exists --force "$target"
    docker compose exec -T db createdb -U odoo "$target"
    docker compose exec -T db psql -U odoo -d "$target" -v ON_ERROR_STOP=1 < "${tmp}/dump.sql" >/dev/null
    docker compose run --rm --no-deps -T odoo sh -c "rm -rf '/var/lib/odoo/filestore/${target}' && mkdir -p '/var/lib/odoo/filestore/${target}'"
    if [[ -d "${tmp}/filestore" ]]; then
      (cd "${tmp}/filestore" && COPYFILE_DISABLE=1 tar --no-xattrs -cf - .) | docker compose run --rm --no-deps -T odoo sh -c "tar -xf - -C '/var/lib/odoo/filestore/${target}'"
    fi
    docker compose up -d odoo >/dev/null
    trap - EXIT
    rm -rf "$tmp"
    echo "Restored ${backup} into ${target}"
    ;;
  reset)
    [[ -f "$HOST_BACKUP" ]] || { echo "Golden backup not found: $HOST_BACKUP" >&2; exit 1; }
    "$0" restore "$HOST_BACKUP" "$DB"
    ;;
  *)
    echo "Usage: scripts/gi_enterprise_demo.sh {create|seed|verify|backup|restore [zip] [target]|reset}"
    ;;
esac
