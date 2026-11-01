from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from pulseops_api.api.deps import TenantContext, require_app_request, require_min_role
from pulseops_api.core.config import get_settings
from pulseops_api.core.security import Role
from pulseops_api.db.session import get_db
from pulseops_api.repositories.repositories import create_audit_event, get_or_create_dataset
from pulseops_api.schemas.api import DatasetBundleRead, DatasetRead
from pulseops_api.services.csv_ingestion import parse_csv_bundle
from pulseops_api.services.ingestion import parse_operational_json

router = APIRouter(prefix="/datasets", tags=["datasets"])


async def _read_limited(file: UploadFile) -> bytes:
    max_bytes = get_settings().max_upload_bytes
    raw = await file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise HTTPException(413, f"{file.filename or 'file'} exceeds upload limit")
    return raw


@router.post(
    "",
    response_model=DatasetRead,
    status_code=201,
    dependencies=[Depends(require_app_request)],
)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.ANALYST)),
):
    raw_bytes = await _read_limited(file)
    try:
        raw = raw_bytes.decode("utf-8")
        parse_operational_json(raw)
    except (UnicodeDecodeError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(422, f"invalid operational dataset: {exc}") from exc
    content_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    dataset, duplicate = get_or_create_dataset(
        db,
        organization_id=tenant.organization_id,
        content_sha256=content_sha256,
        filename=file.filename or "dataset.json",
        status="validated",
        raw_payload=raw,
    )
    create_audit_event(
        db, action="dataset.uploaded", organization_id=tenant.organization_id,
        user_id=tenant.user.id, resource_type="dataset", resource_id=dataset.id,
        details={"filename": dataset.filename, "format": "json", "duplicate": duplicate},
    )
    db.commit()
    return dataset


@router.post(
    "/csv-bundle",
    response_model=DatasetBundleRead,
    status_code=201,
    dependencies=[Depends(require_app_request)],
)
async def upload_csv_bundle(
    equipment: UploadFile = File(...),
    availability: UploadFile = File(...),
    appointments: UploadFile = File(...),
    executions: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.ANALYST)),
):
    """Normalize four operational CSV exports into the OIE canonical model."""
    equipment_bytes = await _read_limited(equipment)
    availability_bytes = await _read_limited(availability)
    appointments_bytes = await _read_limited(appointments)
    executions_bytes = await _read_limited(executions)

    try:
        result = parse_csv_bundle(
            equipment_csv=equipment_bytes,
            availability_csv=availability_bytes,
            appointments_csv=appointments_bytes,
            executions_csv=executions_bytes,
        )
    except ValueError as exc:
        raise HTTPException(422, f"invalid CSV bundle: {exc}") from exc

    digest = hashlib.sha256()
    for raw in (
        equipment_bytes,
        availability_bytes,
        appointments_bytes,
        executions_bytes,
    ):
        digest.update(raw)

    dataset, duplicate = get_or_create_dataset(
        db,
        organization_id=tenant.organization_id,
        content_sha256=digest.hexdigest(),
        filename="operational-csv-bundle",
        status="validated",
        raw_payload=result.canonical_json(),
    )
    report = result.report.to_dict()
    create_audit_event(
        db, action="dataset.csv_bundle_uploaded", organization_id=tenant.organization_id,
        user_id=tenant.user.id, resource_type="dataset", resource_id=dataset.id,
        details={
            "rows_received": report["rows_received"],
            "rows_valid": report["rows_valid"],
            "rows_rejected": report["rows_rejected"],
            "duplicate": duplicate,
        },
    )
    db.commit()
    return {"dataset": dataset, "quality": report, "duplicate": duplicate}
