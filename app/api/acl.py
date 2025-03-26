from collections.abc import Sequence
import logging
from django.db.models import QuerySet
from django.utils import timezone
from .models import ProjectAPIAccess
from .types import APIRole
from app.projects.models import Project
from app.users.models import User

logger = logging.getLogger(__name__)


def can_user_submit_response(*, user: User, project: Project) -> bool:
    return user.is_superuser or _active_api_access_queryset(
        user=user, project=project, role=APIRole.RESPONSE_SUBMITTER
    ).exists()


def can_user_read_project_data(*, user: User, project: Project) -> bool:
    return user.is_superuser or _active_api_access_queryset(
        user=user, project=project, role=APIRole.READ_ONLY
    ).exists()


def can_user_view_feedback_forms(*, user: User, project: Project) -> bool:
    return user.is_superuser or _active_api_access_queryset(
        user=user, project=project, roles=[APIRole.READ_ONLY, APIRole.RESPONSE_SUBMITTER]
    ).exists()


def _active_api_access_queryset(
    *, user: User, project: Project, roles: Sequence[APIRole]
) -> QuerySet:
    try:
        roles = [APIRole(role) for role in roles]
    except ValueError:
        logger.exception(
            "Invalid API role: %s for user=%s and project=%s",
            role,
            user.id,
            project.id,
        )
        return ProjectAPIAccess.objects.none()

    return ProjectAPIAccess.objects.filter(
        grantee=user, project=project, role__in=roles
    ).active()