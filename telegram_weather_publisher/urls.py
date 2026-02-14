from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

from weatherbot.views import home, internal_publish


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("health/", healthcheck, name="healthcheck"),
    path(
        "internal/publish/<str:forecast_type>/",
        internal_publish,
        name="internal_publish",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
