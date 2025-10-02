# vanita_lunch/urls.py

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.template.loader import render_to_string

# This view dynamically serves the Firebase Service Worker JS file
def firebase_messaging_sw(request):
    """
    Renders the firebase-messaging-sw.js file.
    This is the correct way to serve the service worker in Django.
    """
    try:
        # We will create this template in the next step
        return HttpResponse(
            render_to_string('OrderMaster/firebase-messaging-sw.js'),
            content_type='application/javascript'
        )
    except Exception as e:
        # This helps debug if the template is not found
        print(f"Error rendering service worker: {e}")
        return HttpResponse(status=500)

urlpatterns = [
    # This URL is critical for Firebase to work
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw'),
    
    # This includes all your other app URLs like the dashboard, login, etc.
    path('', include('OrderMaster.urls')),
]

# This is for serving media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
