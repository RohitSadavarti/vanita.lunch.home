# OrderMaster/OrderMaster/urls.py
import sys
import os
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.template.loader import render_to_string
from . import views

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from OrderMaster import views
from OrderMaster.scripts.analytics_views import urlpatterns as analytics_urlpatterns

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
    # Admin Auth URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin Pages
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.order_management_view, name='order_management'),
    path('menu/', views.menu_management_view, name='menu_management'),
    path('menu/edit/<int:item_id>/', views.edit_menu_item_view, name='edit_menu_item'),
    path('menu/delete/<int:item_id>/', views.delete_menu_item_view, name='delete_menu_item'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('settings/', views.settings_view, name='settings'),
    path('take-order/', views.take_order_view, name='take_order'),
    path('invoice/<int:order_id>/', views.invoice_view, name='invoice_view'),
    path('api/analytics/', views.analytics_api_view, name='api_analytics'),
    path('api/all-orders/', views.get_all_orders_api, name='api_all_orders'),
    path('api/create-manual-order/', views.create_manual_order, name='api_create_manual_order'),
    

    # Customer Page
    path('customer/', views.customer_order_view, name='customer_order'),
    
    # Firebase
    path('firebase-messaging-sw.js', views.firebase_messaging_sw, name='firebase-messaging-sw'),

    # --- APIs for both Web & Flutter ---
    path('api/get-orders/', views.get_orders_api, name='get_orders_api'), # For Web Kanban
    path('api/get-pending-orders/', views.get_pending_orders, name='get_pending_orders'), # For Flutter App
    path('api/update-order-status/', views.update_order_status, name='update_order_status'),
    path('api/handle-order-action/', views.handle_order_action, name='handle_order_action'),
    path('api/menu-items/', views.api_menu_items, name='api_menu_items'),
    path('api/menu-items/<int:item_id>/', views.api_menu_item_detail, name='api_menu_item_detail'),
    path('api/place-order/', views.api_place_order, name='api_place_order'),
    path('api/analytics-data/', views.analytics_data_api, name='analytics_data_api'),
    path('api/subscribe-topic/', views.subscribe_to_topic, name='subscribe_to_topic'),
]


