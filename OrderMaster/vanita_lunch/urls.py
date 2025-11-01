# vanita_lunch/urls.py

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- FIX: Point explicitly to the nested urls.py file ---
    path('', include('OrderMaster.OrderMaster.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
