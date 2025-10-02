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

    # --- THIS IS THE CRITICAL FIX ---
    # This line tells Django that for any URL that isn't 'admin/', 'analytics/', 
    # or the firebase file, it should look for a match inside your 
    # OrderMaster app's urls.py file. This is what makes '/dashboard/' work.
    path('', include('OrderMaster.urls')),
    # ------------------------------------

    # This handles the analytics page separately.
    path('analytics/', include('OrderMaster.scripts.analytics_views.urlpatterns')),
    
    # This correctly serves the Firebase service worker file from the root.
    path(
        "firebase-messaging-sw.js",
        TemplateView.as_view(
            template_name="firebase-messaging-sw.js",
            content_type="application/javascript",
        ),
        name="firebase-messaging-sw.js",
    ),
]

# This is for serving images during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
