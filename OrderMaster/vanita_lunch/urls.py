# vanita_lunch/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.template.loader import render_to_string

# This view dynamically serves the Firebase Service Worker JS file
def firebase_messaging_sw(request):
    """
    Renders the firebase-messaging-sw.js file with the correct context.
    This ensures your Firebase config is correctly injected.
    """
    return HttpResponse(
        render_to_string('firebase-messaging-sw.js'),
        content_type='application/javascript'
    )

urlpatterns = [
    # URL for the service worker
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw'),
    
    # Include your app's URLs
    path('', include('OrderMaster.urls')),
]

# This is for serving media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
