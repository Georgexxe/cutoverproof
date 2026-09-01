#!/bin/sh
set -eu

PG_BIN="$(dirname "$(find /usr/lib/postgresql -type f -name initdb | head -n 1)")"
PG_DATA="${CUTOVERPROOF_PG_DATA:-/tmp/cutoverproof-pgdata}"
PG_PORT="${POSTGRES_PORT:-5432}"

if [ ! -s "$PG_DATA/PG_VERSION" ]; then
  rm -rf "$PG_DATA"
  "$PG_BIN/initdb" -D "$PG_DATA" --username=cutover --auth=trust --no-locale >/dev/null
fi

"$PG_BIN/pg_ctl" -D "$PG_DATA" -l /tmp/cutoverproof-postgres.log \
  -o "-h 127.0.0.1 -k /tmp -p $PG_PORT" -w start >/dev/null

if ! "$PG_BIN/psql" -h 127.0.0.1 -p "$PG_PORT" -U cutover -d postgres -tAc \
  "SELECT 1 FROM pg_database WHERE datname = 'cutoverproof_sandbox'" | grep -q 1; then
  "$PG_BIN/createdb" -h 127.0.0.1 -p "$PG_PORT" -U cutover cutoverproof_sandbox
fi

export DATABASE_URL="${DATABASE_URL:-postgresql://cutover@127.0.0.1:$PG_PORT/cutoverproof_sandbox}"
export CUTOVERPROOF_ALLOWED_SANDBOX_HOST="${CUTOVERPROOF_ALLOWED_SANDBOX_HOST:-127.0.0.1}"

exec python -m src.api.app
