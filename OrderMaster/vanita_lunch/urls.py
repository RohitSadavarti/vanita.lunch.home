from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.decorators.cache import never_cache

@never_cache
def firebase_sw(request):
    js_code = """
importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-messaging.js');

const firebaseConfig = {
  apiKey: "AIzaSyBnYYq_K3TL9MxyKaCNPkB8SRqAIucF0rI",
  authDomain: "vanita-lunch-home.firebaseapp.com",
  projectId: "vanita-lunch-home",
  storageBucket: "vanita-lunch-home.firebasestorage.app",
  messagingSenderId: "86193565341",
  appId: "1:86193565341:web:b9c234bda59b37ee366e74"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('Background message received:', payload);
  const title = payload.notification.title;
  const options = {
    body: payload.notification.body,
    icon: '/static/favicon.ico'
  };
  self.registration.showNotification(title, options);
});
"""
    return HttpResponse(js_code, content_type='application/javascript')

urlpatterns = [
    path('firebase-messaging-sw.js', firebase_sw, name='firebase-sw'),
    path('', include('OrderMaster.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
