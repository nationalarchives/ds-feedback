from django.urls import include, path

app_name = "editor_ui"

urlpatterns = [
    path(
        "",
        include("app.editor_ui.urls.project_urls", namespace="projects"),
    ),
    path(
        "api-keys/",
        include("app.editor_ui.urls.api_key_urls", namespace="api_keys"),
    ),
]
