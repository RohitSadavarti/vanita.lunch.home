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
    # Firebase Service Worker URL (CRITICAL - MUST BE AT THE ROOT)
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw'),

    # Admin URLs
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.order_management_view, name='order_management'),
    path('menu/', views.menu_management_view, name='menu_management'),
    path('menu/delete/<int:item_id>/', views.delete_menu_item_view, name='delete_menu_item'),
    path('api/pending-orders/', views.get_pending_orders, name='get_pending_orders'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('analytics/', include(analytics_urlpatterns)),
    
    path('settings/', views.settings_view, name='settings'),
    path('api/subscribe-topic/', views.subscribe_to_topic, name='subscribe_topic'),
    path('api/analytics/', views.analytics_api_view, name='analytics_api'),
    path('api/handle-order-action/', views.handle_order_action, name='handle_order_action'),
    
    # Other API URLs
    path('api/menu-item/<int:item_id>/', views.api_menu_item_detail, name='api_menu_item_detail'),
    path('api/update-order-status/', views.update_order_status, name='update_order_status'),
    path('api/get_orders/', views.get_orders_api, name='get_orders_api'),
    path('api/menu-items/', views.api_menu_items, name='api_menu_items'),
    path('api/place-order/', views.api_place_order, name='api_place_order'),

    # Customer-facing URL
    path('customer-order/', views.customer_order_view, name='customer_home'),
    path('take-order/', views.take_order_view, name='take_order'),
    path('api/create-manual-order/', views.create_manual_order, name='create_manual_order'),
    path('invoice/<int:order_id>/', views.generate_invoice_view, name='generate_invoice'),
]


