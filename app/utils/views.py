from django.db import models


def get_admin_viewname(
    app_label: str, model: models.Model, view_name: str
) -> str:
    """
    Gets an admin viewname for a model
    """
    return f"admin:{app_label}_{model._meta.model_name}_{view_name}"
