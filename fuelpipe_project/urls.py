# fuelpipe_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from pipes.views import custom_admin_dashboard

# Custom admin URL patterns
admin.site.site_header = "SP Auto Parts Solution - Admin"
admin.site.site_title = "SP Auto Parts Solution"
admin.site.index_title = "Welcome to SP Auto Parts Solution Admin"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pipes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
