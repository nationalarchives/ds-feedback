from django.urls import path, include

from . import views
from app.dashboard import urls as dashboard_urls

urlpatterns = [
    path("", views.index, name="index"),
    path("cookies/", views.cookies, name="cookies"),
]
