"""
URL configuration for trapick project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include("trapickapp.urls")),
    
    # Serve React app for all non-static, non-api routes
    re_path(r'^(?!static/|api/|admin/).*', TemplateView.as_view(template_name='index.html')),
]

# This will serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)