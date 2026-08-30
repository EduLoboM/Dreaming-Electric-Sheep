"""
Django WSGI benchmark application (default stack, stripped middleware).
Runs on Granian with --interface wsgi.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import django
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import path
from jinja2 import Template
from perf.compare.mock_db import (
    clamp_queries,
    get_single_world,
    get_multiple_worlds,
    get_fortunes_sorted,
    update_multiple_worlds,
    FORTUNES_HTML_TEMPLATE,
)

_JINJA_TEMPLATE = Template(FORTUNES_HTML_TEMPLATE, autoescape=True)


def plaintext_view(request):
    return HttpResponse("Hello, World!", content_type="text/plain")


def json_view(request):
    return JsonResponse({"message": "Hello, World!"})


def single_query_view(request):
    return JsonResponse(get_single_world())


def multiple_queries_view(request):
    queries = request.GET.get("queries")
    n = clamp_queries(queries)
    return JsonResponse(get_multiple_worlds(n), safe=False)


def fortunes_view(request):
    items = get_fortunes_sorted()
    return HttpResponse(_JINJA_TEMPLATE.render(fortunes=items), content_type="text/html")


def data_updates_view(request):
    queries = request.GET.get("queries")
    n = clamp_queries(queries)
    return JsonResponse(update_multiple_worlds(n), safe=False)


urlpatterns = [
    path("plaintext", plaintext_view),
    path("json", json_view),
    path("db", single_query_view),
    path("queries", multiple_queries_view),
    path("fortunes", fortunes_view),
    path("updates", data_updates_view),
]

if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY="secret-bench-key-not-for-production",
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=["*"],
        MIDDLEWARE=[],
    )
    django.setup()

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
