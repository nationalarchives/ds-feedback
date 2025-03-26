from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from app.projects.models import Project 



@login_required(login_url="admin:login")
def projects_index(request):

    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    projects_qs = Project.objects.select_related("owned_by").owned_by(request.user).order_by("name", "-pk")

    paginator = Paginator(projects_qs, 1)
    page = paginator.page(page)

    projects = [
        {
            "name": project.name,
            "domain": project.domain,
            "owned_by": project.owned_by.get_display_name(),
            "url": "#",
        }
        for project in page.object_list
    ]
    context = {"projects": projects, "pagination": pagination_context(path=request.path, page=page)}
    return render(request, "dashboard/projects.html", context)