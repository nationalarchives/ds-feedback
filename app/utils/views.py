from uuid import UUID

from django.db import models


def is_valid_uuid(uuid: str, version=4):
    """
    Validate if a string is a valid UUID
    """

    try:
        UUID(uuid, version=version)
        return True
    except ValueError:
        return False


def get_admin_viewname(
    *, app_label: str, model: models.Model, view_name: str
) -> str:
    """
    Gets an admin viewname for a model
    """
    return f"admin:{app_label}_{model._meta.model_name}_{view_name}"
