# vanita_lunch/urls.py

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # This line tells Django to use the URLs defined in your OrderMaster app
    path('', include('OrderMaster.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
