from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from pulseops_api.api.deps import get_current_user, require_app_request
from pulseops_api.db.session import get_db
from pulseops_api.models.db_models import User
from pulseops_api.repositories.repositories import create_audit_event, create_organization_with_owner
from pulseops_api.schemas.api import OrganizationCreate, OrganizationRead

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post(
    "",
    response_model=OrganizationRead,
    status_code=201,
    dependencies=[Depends(require_app_request)],
)
def post_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    organization = create_organization_with_owner(db, name=payload.name, user_id=user.id)
    create_audit_event(
        db, action="organization.created", organization_id=organization.id,
        user_id=user.id, resource_type="organization", resource_id=organization.id,
        details={"name": organization.name},
    )
    db.commit()
    return organization
