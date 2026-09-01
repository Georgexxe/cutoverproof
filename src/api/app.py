"""FastAPI application for the CutoverProof customer portal."""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os
import re
import secrets
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.schemas import (
    ConnectionTestRequest,
    JobAccepted,
    LoginRequest,
    RepairApproval,
    RunCreate,
    ScenarioPackImport,
)
from src.api.service import (
    ProductServiceError,
    approve_and_replay,
    benchmark_summary,
    evidence_path,
    execute_run,
    get_run,
    list_runs,
    list_scenarios,
)
from src.agent.llm_client import LLMClient
from src.executor.db import DatabaseManager


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = PROJECT_ROOT / "web" / "dist" / "client"
IMPORTED_SCENARIOS = PROJECT_ROOT / "artifacts" / "imported_scenarios"
SESSION_COOKIE = "cutoverproof_session"

app = FastAPI(
    title="CutoverProof API",
    version="0.2.0",
    description=(
        "Bounded agent-driven schedule search, deterministic PostgreSQL execution, "
        "independent invariant verification, and human-approved sandbox replay."
    ),
)


def _jobs(request: Request) -> dict[str, dict[str, Any]]:
    if not hasattr(request.app.state, "jobs"):
        request.app.state.jobs = {}
    return request.app.state.jobs


def _state_dict(app_instance: FastAPI, name: str) -> dict[str, Any]:
    if not hasattr(app_instance.state, name):
        setattr(app_instance.state, name, {})
    return getattr(app_instance.state, name)


def _expected_login() -> tuple[str, str]:
    email = os.environ.get("CUTOVERPROOF_DEMO_EMAIL", "engineer@cutoverproof.dev").strip().lower()
    password = os.environ.get("CUTOVERPROOF_DEMO_PASSWORD", "")
    if not password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo access is not configured on this server.",
        )
    return email, password


@app.middleware("http")
async def require_demo_session(request: Request, call_next):
    public_paths = {"/api/health", "/api/auth/login", "/api/auth/session", "/api"}
    if request.url.path.startswith("/api/") and request.url.path not in public_paths:
        token = request.cookies.get(SESSION_COOKIE, "")
        sessions = _state_dict(request.app, "sessions")
        if not token or token not in sessions:
            return JSONResponse(status_code=401, content={"detail": "Sign in to continue."})
    return await call_next(request)


@app.exception_handler(ProductServiceError)
async def product_error_handler(_request: Request, exc: ProductServiceError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


@app.get("/api/health", tags=["system"])
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "surface": "customer_portal",
        "model_configured": LLMClient().is_live_model_available(),
        "execution_boundary": "checked-in synthetic scenarios and allow-listed repairs",
        "demo_access_configured": bool(os.environ.get("CUTOVERPROOF_DEMO_PASSWORD")),
    }


@app.post("/api/auth/login", tags=["auth"])
async def login(payload: LoginRequest, request: Request) -> JSONResponse:
    expected_email, expected_password = _expected_login()
    email_ok = hmac.compare_digest(payload.email.strip().lower(), expected_email)
    password_ok = hmac.compare_digest(payload.password, expected_password)
    if not (email_ok and password_ok):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    token = secrets.token_urlsafe(32)
    _state_dict(request.app, "sessions")[token] = {"email": expected_email}
    response = JSONResponse({"authenticated": True, "email": expected_email})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=os.environ.get("CUTOVERPROOF_COOKIE_SECURE", "false").lower() == "true",
        samesite="strict",
        max_age=8 * 60 * 60,
        path="/",
    )
    return response


@app.get("/api/auth/session", tags=["auth"])
async def session(request: Request) -> dict[str, Any]:
    token = request.cookies.get(SESSION_COOKIE, "")
    record = _state_dict(request.app, "sessions").get(token)
    return {"authenticated": bool(record), "email": record.get("email") if record else None}


@app.post("/api/auth/logout", tags=["auth"])
async def logout(request: Request) -> JSONResponse:
    token = request.cookies.get(SESSION_COOKIE, "")
    _state_dict(request.app, "sessions").pop(token, None)
    response = JSONResponse({"authenticated": False})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@app.get("/api/scenarios", tags=["assessments"])
async def scenarios() -> list[dict[str, Any]]:
    return await asyncio.to_thread(list_scenarios)


_DANGEROUS_SQL = re.compile(
    r"\b(COPY|PROGRAM|CREATE\s+EXTENSION|ALTER\s+SYSTEM|CREATE\s+ROLE|ALTER\s+ROLE|"
    r"DROP\s+DATABASE|CREATE\s+DATABASE|PG_READ_FILE|PG_WRITE_FILE|LO_IMPORT|DBLINK|"
    r"POSTGRES_FDW|FILE_FDW)\b",
    re.IGNORECASE,
)


def _validate_imported_sql(payload: ScenarioPackImport) -> None:
    sql_blocks = [payload.schema_sql, payload.seed_sql]
    sql_blocks.extend(operation.sql for operation in payload.operations.values())
    sql_blocks.extend(invariant.sql for invariant in payload.invariants)
    if payload.repair_sql:
        sql_blocks.append(payload.repair_sql)
    if any(_DANGEROUS_SQL.search(sql) for sql in sql_blocks):
        raise HTTPException(400, "The pack contains a server-level SQL command outside the sandbox contract.")
    if bool(payload.permitted_repairs) != bool(payload.repair_sql and payload.repair_sql.strip()):
        raise HTTPException(400, "A declared repair and its repair_sql must be supplied together.")
    phase_ids = {phase.id for phase in payload.phases}
    for key, operation in payload.operations.items():
        if key != operation.id:
            raise HTTPException(400, f"Operation key '{key}' must match its id.")
        if operation.phase not in phase_ids:
            raise HTTPException(400, f"Operation '{key}' references an unknown phase.")
    for invariant in payload.invariants:
        normalized = invariant.sql.lstrip().upper()
        if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
            raise HTTPException(400, f"Invariant '{invariant.id}' must be a read-only SELECT or WITH query.")


def _stored_pack_matches(destination: Path, payload: ScenarioPackImport) -> bool:
    """Return whether an existing imported pack is byte-for-byte equivalent in meaning.

    The bundled example is intentionally reusable. Re-importing the same validated
    payload should start another assessment rather than fail with an ID conflict.
    A different payload that reuses an ID remains a conflict so evidence cannot be
    silently rebound to changed SQL.
    """

    try:
        scenario = json.loads((destination / "scenario.json").read_text(encoding="utf-8"))
        stored = {
            "id": scenario["id"],
            "name": scenario["name"],
            "description": scenario["description"],
            "schema_sql": (destination / "schema.sql").read_text(encoding="utf-8"),
            "seed_sql": (destination / "seed.sql").read_text(encoding="utf-8"),
            "phases": scenario["phases"],
            "operations": scenario["operations"],
            "invariants": scenario["invariants"],
            "permitted_repairs": scenario.get("permitted_repairs", []),
            "repair_sql": (
                (destination / "repair.sql").read_text(encoding="utf-8")
                if (destination / "repair.sql").exists()
                else None
            ),
            "max_candidates": scenario["max_candidates"],
            "max_schedule_length": scenario["max_schedule_length"],
        }
    except (KeyError, OSError, ValueError, json.JSONDecodeError):
        return False
    return stored == payload.model_dump(mode="json")


@app.post("/api/scenario-packs", status_code=201, tags=["assessments"])
async def import_scenario_pack(payload: ScenarioPackImport) -> dict[str, Any]:
    _validate_imported_sql(payload)
    built_in = PROJECT_ROOT / "scenarios" / payload.id
    destination = IMPORTED_SCENARIOS / payload.id
    if built_in.exists():
        raise HTTPException(409, "A pack with this ID already exists.")
    if destination.exists():
        if _stored_pack_matches(destination, payload):
            return {"id": payload.id, "name": payload.name, "imported": True, "reused": True}
        raise HTTPException(409, "A different pack with this ID already exists. Choose a new ID.")
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "schema.sql").write_text(payload.schema_sql, encoding="utf-8")
    (destination / "seed.sql").write_text(payload.seed_sql, encoding="utf-8")
    if payload.repair_sql:
        (destination / "repair.sql").write_text(payload.repair_sql, encoding="utf-8")
    scenario = payload.model_dump(exclude={"schema_sql", "seed_sql", "repair_sql"})
    scenario.update(
        evaluator_label="unknown",
        schema_file="schema.sql",
        seed_file="seed.sql",
        repair_file="repair.sql",
        phases=[phase.model_dump() for phase in payload.phases],
        operations={key: value.model_dump() for key, value in payload.operations.items()},
        invariants=[invariant.model_dump() for invariant in payload.invariants],
        known_failing_schedule=[],
        permitted_repairs=[repair.model_dump() for repair in payload.permitted_repairs],
    )
    (destination / "scenario.json").write_text(json.dumps(scenario, indent=2), encoding="utf-8")
    return {"id": payload.id, "name": payload.name, "imported": True, "reused": False}


@app.get("/api/scenario-packs/template", tags=["assessments"])
async def scenario_pack_template() -> dict[str, Any]:
    path = PROJECT_ROOT / "examples" / "custom_assessment_pack.json"
    if not path.exists():
        raise HTTPException(404, "Template is unavailable.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/connections", tags=["connections"])
async def connections(request: Request) -> dict[str, Any]:
    configured = DatabaseManager()
    parsed = urlparse(configured.connection_url)
    saved = [value["public"] for value in _state_dict(request.app, "connections").values()]
    return {
        "configured": {
            "id": "configured",
            "label": "Configured demo sandbox",
            "host": parsed.hostname or "unix socket",
            "port": parsed.port or 5432,
            "database": parsed.path.lstrip("/"),
            "username": parsed.username,
            "status": "configured",
        },
        "ephemeral": saved,
    }


@app.post("/api/connections/test", tags=["connections"])
async def test_connection(payload: ConnectionTestRequest, request: Request) -> dict[str, Any]:
    if not payload.confirm_disposable:
        raise HTTPException(400, "Confirm that this is a disposable sandbox before testing.")
    host = payload.host.strip().lower()
    local_hosts = {"localhost", "127.0.0.1", "::1", "postgres"}
    configured_hosts = {
        item.strip().lower()
        for item in os.environ.get("CUTOVERPROOF_EXTERNAL_SANDBOX_HOSTS", "").split(",")
        if item.strip()
    }
    if host not in local_hosts | configured_hosts:
        raise HTTPException(400, "This host is not on the server's exact disposable-sandbox allowlist.")
    url = (
        f"postgresql://cutover:{quote_plus(payload.password)}@{host}:{payload.port}/"
        f"cutoverproof_sandbox?sslmode={payload.sslmode}&connect_timeout=5"
    )
    manager = DatabaseManager(url)
    rows = await asyncio.to_thread(
        manager.query_rows,
        "SELECT current_database() AS database, current_user AS username, "
        "current_setting('server_version') AS server_version",
    )
    connection_id = uuid.uuid4().hex
    public = {
        "id": connection_id,
        "label": f"{host}:{payload.port}",
        "host": host,
        "port": payload.port,
        "database": rows[0]["database"],
        "username": rows[0]["username"],
        "server_version": rows[0]["server_version"],
        "status": "verified",
    }
    _state_dict(request.app, "connections")[connection_id] = {"url": url, "public": public}
    return public


@app.get("/api/runs", tags=["runs"])
async def runs() -> list[dict[str, Any]]:
    return await asyncio.to_thread(list_runs)


@app.get("/api/runs/{run_id}", tags=["runs"])
async def run_detail(run_id: str) -> dict[str, Any]:
    return await asyncio.to_thread(get_run, run_id)


async def _run_job(app_instance: FastAPI, job_id: str, payload: dict[str, Any]) -> None:
    jobs: dict[str, dict[str, Any]] = app_instance.state.jobs
    jobs[job_id] = {
        **jobs[job_id],
        "status": "running",
        "progress": 6,
        "stage": "Starting the assessment",
    }
    try:
        connection_id = payload.pop("connection_id", None)
        connection_url = None
        if connection_id:
            record = _state_dict(app_instance, "connections").get(connection_id)
            if not record:
                raise ProductServiceError("The selected sandbox connection has expired. Test it again.")
            connection_url = record["url"]
        def update_progress(progress: int, stage: str) -> None:
            jobs[job_id] = {
                **jobs[job_id],
                "status": "running",
                "progress": progress,
                "stage": stage,
            }

        result = await asyncio.to_thread(execute_run, payload, connection_url, update_progress)
        if connection_url:
            _state_dict(app_instance, "run_connections")[result["run_id"]] = connection_url
        jobs[job_id] = {
            **jobs[job_id],
            "status": "completed",
            "progress": 100,
            "stage": "Assessment complete",
            "result": result,
        }
    except Exception as exc:  # Boundary: errors must never become product verdicts.
        logger.exception("Assessment job %s failed", job_id)
        jobs[job_id] = {
            **jobs[job_id],
            "status": "failed",
            "progress": 100,
            "stage": "Assessment stopped",
            "error": str(exc),
        }


@app.post(
    "/api/runs",
    response_model=JobAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["runs"],
)
async def create_run(payload: RunCreate, request: Request) -> JobAccepted:
    job_id = uuid.uuid4().hex
    jobs = _jobs(request)
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "stage": "Queued",
    }
    asyncio.create_task(_run_job(request.app, job_id, payload.model_dump()))
    return JobAccepted(job_id=job_id, status="queued")


@app.get("/api/jobs/{job_id}", tags=["runs"])
async def job_status(job_id: str, request: Request) -> dict[str, Any]:
    job = _jobs(request).get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@app.post("/api/runs/{run_id}/approve-repair", tags=["repairs"])
async def approve_repair(run_id: str, payload: RepairApproval, request: Request) -> dict[str, Any]:
    connection_url = _state_dict(request.app, "run_connections").get(run_id)
    return await asyncio.to_thread(approve_and_replay, run_id, payload.reviewer_name, connection_url)


@app.get("/api/benchmarks", tags=["benchmarks"])
async def benchmarks() -> dict[str, Any]:
    return await asyncio.to_thread(benchmark_summary)


@app.get("/api/evidence/{run_id}", response_class=FileResponse, tags=["evidence"])
async def evidence(run_id: str) -> FileResponse:
    path = await asyncio.to_thread(evidence_path, run_id)
    return FileResponse(path, media_type="text/html")


@app.get("/api", tags=["system"])
async def api_index() -> dict[str, str]:
    return {"name": "CutoverProof API", "docs": "/docs"}


if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="portal")
else:

    @app.get("/")
    async def frontend_not_built() -> dict[str, str]:
        return {
            "status": "frontend_not_built",
            "detail": "Build web/ to serve the customer portal from this process.",
        }


def main() -> None:
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8766")),
        reload=False,
    )


if __name__ == "__main__":
    main()
