from django.core.exceptions import ImproperlyConfigured
from django.views.generic import CreateView


class BaseCreateView(CreateView):
    """
    Base class for creation views in the editor UI.

    - Ensures that an 'object_name' attribute is set as a string on the subclass.
    - Adds 'object_name' to the template context for use in generic create templates.
    - Raises ImproperlyConfigured if 'object_name' is not set or not a string.
    - Uses a default template 'editor_ui/create.html'.
    """
    object_name = None
    template_name = "editor_ui/create.html"

    def get_context_data(self, **kwargs):
        if not self.object_name or type(self.object_name) is not str:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires 'object_name' to be set as a string."
            )
        context = super().get_context_data(**kwargs)
        context["object_name"] = self.object_name
        return context
