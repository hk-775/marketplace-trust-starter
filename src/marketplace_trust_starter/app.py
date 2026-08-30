"""FastAPI application and local web experience."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from marketplace_trust_starter import __version__
from marketplace_trust_starter.models import (
    AssessmentResponse,
    AuditResponse,
    CaseStatus,
    CaseUpdateRequest,
    ContentAssessmentRequest,
    CoordinatedAbuseRequest,
    PaginatedAssessments,
    PaginatedCases,
    PolicyRule,
    PolicyUpdateRequest,
    ProfileAssessmentRequest,
    ResetRequest,
    ResetResponse,
    ReviewCase,
)
from marketplace_trust_starter.service import TrustSafetyService
from marketplace_trust_starter.store import Store, utc_now


def create_app(database_path: str | Path | None = None) -> FastAPI:
    source_root = Path(__file__).resolve().parents[2]
    default_database_path = (
        source_root / "data" / "marketplace_trust_starter.db"
        if (source_root / "pyproject.toml").exists()
        else Path.cwd() / "data" / "marketplace_trust_starter.db"
    )
    resolved_database_path = Path(
        database_path or os.getenv("MTS_DATABASE_PATH", str(default_database_path))
    )
    store = Store(resolved_database_path)
    store.initialize()
    service = TrustSafetyService(store)
    web_root = Path(__file__).resolve().parent / "web"

    app = FastAPI(
        title="Marketplace Trust Starter API",
        version=__version__,
        summary="Explainable trust-and-safety assessments with real human-review state",
        description=(
            "A local-first reference API. Scores prioritize review; they never prove abuse "
            "or authorize irreversible enforcement."
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    app.state.store = store
    app.state.service = service
    app.mount("/assets", StaticFiles(directory=web_root / "assets"), name="assets")

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    def landing_page() -> FileResponse:
        return FileResponse(web_root / "index.html")

    @app.get("/dashboard", include_in_schema=False)
    @app.get("/dashboard/", include_in_schema=False)
    @app.get("/dashboard.html", include_in_schema=False)
    def dashboard_page() -> FileResponse:
        return FileResponse(web_root / "dashboard.html")

    @app.get("/architecture", include_in_schema=False)
    @app.get("/architecture/", include_in_schema=False)
    @app.get("/architecture.html", include_in_schema=False)
    def architecture_page() -> FileResponse:
        return FileResponse(web_root / "architecture.html")

    @app.get("/health", include_in_schema=False)
    @app.get("/api/v1/health", tags=["system"])
    def health() -> dict[str, Any]:
        counts = store.counts()
        return {
            "status": "ok",
            "service": "marketplace-trust-starter",
            "version": __version__,
            "time": utc_now(),
            "mode": "local_seeded_demo",
            "storage": "sqlite",
            "external_network_calls": False,
            "counts": counts,
            "ethical_boundaries": {
                "protected_attribute_inference": "prohibited",
                "face_or_attractiveness_scoring": "prohibited",
                "irreversible_automated_enforcement": "not_implemented",
            },
        }

    @app.post(
        "/api/v1/assess/profile",
        response_model=AssessmentResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["assessments"],
    )
    def assess_profile_endpoint(
        payload: ProfileAssessmentRequest,
    ) -> AssessmentResponse:
        return service.assess_profile(payload)

    @app.post(
        "/api/v1/assess/content",
        response_model=AssessmentResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["assessments"],
    )
    def assess_content_endpoint(
        payload: ContentAssessmentRequest,
    ) -> AssessmentResponse:
        return service.assess_content(payload)

    @app.post(
        "/api/v1/assess/coordinated-abuse",
        response_model=AssessmentResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["assessments"],
    )
    def assess_coordination_endpoint(
        payload: CoordinatedAbuseRequest,
    ) -> AssessmentResponse:
        return service.assess_coordination(payload)

    @app.get(
        "/api/v1/assessments",
        response_model=PaginatedAssessments,
        tags=["assessments"],
    )
    def list_assessments(
        limit: Annotated[int, Query(ge=1, le=250)] = 50,
    ) -> PaginatedAssessments:
        items, total = store.list_assessments(limit=limit)
        return PaginatedAssessments(items=items, total=total)

    @app.get("/api/v1/cases", response_model=PaginatedCases, tags=["human review"])
    def list_cases(
        case_status: Annotated[CaseStatus | None, Query(alias="status")] = None,
        limit: Annotated[int, Query(ge=1, le=250)] = 100,
    ) -> PaginatedCases:
        items, total = store.list_cases(status=case_status, limit=limit)
        return PaginatedCases(items=items, total=total)

    @app.get(
        "/api/v1/cases/{case_id}",
        response_model=ReviewCase,
        tags=["human review"],
    )
    def get_case(case_id: str) -> ReviewCase:
        try:
            return store.get_case(case_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="case not found") from exc

    @app.patch(
        "/api/v1/cases/{case_id}",
        response_model=ReviewCase,
        tags=["human review"],
    )
    def update_case(case_id: str, payload: CaseUpdateRequest) -> ReviewCase:
        try:
            return store.update_case(case_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="case not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/metrics", tags=["operations"])
    def metrics() -> dict[str, Any]:
        return store.metrics()

    @app.get("/api/v1/insights", tags=["operations"])
    def insights() -> dict[str, Any]:
        return store.insights()

    @app.get(
        "/api/v1/policies",
        response_model=list[PolicyRule],
        tags=["policy"],
    )
    def list_policies() -> list[PolicyRule]:
        return store.list_policies()

    @app.patch(
        "/api/v1/policies/{policy_id}",
        response_model=PolicyRule,
        tags=["policy"],
    )
    def update_policy(
        policy_id: str,
        payload: PolicyUpdateRequest,
    ) -> PolicyRule:
        try:
            return store.update_policy(policy_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="policy not found") from exc
        except PermissionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/audit", response_model=AuditResponse, tags=["audit"])
    def audit(
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> AuditResponse:
        items, total, chain_valid = store.audit_events(limit=limit)
        return AuditResponse(items=items, total=total, chain_valid=chain_valid)

    @app.get("/api/v1/demo/scenarios", tags=["demo"])
    def demo_scenarios() -> dict[str, Any]:
        return {"items": service.demo_scenarios()}

    @app.post(
        "/api/v1/demo/scenarios/{scenario_id}",
        response_model=AssessmentResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["demo"],
    )
    def run_demo_scenario(scenario_id: str) -> AssessmentResponse:
        try:
            return service.run_demo_scenario(scenario_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="demo scenario not found") from exc

    @app.post(
        "/api/v1/demo/reset",
        response_model=ResetResponse,
        tags=["demo"],
    )
    def reset_demo(payload: ResetRequest) -> ResetResponse:
        return ResetResponse.model_validate(store.reset_demo(actor=payload.actor))

    return app
