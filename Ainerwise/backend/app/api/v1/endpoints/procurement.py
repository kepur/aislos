"""AI Procurement Engine endpoints.

Phase 1 / C01: portal policy.
Phase 1 / C03: projects, facts and file attachments.
Phase 1 / C04: BOQ versions, review and freeze.
Phase 1 / C05: AI analyze and confidence gate.
Phase 1 / C06: package generation and partner matching.
Phase 1 / C07: commercial snapshot and RFQ publish.
"""
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DB
from app.core.portal_context import PortalContextDep
from app.models.procurement import BoqVersion, ProcurementProjectFact
from app.schemas.portal_policy import PortalPolicyPublic
from app.schemas.procurement import (
    AnalyzeRequest,
    AnalyzeResponse,
    BoqDraftCreate,
    BoqFreezeRequest,
    BoqReviewSubmit,
    ProcurementFactPatch,
    ProcurementFactRead,
    ProcurementFileAttach,
    ProcurementFileRead,
    ProcurementProjectCreate,
    ProcurementProjectList,
    PackageGenerateResponse,
    ProcurementPackagePatch,
    ProcurementPackageRead,
    PublishRfqCustomerResponse,
    PublishRfqRequest,
    ProcurementProjectRead,
    TransferPortalRequest,
)
from app.services.audit import append_audit_event
from app.services.event_bus import EventType, emit_event
from app.services.procurement_ai import ProcurementAIError, run_project_analyze
from app.services.procurement_boq import (
    ProcurementBoqError,
    create_draft_boq,
    freeze_boq_version,
    get_project_boq_version,
    list_items_for_version,
    list_options_for_items,
    list_solution_plans,
    serialize_boq_public,
    submit_boq_for_review,
)
from app.services.procurement_facts import (
    ProcurementFactError,
    get_fact_for_project,
    list_facts,
    patch_fact,
)
from app.services.procurement_packages import (
    ProcurementPackageError,
    generate_packages_from_frozen_boq,
    get_package_for_project,
    list_package_items,
    list_packages_for_project,
    match_partner_candidates,
    patch_package,
    serialize_package,
)
from app.services.procurement_rfq import (
    CommercialSnapshotImmutableError,
    ProcurementRfqError,
    portal_brand_payload,
    publish_package_rfq,
    serialize_rfq_for_customer,
    serialize_rfq_for_supplier,
)
from app.services.procurement_projects import (
    ProcurementProjectError,
    attach_file,
    create_project,
    get_project_by_id,
    get_project_for_user,
    list_projects,
    transfer_portal,
)

router = APIRouter(prefix="/procurement", tags=["procurement"])


@router.get("/portal-policy", response_model=PortalPolicyPublic)
async def get_portal_policy(ctx: PortalContextDep) -> PortalPolicyPublic:
    """Return the customer-visible active policy of the trusted Portal."""
    return PortalPolicyPublic.from_policy(ctx.policy)


@router.post("/projects", response_model=ProcurementProjectRead, status_code=status.HTTP_201_CREATED)
async def create_procurement_project(
    body: ProcurementProjectCreate,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
) -> ProcurementProjectRead:
    try:
        project, facts = await create_project(
            db,
            user=user,
            ctx=ctx,
            project_type=body.project_type,
            title=body.title,
            description=body.description,
            region=body.region,
            country=body.country,
            city=body.city,
        )
    except ProcurementProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key=ctx.portal_key,
        action="procurement.project.created",
        entity_type="procurement_project",
        entity_id=project.id,
        after={
            "id": str(project.id),
            "portal_key": project.portal_key,
            "project_type": project.project_type,
            "status": project.status,
            "facts_initialized": len(facts),
        },
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_PROJECT_CREATED,
        {
            "project_id": str(project.id),
            "portal_key": project.portal_key,
            "project_type": project.project_type,
            "owner_user_id": str(user.id),
        },
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    for fact in facts:
        await append_audit_event(
            db,
            actor_type="system",
            portal_key=ctx.portal_key,
            action="procurement.fact.created",
            entity_type="procurement_fact",
            entity_id=fact.id,
            after={"template_key": fact.template_key, "project_id": str(project.id)},
            source="procurement.api",
            require_procurement_action=True,
        )

    await db.commit()
    await db.refresh(project)
    return ProcurementProjectRead.model_validate(project)


@router.get("/projects", response_model=ProcurementProjectList)
async def list_procurement_projects(
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
    skip: int = 0,
    limit: int = 50,
) -> ProcurementProjectList:
    items, total = await list_projects(
        db, user=user, portal_key=ctx.portal_key, skip=skip, limit=limit
    )
    return ProcurementProjectList(
        items=[ProcurementProjectRead.model_validate(p) for p in items],
        total=total,
    )


@router.get("/projects/{project_id}", response_model=ProcurementProjectRead)
async def get_procurement_project(
    project_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
) -> ProcurementProjectRead:
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProcurementProjectRead.model_validate(project)


@router.post("/projects/{project_id}/transfer-portal", response_model=ProcurementProjectRead)
async def transfer_procurement_project_portal(
    project_id: uuid.UUID,
    body: TransferPortalRequest,
    db: DB,
    admin: AdminUser,
    ctx: PortalContextDep,
) -> ProcurementProjectRead:
    project = await get_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        project, before, after = await transfer_portal(
            db,
            project=project,
            target_portal_key=body.target_portal_key.strip().lower(),
            reason=body.reason,
        )
    except ProcurementProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=admin.id,
        portal_key=ctx.portal_key,
        action="procurement.project.portal_transferred",
        entity_type="procurement_project",
        entity_id=project.id,
        before=before,
        after=after,
        reason=body.reason,
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_PROJECT_PORTAL_TRANSFERRED,
        {
            "project_id": str(project.id),
            "from_portal_key": before["portal_key"],
            "to_portal_key": after["portal_key"],
            "reason": body.reason,
            "admin_user_id": str(admin.id),
        },
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    await db.commit()
    await db.refresh(project)
    return ProcurementProjectRead.model_validate(project)


@router.post(
    "/projects/{project_id}/files",
    response_model=ProcurementFileRead,
    status_code=status.HTTP_201_CREATED,
)
async def attach_procurement_project_file(
    project_id: uuid.UUID,
    body: ProcurementFileAttach,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
) -> ProcurementFileRead:
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    asset = await attach_file(
        db,
        project=project,
        user=user,
        original_name=body.original_name,
        storage_path=body.storage_path,
        mime_type=body.mime_type,
        size_bytes=body.size_bytes,
        file_type=body.file_type,
    )
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key=ctx.portal_key,
        action="procurement.file.attached",
        entity_type="procurement_project",
        entity_id=project.id,
        after={
            "file_asset_id": str(asset.id),
            "original_name": asset.original_name,
            "storage_path": asset.storage_path,
        },
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_FILE_ATTACHED,
        {
            "project_id": str(project.id),
            "file_asset_id": str(asset.id),
            "portal_key": project.portal_key,
        },
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    await db.commit()
    await db.refresh(asset)
    return ProcurementFileRead.model_validate(asset)


@router.get("/projects/{project_id}/facts", response_model=list[ProcurementFactRead])
async def list_procurement_project_facts(
    project_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
) -> list[ProcurementFactRead]:
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    facts = await list_facts(db, project.id)
    return [ProcurementFactRead.model_validate(f) for f in facts]


@router.patch("/projects/{project_id}/facts/{fact_id}", response_model=ProcurementFactRead)
async def patch_procurement_project_fact(
    project_id: uuid.UUID,
    fact_id: uuid.UUID,
    body: ProcurementFactPatch,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
) -> ProcurementFactRead:
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    fact = await get_fact_for_project(db, project_id, fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="Fact not found")

    fields_set = body.model_fields_set
    try:
        fact, before, after, confirmed_now = await patch_fact(
            db,
            fact,
            value_json=body.value_json,
            value_provided="value_json" in fields_set,
            user_confirmed=body.user_confirmed,
            assumption=body.assumption,
            assumption_provided="assumption" in fields_set,
        )
    except ProcurementFactError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    action = "procurement.fact.confirmed" if confirmed_now else "procurement.fact.updated"
    event_type = (
        EventType.PROCUREMENT_FACT_CONFIRMED
        if confirmed_now
        else EventType.PROCUREMENT_FACT_UPDATED
    )
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key=ctx.portal_key,
        action=action,
        entity_type="procurement_fact",
        entity_id=fact.id,
        before=before,
        after=after,
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        event_type,
        {
            "fact_id": str(fact.id),
            "project_id": str(project.id),
            "template_key": fact.template_key,
            "user_confirmed": fact.user_confirmed,
        },
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    await db.commit()
    await db.refresh(fact)
    return ProcurementFactRead.model_validate(fact)


@router.post("/projects/{project_id}/analyze", response_model=AnalyzeResponse)
async def analyze_procurement_project(
    project_id: uuid.UUID,
    body: AnalyzeRequest,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
):
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key=ctx.portal_key,
        action="procurement.ai.started",
        entity_type="procurement_project",
        entity_id=project.id,
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_AI_STARTED,
        {"project_id": str(project.id), "portal_key": ctx.portal_key},
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )

    try:
        result = await run_project_analyze(
            db,
            project=project,
            user=user,
            portal_key=ctx.portal_key,
            test_scenario=body.test_scenario,
        )
    except ProcurementAIError as exc:
        await append_audit_event(
            db,
            actor_type="system",
            portal_key=ctx.portal_key,
            action="procurement.ai.failed",
            entity_type="procurement_project",
            entity_id=project.id,
            reason=str(exc),
            source="procurement.api",
            require_procurement_action=True,
        )
        await emit_event(
            db,
            EventType.PROCUREMENT_AI_FAILED,
            {"project_id": str(project.id), "error": str(exc)},
            aggregate_type="procurement_project",
            aggregate_id=project.id,
        )
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await append_audit_event(
        db,
        actor_type="agent",
        agent_slug="procurement-agent",
        portal_key=ctx.portal_key,
        action="procurement.ai.completed",
        entity_type="procurement_project",
        entity_id=project.id,
        after={
            "status": result["status"],
            "overall_confidence": result["overall_confidence"],
            "run_id": result["run_id"],
        },
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_AI_COMPLETED,
        {
            "project_id": str(project.id),
            "status": result["status"],
            "overall_confidence": result["overall_confidence"],
        },
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    await db.commit()
    await db.refresh(project)
    return AnalyzeResponse.model_validate(result)


async def _resolve_boq_version(
    db: DB, project, body_version_id: uuid.UUID | None
) -> BoqVersion:
    if body_version_id:
        version = await db.get(BoqVersion, body_version_id)
        if version is None or version.project_id != project.id:
            raise HTTPException(status_code=404, detail="BOQ version not found")
        return version
    version = await get_project_boq_version(db, project)
    if version is None:
        raise HTTPException(status_code=404, detail="No BOQ version for project")
    return version


@router.get("/projects/{project_id}/boq")
async def get_procurement_project_boq(
    project_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
):
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    version = await get_project_boq_version(db, project)
    if version is None:
        raise HTTPException(status_code=404, detail="No BOQ version for project")
    items = await list_items_for_version(db, version.id)
    options = await list_options_for_items(db, [i.id for i in items])
    plans = await list_solution_plans(db, version.id)
    return serialize_boq_public(version, items, options, plans)


@router.post(
    "/projects/{project_id}/boq/draft",
    status_code=status.HTTP_201_CREATED,
)
async def create_procurement_boq_draft(
    project_id: uuid.UUID,
    body: BoqDraftCreate,
    db: DB,
    admin: AdminUser,
    ctx: PortalContextDep,
):
    """Admin/test helper to seed a draft BOQ without running AI (C04)."""
    project = await get_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    facts_result = await db.execute(
        select(ProcurementProjectFact).where(ProcurementProjectFact.project_id == project.id)
    )
    facts = list(facts_result.scalars().all())
    try:
        version, items, options, plans = await create_draft_boq(
            db,
            project=project,
            facts=facts,
            items_payload=[i.model_dump(mode="json") for i in body.items],
            disclaimer=body.disclaimer,
            source_run_id=body.source_run_id,
        )
    except ProcurementBoqError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=admin.id,
        portal_key=ctx.portal_key,
        action="procurement.boq.generated",
        entity_type="procurement_project",
        entity_id=project.id,
        after={"boq_version_id": str(version.id), "version": version.version},
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_BOQ_GENERATED,
        {"project_id": str(project.id), "boq_version_id": str(version.id)},
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    await db.commit()
    return serialize_boq_public(version, items, options, plans)


@router.post("/projects/{project_id}/boq/review")
async def submit_procurement_boq_review(
    project_id: uuid.UUID,
    body: BoqReviewSubmit,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
):
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    version = await _resolve_boq_version(db, project, body.boq_version_id)
    try:
        review = await submit_boq_for_review(db, project=project, version=version, user=user)
    except ProcurementBoqError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key=ctx.portal_key,
        action="procurement.boq.reviewed",
        entity_type="procurement_project",
        entity_id=project.id,
        after={"boq_version_id": str(version.id), "review_id": str(review.id)},
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_BOQ_REVIEWED,
        {
            "project_id": str(project.id),
            "boq_version_id": str(version.id),
            "review_id": str(review.id),
        },
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    await db.commit()
    return {"review_id": str(review.id), "status": review.status, "boq_version_id": str(version.id)}


@router.post("/projects/{project_id}/boq/freeze")
async def freeze_procurement_boq(
    project_id: uuid.UUID,
    body: BoqFreezeRequest,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
):
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    version = await _resolve_boq_version(db, project, body.boq_version_id)
    try:
        version = await freeze_boq_version(db, project=project, version=version, user=user)
    except ProcurementBoqError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key=ctx.portal_key,
        action="procurement.boq.frozen",
        entity_type="procurement_project",
        entity_id=project.id,
        after={"boq_version_id": str(version.id), "version": version.version},
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_BOQ_FROZEN,
        {"project_id": str(project.id), "boq_version_id": str(version.id)},
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    await db.commit()
    await db.refresh(project)
    items = await list_items_for_version(db, version.id)
    options = await list_options_for_items(db, [i.id for i in items])
    plans = await list_solution_plans(db, version.id)
    return {
        "project_status": project.status,
        "boq": serialize_boq_public(version, items, options, plans),
    }


@router.get(
    "/projects/{project_id}/packages",
    response_model=list[ProcurementPackageRead],
)
async def list_procurement_packages(
    project_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
):
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    packages = await list_packages_for_project(db, project.id)
    if not packages:
        return []

    package_ids = [p.id for p in packages]
    items = await list_package_items(db, package_ids)
    payload = []
    for pkg in packages:
        candidates = await match_partner_candidates(
            db,
            trade=pkg.trade,
            commercial_type=pkg.commercial_type,
            region=pkg.region,
        )
        payload.append(serialize_package(pkg, items, candidates))
    return [ProcurementPackageRead.model_validate(p) for p in payload]


@router.post(
    "/projects/{project_id}/packages/generate",
    response_model=PackageGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_procurement_packages(
    project_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
):
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    version = await get_project_boq_version(db, project)
    try:
        packages, package_items, partner_map = await generate_packages_from_frozen_boq(
            db, project=project, boq_version=version
        )
    except ProcurementPackageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key=ctx.portal_key,
        action="procurement.package.generated",
        entity_type="procurement_project",
        entity_id=project.id,
        after={
            "package_count": len(packages),
            "boq_version_id": str(version.id) if version else None,
        },
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_PACKAGES_GENERATED,
        {
            "project_id": str(project.id),
            "boq_version_id": str(version.id) if version else None,
            "package_count": len(packages),
        },
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    await db.commit()
    await db.refresh(project)

    payload = [
        serialize_package(
            pkg,
            package_items,
            partner_map.get(pkg.id, []),
        )
        for pkg in packages
    ]
    return PackageGenerateResponse(
        project_status=project.status,
        packages=[ProcurementPackageRead.model_validate(p) for p in payload],
    )


@router.patch(
    "/projects/{project_id}/packages/{package_id}",
    response_model=ProcurementPackageRead,
)
async def patch_procurement_package(
    project_id: uuid.UUID,
    package_id: uuid.UUID,
    body: ProcurementPackagePatch,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
):
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    package = await get_package_for_project(db, project_id, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")

    fields_set = body.model_fields_set
    try:
        package, before, after = await patch_package(
            db,
            package=package,
            title=body.title,
            title_provided="title" in fields_set,
            procurement_mode=body.procurement_mode,
            mode_provided="procurement_mode" in fields_set,
            status=body.status,
            status_provided="status" in fields_set,
        )
    except ProcurementPackageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key=ctx.portal_key,
        action="procurement.package.updated",
        entity_type="procurement_package",
        entity_id=package.id,
        before=before,
        after=after,
        source="procurement.api",
        require_procurement_action=True,
    )
    await emit_event(
        db,
        EventType.PROCUREMENT_PACKAGE_UPDATED,
        {
            "project_id": str(project.id),
            "package_id": str(package.id),
            "status": package.status,
        },
        aggregate_type="procurement_project",
        aggregate_id=project.id,
    )
    await db.commit()
    await db.refresh(package)

    items = await list_package_items(db, [package.id])
    candidates = await match_partner_candidates(
        db,
        trade=package.trade,
        commercial_type=package.commercial_type,
        region=package.region,
    )
    return ProcurementPackageRead.model_validate(
        serialize_package(package, items, candidates)
    )


@router.post(
    "/projects/{project_id}/packages/{package_id}/publish-rfq",
    response_model=PublishRfqCustomerResponse,
)
async def publish_procurement_package_rfq(
    project_id: uuid.UUID,
    package_id: uuid.UUID,
    body: PublishRfqRequest,
    db: DB,
    user: CurrentUser,
    ctx: PortalContextDep,
):
    project = await get_project_for_user(
        db, project_id=project_id, user=user, portal_key=ctx.portal_key
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    package = await get_package_for_project(db, project_id, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")

    terms = {
        "currency": body.currency,
        "exchange_rate_snapshot_json": body.exchange_rate_snapshot_json,
        "tax_mode": body.tax_mode,
        "margin_rule_json": body.margin_rule_json,
        "service_fee_json": body.service_fee_json,
        "warranty_rule_json": body.warranty_rule_json,
        "delivery_region_json": body.delivery_region_json,
        "quote_expiry": body.quote_expiry,
        "payment_terms_json": body.payment_terms_json,
    }
    try:
        snapshot, rfq, created = await publish_package_rfq(
            db,
            project=project,
            package=package,
            user_id=user.id,
            terms=terms,
            bid_deadline=body.bid_deadline,
        )
    except CommercialSnapshotImmutableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ProcurementRfqError as exc:
        message = str(exc)
        if "commercial field" in message or "missing or empty" in message:
            raise HTTPException(status_code=422, detail=message) from exc
        if "status" in message or "frozen" in message or "packaged" in message:
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    brand = portal_brand_payload(project)
    if created:
        await append_audit_event(
            db,
            actor_type="user",
            actor_user_id=user.id,
            portal_key=ctx.portal_key,
            action="procurement.commercial_snapshot.created",
            entity_type="commercial_snapshot",
            entity_id=snapshot.id,
            after={"terms_hash": snapshot.terms_hash, "package_id": str(package.id)},
            source="procurement.api",
            require_procurement_action=True,
        )
        await emit_event(
            db,
            EventType.PROCUREMENT_COMMERCIAL_SNAPSHOT_CREATED,
            {
                **brand,
                "project_id": str(project.id),
                "package_id": str(package.id),
                "snapshot_id": str(snapshot.id),
                "terms_hash": snapshot.terms_hash,
            },
            aggregate_type="procurement_project",
            aggregate_id=project.id,
        )
        await append_audit_event(
            db,
            actor_type="user",
            actor_user_id=user.id,
            portal_key=ctx.portal_key,
            action="procurement.rfq.published",
            entity_type="rfq",
            entity_id=rfq.id,
            after={
                "package_id": str(package.id),
                "revision": package.revision,
                "portal_key": project.portal_key,
            },
            source="procurement.api",
            require_procurement_action=True,
        )
        await emit_event(
            db,
            EventType.PROCUREMENT_RFQ_PUBLISHED,
            {
                **brand,
                "project_id": str(project.id),
                "package_id": str(package.id),
                "rfq_id": str(rfq.id),
                "snapshot_id": str(snapshot.id),
                "revision": package.revision,
            },
            aggregate_type="procurement_project",
            aggregate_id=project.id,
        )

    await db.commit()
    await db.refresh(project)
    await db.refresh(package)

    customer_rfq = serialize_rfq_for_customer(rfq, snapshot, project)
    supplier_rfq = serialize_rfq_for_supplier(rfq, snapshot)
    return PublishRfqCustomerResponse(
        project_status=project.status,
        package_status=package.status,
        created=created,
        rfq=customer_rfq,
        supplier_view=supplier_rfq,
    )
