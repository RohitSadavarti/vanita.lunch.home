# OrderMaster/vanita_lunch/urls.py
"""
URL configuration for vanita_lunch project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView # Import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- THIS IS THE CRITICAL FIX ---
    # This line correctly includes all the URLs from your OrderMaster app,
    # such as the dashboard, orders, menu, and all the APIs.
    path('', include('OrderMaster.urls')),
    # ------------------------------------

    # This handles the analytics page separately
    path('analytics/', include('OrderMaster.scripts.analytics_views.urlpatterns')),
    
    # --- FIX FOR FIREBASE SERVICE WORKER ---
    # This serves the firebase-messaging-sw.js file from the root directory,
    # which is required by Firebase for background notifications to work.
    path(
        "firebase-messaging-sw.js",
        TemplateView.as_view(
            template_name="firebase-messaging-sw.js",
            content_type="application/javascript",
        ),
        name="firebase-messaging-sw.js",
    ),
    # -----------------------------------------
]

# This is important for serving images during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
