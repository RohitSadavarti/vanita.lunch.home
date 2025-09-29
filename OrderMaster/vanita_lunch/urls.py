# vanita_lunch/urls.py

from django.urls import path, include
from .views import firebase_messaging_sw # Corrected import

urlpatterns = [
    # This path correctly serves the Firebase service worker
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw.js'),
    
    # This is the ONLY include you need for your app
    path('', include('OrderMaster.urls')),
]
