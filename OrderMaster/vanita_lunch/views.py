from django.http import HttpResponse
from django.views.decorators.cache import cache_control
import os

@cache_control(max_age=60 * 60 * 24 * 30) # Cache for 30 days
def firebase_messaging_sw(request):
    try:
        # This path correctly finds the service worker in your app's static folder
        sw_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), # Navigates to the project's BASE_DIR
            'OrderMaster',
            'static',
            'firebase-messaging-sw.js'
        )
        with open(sw_path, 'r') as f:
            return HttpResponse(f.read(), content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse("Service worker not found.", status=404, content_type='application/javascript')
