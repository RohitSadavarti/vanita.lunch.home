# OrderMaster/OrderMaster/urls.py
from django.urls import path
from . import views

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

