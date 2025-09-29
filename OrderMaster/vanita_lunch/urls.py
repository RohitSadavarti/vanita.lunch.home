from django.contrib import admin
from django.urls import path, include
# --- Import the new view from its new location ---
from .views import firebase_messaging_sw

urlpatterns = [
    path('admin/', admin.site.urls),
    # This URL pattern for the service worker is now correct
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw'),
    # This includes all the URLs from your OrderMaster app
    path('', include('OrderMaster.urls')),
]
