from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from pulseops_api.api.deps import TenantContext, require_min_role
from pulseops_api.core.security import Role
from pulseops_api.db.session import get_db
from pulseops_api.schemas.api import ExecutiveSummaryRead
from pulseops_api.services.executive import build_executive_summary

router = APIRouter(tags=["executive"])


@router.get("/executive/summary", response_model=ExecutiveSummaryRead)
def get_executive_summary(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.VIEWER)),
):
    return ExecutiveSummaryRead.model_validate(
        build_executive_summary(db, tenant.organization_id)
    )
