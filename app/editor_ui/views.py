from django.shortcuts import render


def index(request):
    return render(request, "editor_ui/index.html")
