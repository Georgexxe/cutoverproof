"""Validated request and response contracts for the CutoverProof web API."""

from typing import Dict, List, Literal

from pydantic import BaseModel, Field, field_validator


class RunCreate(BaseModel):
    """Starts one bounded assessment against a checked-in scenario."""

    scenario_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,79}$")
    approach: Literal["specialised_agent", "one_shot_llm", "random_heuristic"] = (
        "specialised_agent"
    )
    budget: int = Field(default=4, ge=1, le=8)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    model_name: str | None = Field(default=None, min_length=1, max_length=120)
    request_repair: bool = True
    connection_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")

    @field_validator("model_name")
    @classmethod
    def normalize_model_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class RepairApproval(BaseModel):
    """Records the named human who approves a bounded sandbox replay."""

    reviewer_name: str = Field(min_length=2, max_length=80)

    @field_validator("reviewer_name")
    @classmethod
    def normalize_reviewer_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("Reviewer name must contain at least two characters")
        return normalized


class JobAccepted(BaseModel):
    job_id: str
    status: Literal["queued"]


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=1, max_length=256)


class ConnectionTestRequest(BaseModel):
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=5432, ge=1, le=65535)
    database: Literal["cutoverproof_sandbox"] = "cutoverproof_sandbox"
    username: Literal["cutover"] = "cutover"
    password: str = Field(min_length=1, max_length=256)
    sslmode: Literal["prefer", "require", "disable"] = "prefer"
    confirm_disposable: bool


class PackPhase(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=4, max_length=500)


class PackOperation(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    phase: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    actor: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=4, max_length=500)
    sql: str = Field(min_length=1, max_length=30_000)


class PackInvariant(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=4, max_length=500)
    sql: str = Field(min_length=1, max_length=10_000)


class PackRepair(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=1000)
    patch_type: str = Field(min_length=3, max_length=80)


class ScenarioPackImport(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=1000)
    schema_sql: str = Field(min_length=1, max_length=50_000)
    seed_sql: str = Field(min_length=1, max_length=50_000)
    phases: List[PackPhase] = Field(min_length=2, max_length=10)
    operations: Dict[str, PackOperation] = Field(min_length=2, max_length=30)
    invariants: List[PackInvariant] = Field(min_length=1, max_length=10)
    permitted_repairs: List[PackRepair] = Field(default_factory=list, max_length=1)
    repair_sql: str | None = Field(default=None, max_length=50_000)
    max_candidates: int = Field(default=4, ge=1, le=8)
    max_schedule_length: int = Field(default=6, ge=2, le=12)
