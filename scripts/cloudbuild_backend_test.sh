#!/usr/bin/env bash
set -euo pipefail

apt-get update --quiet
DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet postgresql postgresql-client

pg_version="$(pg_lsclusters --no-header | awk 'NR == 1 { print $1 }')"
pg_ctlcluster "$pg_version" main start
su postgres -c "psql --set ON_ERROR_STOP=1 --command=\"CREATE USER cutover WITH PASSWORD 'proof_sandbox_password';\""
su postgres -c "createdb --owner cutover cutoverproof_sandbox"

pip install --quiet -r requirements.txt
pytest -q --basetemp=/tmp/cutoverproof-tests -o cache_dir=/tmp/cutoverproof-cache
