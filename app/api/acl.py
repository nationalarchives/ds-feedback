import logging

from app.projects.models import Project
from app.users.models import User

from .models import ProjectAPIAccess
from .types import APIRole

logger = logging.getLogger(__name__)


def can_access_project_with_role(
    *, user: User, project: Project, allowed_roles: list[APIRole]
) -> bool:
    return (
        user.is_superuser
        or ProjectAPIAccess.objects.filter(
            grantee=user,
            project=project,
            role__in=allowed_roles,
        )
        .active()
        .exists()
    )


def can_access_any_project_with_role(
    *, user: User, allowed_roles: list[APIRole]
) -> bool:
    return (
        user.is_superuser
        or ProjectAPIAccess.objects.filter(grantee=user, role__in=allowed_roles)
        .active()
        .exists()
    )


def get_accessible_projects_with_role(
    *, user: User, allowed_roles: list[APIRole]
) -> list[Project]:
    """
    Returns the list of projects which the user has access to with the given roles
    """
    if user.is_superuser:
        raise ValueError("This function is not intended for super users")

    return (
        access.project
        for access in ProjectAPIAccess.objects.filter(
            grantee=user,
            role__in=allowed_roles,
        ).select_related("project")
    )
