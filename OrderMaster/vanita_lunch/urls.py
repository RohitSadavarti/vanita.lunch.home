# OrderMaster/vanita_lunch/urls.py
"""
URL configuration for vanita_lunch project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    # This correctly points to the analytics script.
    path('analytics/', include('OrderMaster.scripts.analytics_views')),
    
    # This serves the Firebase service worker file, which is required for notifications.
    path(
        "firebase-messaging-sw.js",
        TemplateView.as_view(
            template_name="firebase-messaging-sw.js",
            content_type="application/javascript",
        ),
        name="firebase-messaging-sw.js",
    ),

    # --- THIS IS THE CRITICAL FIX ---
    # This single line includes all of your application's main URLs 
    # (login, dashboard, orders, etc.) and makes them accessible from the root.
    path('', include('OrderMaster.urls')),
    # -----------------------------------
]

# This is necessary for serving media files (like menu item images) during development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
