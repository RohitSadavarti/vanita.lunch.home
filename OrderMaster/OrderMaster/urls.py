# OrderMaster/OrderMaster/urls.py

from django.urls import path, include, re_path
from django.http import HttpResponse
from django.template.loader import render_to_string
from . import views
from .scripts.analytics_views import urlpatterns as analytics_urlpatterns

# This view dynamically serves the Firebase Service Worker JS file
def firebase_messaging_sw(request):
    try:
        return HttpResponse(
            render_to_string('firebase-messaging-sw.js'),
            content_type='application/javascript'
        )
    except Exception as e:
        print(f"FATAL: Could not render service worker. Error: {e}")
        return HttpResponse(status=500)

urlpatterns = [
    # Customer URL - Changed from root to /order/
    path('order/', views.customer_order_view, name='customer_order'),

    # Admin Auth URLs - Root path now goes to login
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'), # Keep this for explicit /login/ URL
    path('logout/', views.logout_view, name='logout'),

    # Admin Panel URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.order_management_view, name='order_management'),
    path('menu/', views.menu_management_view, name='menu_management'),
    path('menu/edit/<int:item_id>/', views.edit_menu_item_view, name='edit_menu_item'),
    path('menu/delete/<int:item_id>/', views.delete_menu_item_view, name='delete_menu_item'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('settings/', views.settings_view, name='settings'),

    # API URLs
    path('api/get_orders/', views.get_orders_api, name='get_orders_api'),
    path('api/update_order_status/', views.update_order_status, name='update_order_status'),

    # You might need these APIs depending on which customer view/js you are using
    # path('api/menu-items/', views.api_menu_items, name='api_menu_items'),
    # path('api/place-order/', views.api_place_order, name='api_place_order'),
]


