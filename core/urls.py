from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('courts.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('management/', include('management_portal.urls')),
    
    # Authentication URLs (if using Django's built-in auth views)
    path('auth/', include('django.contrib.auth.urls')),
    
    # Optional: Custom error pages
]

# Serve static/media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Optional: Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass