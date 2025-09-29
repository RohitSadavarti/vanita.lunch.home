# vanita_lunch/urls.py

from django.urls import path, include
from OrderMaster.views import firebase_messaging_sw

urlpatterns = [
    # This path correctly serves the Firebase service worker
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw.js'),
    
    # This is the ONLY include you need for your app
    path('', include('OrderMaster.urls')),
]
