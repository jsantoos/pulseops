from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pulseops_api.api.deps import get_current_user, require_app_request
from pulseops_api.core.config import get_settings
from pulseops_api.core.security import (
    Role,
    hash_password,
    new_session_token,
    session_token_hash,
    validate_email,
    verify_password,
)
from pulseops_api.db.session import get_db
from pulseops_api.models.db_models import User
from pulseops_api.repositories.repositories import (
    create_membership,
    create_organization,
    create_user,
    create_user_session,
    delete_user_session,
    get_memberships_for_user,
    get_user_by_email,
    list_organizations,
    user_count,
)
from pulseops_api.schemas.api import (
    AuthRead,
    BootstrapCreate,
    BootstrapStatusRead,
    LoginCreate,
    MembershipRead,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_read(db: Session, user: User) -> UserRead:
    memberships = get_memberships_for_user(db, user.id)
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        memberships=[
            MembershipRead(
                organization_id=item.organization_id,
                organization_name=item.organization.name,
                role=item.role,
            )
            for item in memberships
        ],
    )


def _create_session(response: Response, db: Session, user_id: str) -> None:
    settings = get_settings()
    token = new_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.auth_session_minutes
    )
    create_user_session(
        db,
        token_hash=session_token_hash(token),
        user_id=user_id,
        expires_at=expires_at,
    )
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.auth_session_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.get("/bootstrap-status", response_model=BootstrapStatusRead)
def bootstrap_status(db: Session = Depends(get_db)) -> BootstrapStatusRead:
    return BootstrapStatusRead(bootstrap_required=user_count(db) == 0)


@router.post(
    "/bootstrap",
    response_model=AuthRead,
    status_code=201,
    dependencies=[Depends(require_app_request)],
)
def bootstrap(
    payload: BootstrapCreate,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthRead:
    if get_settings().environment.lower() == "production":
        raise HTTPException(404, "not found")
    if user_count(db) != 0:
        raise HTTPException(409, "bootstrap already completed")

    organizations = list_organizations(db)
    if len(organizations) == 1:
        organization = organizations[0]
    elif len(organizations) == 0:
        if not payload.organization_name:
            raise HTTPException(422, "organization_name is required for first setup")
        organization = create_organization(db, payload.organization_name)
    else:
        raise HTTPException(
            409,
            "multiple organizations exist; bootstrap requires manual membership migration",
        )

    try:
        email = validate_email(payload.email)
        user = create_user(
            db,
            email=email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
        )
        create_membership(
            db,
            user_id=user.id,
            organization_id=organization.id,
            role=Role.OWNER,
        )
        db.commit()
        db.refresh(user)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "user already exists") from exc

    _create_session(response, db, user.id)
    return AuthRead(user=_user_read(db, user))


@router.post(
    "/login",
    response_model=AuthRead,
    dependencies=[Depends(require_app_request)],
)
def login(
    payload: LoginCreate,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthRead:
    try:
        email = validate_email(payload.email)
    except ValueError as exc:
        raise HTTPException(401, "invalid credentials") from exc
    user = get_user_by_email(db, email)
    if user is None or not user.is_active or not verify_password(
        payload.password, user.password_hash
    ):
        raise HTTPException(401, "invalid credentials")
    _create_session(response, db, user.id)
    return AuthRead(user=_user_read(db, user))


@router.post("/logout", status_code=204, dependencies=[Depends(require_app_request)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    settings = get_settings()
    token = request.cookies.get(settings.auth_cookie_name)
    if token:
        delete_user_session(db, session_token_hash(token))
    response.delete_cookie(settings.auth_cookie_name, path="/")


@router.get("/me", response_model=AuthRead)
def me(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AuthRead:
    return AuthRead(user=_user_read(db, user))
