from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def page_not_found(request: HttpRequest, exception) -> HttpResponse:
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request: HttpRequest, reason: str = '') -> HttpResponse:
    return render(request, 'core/403csrf.html')


def permission_denied(request: HttpRequest, exception) -> HttpResponse:
    return render(request, 'core/403.html', status=403)


def server_error(request: HttpRequest) -> HttpResponse:
    return render(request, 'core/500.html', status=500)
