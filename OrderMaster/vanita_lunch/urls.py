# vanita_lunch/urls.py
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # ... other urls
    path('firebase-messaging-sw.js', (TemplateView.as_view(
        template_name="firebase-messaging-sw.js",
        content_type='application/javascript',
    )), name='firebase-messaging-sw.js'),
    path('', include('OrderMaster.urls')),
]
