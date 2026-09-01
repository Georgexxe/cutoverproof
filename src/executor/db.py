"""Database manager for sandbox PostgreSQL connection, reset, and SQL execution."""

import os
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote_plus, urlparse
import psycopg
from src.evidence.serialization import to_json_safe


class DatabaseSafetyError(RuntimeError):
    """Raised when a connection target is not the dedicated local sandbox."""


class DatabaseManager:
    """Manages PostgreSQL connection and clean sandbox resets."""

    def __init__(self, connection_url: Optional[str] = None):
        if connection_url:
            self.connection_url = connection_url
        elif os.environ.get("DATABASE_URL"):
            self.connection_url = os.environ["DATABASE_URL"]
        else:
            host = os.environ.get("POSTGRES_HOST", "localhost")
            port = os.environ.get("POSTGRES_PORT", "5432")
            user = os.environ.get("POSTGRES_USER", "cutover")
            password = quote_plus(os.environ.get("POSTGRES_PASSWORD", "proof_sandbox_password"))
            database = os.environ.get("POSTGRES_DB", "cutoverproof_sandbox")
            self.connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self._validate_sandbox_target()

    def _validate_sandbox_target(self) -> None:
        """Refuses destructive reset access to anything except the dedicated local DB."""
        parsed = urlparse(self.connection_url)
        allowed_hosts = {"localhost", "127.0.0.1", "::1", "postgres"}
        configured_host = os.environ.get("CUTOVERPROOF_ALLOWED_SANDBOX_HOST", "").strip()
        configured_hosts = {
            item.strip()
            for item in os.environ.get("CUTOVERPROOF_EXTERNAL_SANDBOX_HOSTS", "").split(",")
            if item.strip()
        }
        query_host = parse_qs(parsed.query).get("host", [None])[0]
        target_host = parsed.hostname or query_host
        if configured_host:
            # Cloud deployments must opt in to exactly one dedicated sandbox
            # endpoint (including a /cloudsql/... socket path). A broad suffix,
            # wildcard, or database-name-only rule is intentionally unsupported.
            allowed_hosts.add(configured_host)
        allowed_hosts.update(configured_hosts)
        database = parsed.path.lstrip("/")
        if parsed.scheme not in {"postgresql", "postgres"}:
            raise DatabaseSafetyError("DATABASE_URL must use the PostgreSQL scheme.")
        if target_host not in allowed_hosts or database != "cutoverproof_sandbox" or parsed.username != "cutover":
            raise DatabaseSafetyError(
                "Refusing destructive sandbox reset: target must use the cutover user, "
                "the cutoverproof_sandbox database, and either a local endpoint or the "
                "exact CUTOVERPROOF_ALLOWED_SANDBOX_HOST value."
            )

    def _safe_target(self) -> str:
        parsed = urlparse(self.connection_url)
        query_host = parse_qs(parsed.query).get("host", [None])[0]
        host = parsed.hostname or query_host or "unresolved"
        return f"{parsed.username}@{host}:{parsed.port or 5432}/{parsed.path.lstrip('/')}"

    def get_connection(self) -> psycopg.Connection:
        """Establishes and returns a new database connection."""
        try:
            conn = psycopg.connect(self.connection_url, autocommit=True)
            return conn
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL sandbox at {self._safe_target()}: {e}") from e

    def reset_sandbox(self, schema_sql: str = "", seed_sql: str = "") -> None:
        """Completely drops and recreates the public schema, then applies initial schema and seed SQL."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Clean reset of schema
                cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
                cur.execute("CREATE SCHEMA public;")
                cur.execute("GRANT ALL ON SCHEMA public TO cutover;")
                cur.execute("GRANT ALL ON SCHEMA public TO public;")

                if schema_sql.strip():
                    cur.execute(schema_sql)

                if seed_sql.strip():
                    cur.execute(seed_sql)

    def execute_sql(self, sql: str) -> Tuple[int, float]:
        """Executes an arbitrary SQL block in a single transaction, returning (rows_affected, duration_ms)."""
        start_time = time.perf_counter()
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rowcount = cur.rowcount if cur.rowcount >= 0 else 0
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return rowcount, duration_ms

    def query_rows(self, sql: str) -> List[Dict[str, Any]]:
        """Executes a read-only query and returns rows as dictionaries."""
        with self.get_connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql)
                # Normalize at the database boundary so agent prompts, API
                # responses, and persisted evidence all see the same values.
                return to_json_safe(cur.fetchall())
