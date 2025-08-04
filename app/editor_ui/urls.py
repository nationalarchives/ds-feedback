from django.urls import path

from app.editor_ui.views import index

urlpatterns = [
    path("", index, name="index"),
]
