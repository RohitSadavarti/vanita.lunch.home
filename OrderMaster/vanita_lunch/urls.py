# OrderMaster/vanita_lunch/urls.py
"""
URL configuration for vanita_lunch project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# --- THIS IS THE CORRECTED PART ---
# We now correctly import the analytics URLs from the scripts folder.
from OrderMaster.scripts import analytics_views
# ------------------------------------


urlpatterns = [
    path('admin/', admin.site.urls),

    # --- AND WE ADD THE CORRECT PATH HERE ---
    # This tells Django to look inside analytics_views.py for any URL starting with 'analytics/'
    path('analytics/', include(analytics_views.urlpatterns)),
    # ----------------------------------------
    
    # This includes all the main app URLs (dashboard, orders, etc.)
    path('', include('OrderMaster.urls')),
]

# This is important for serving images during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
