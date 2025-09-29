# vanita_lunch/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Service worker must be at root level
    path('firebase-messaging-sw.js', 
         TemplateView.as_view(
             template_name='firebase-messaging-sw.js',
             content_type='application/javascript'
         ), 
         name='firebase-messaging-sw'),
    
    # Include your app's URLs
    path('', include('OrderMaster.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
