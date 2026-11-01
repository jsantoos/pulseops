from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from pulseops_api.api.deps import TenantContext, require_min_role
from pulseops_api.core.security import Role
from pulseops_api.db.session import get_db
from pulseops_api.repositories.repositories import list_audit_events
from pulseops_api.schemas.api import AuditEventRead

router = APIRouter(prefix="/audit-events", tags=["audit"])


@router.get("", response_model=list[AuditEventRead])
def get_audit_events(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.ADMIN)),
):
    return list_audit_events(db, tenant.organization_id, limit=limit)
