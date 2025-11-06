"""
URL configuration for trapick project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView 
from django.views.static import serve
import os

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include("trapickapp.urls")),  # API routes under /api/
    
    # Serve React app for all other routes
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)