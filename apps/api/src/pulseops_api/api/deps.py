from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from pulseops_api.core.config import get_settings
from pulseops_api.core.security import ROLE_ORDER, Role, session_token_hash
from pulseops_api.db.session import get_db
from pulseops_api.models.db_models import OrganizationMembership, User
from pulseops_api.repositories.repositories import (
    get_memberships_for_user,
    get_user_session,
)


@dataclass(frozen=True, slots=True)
class TenantContext:
    user: User
    membership: OrganizationMembership

    @property
    def organization_id(self) -> str:
        return self.membership.organization_id

    @property
    def role(self) -> Role:
        return Role(self.membership.role)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise HTTPException(401, "authentication required")

    session = get_user_session(db, session_token_hash(token))
    if session is None:
        raise HTTPException(401, "invalid session")
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        raise HTTPException(401, "session expired")

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, "user unavailable")
    return user


def get_tenant_context(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    organization_id: str | None = Header(
        default=None, alias="X-PulseOps-Organization"
    ),
) -> TenantContext:
    memberships = get_memberships_for_user(db, user.id)
    if not memberships:
        raise HTTPException(403, "user has no organization membership")

    if organization_id:
        membership = next(
            (item for item in memberships if item.organization_id == organization_id),
            None,
        )
        if membership is None:
            raise HTTPException(403, "organization access denied")
        return TenantContext(user=user, membership=membership)

    if len(memberships) == 1:
        return TenantContext(user=user, membership=memberships[0])

    raise HTTPException(400, "X-PulseOps-Organization header is required")


def require_min_role(minimum: Role):
    def dependency(context: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if ROLE_ORDER[context.role] < ROLE_ORDER[minimum]:
            raise HTTPException(403, "insufficient role")
        return context

    return dependency


def require_app_request(
    request: Request,
    request_marker: str | None = Header(default=None, alias="X-PulseOps-Request"),
) -> None:
    if request_marker != "web":
        raise HTTPException(403, "missing application request marker")

    origin = request.headers.get("origin")
    if origin and origin not in get_settings().allowed_frontend_origins:
        raise HTTPException(403, "request origin is not allowed")
