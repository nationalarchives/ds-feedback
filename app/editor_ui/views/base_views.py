from django.core.exceptions import ImproperlyConfigured
from django.views.generic import CreateView, UpdateView


class BaseCreateView(CreateView):
    """
    Base class for creation views in the editor UI.

    - Ensures that an 'model_display_name' attribute is set as a string on the subclass.
    - Adds 'model_display_name' to the template context for use in generic create templates.
    - Raises ImproperlyConfigured if 'model_display_name' is not set or not a string.
    - Uses a default template 'editor_ui/generic_creation_template.html'.
    """

    model_display_name = None
    template_name = "editor_ui/generic_creation_template.html"

    def get_context_data(self, **kwargs):
        if (
            not self.model_display_name
            or type(self.model_display_name) is not str
        ):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires 'model_display_name' to be set as a string."
            )
        context = super().get_context_data(**kwargs)
        context["model_display_name"] = self.model_display_name
        return context


class CustomUpdateView(UpdateView):
    """
    Base class for update views in the editor UI.

    - Ensures that an 'model_display_name' attribute is set as a string on the subclass.
    - Adds 'model_display_name' to the template context for use in generic update templates.
    - Raises ImproperlyConfigured if 'model_display_name' is not set or not a string.
    - Uses a default template 'editor_ui/generic_update_template.html'.
    """

    model_display_name = None
    template_name = "editor_ui/generic_update_template.html"

    def get_context_data(self, **kwargs):
        if (
            not self.model_display_name
            or type(self.model_display_name) is not str
        ):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires 'model_display_name' to be set as a string."
            )
        context = super().get_context_data(**kwargs)
        context["model_display_name"] = self.model_display_name
        return context
