# vanita_lunch/urls.py

from django.contrib import admin
from django.urls import path, include
from .views import firebase_messaging_sw # Import the new view

urlpatterns = [
    # Path for the service worker
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw.js'),

    # Include your app's URLs
    path('', include('OrderMaster.urls')),
]
