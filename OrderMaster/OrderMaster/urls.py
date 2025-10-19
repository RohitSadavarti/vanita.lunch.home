# OrderMaster/OrderMaster/urls.py
from django.urls import path

from . import views

urlpatterns = [
    # Customer URL
    path('order/', views.customer_order_view, name='customer_order'),

    # Admin Auth URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Admin Panel URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.order_management_view, name='order_management'),
    path('menu/', views.menu_management_view, name='menu_management'),
    path('menu/edit/<int:item_id>/', views.edit_menu_item_view, name='edit_menu_item'),
    path('menu/delete/<int:item_id>/', views.delete_menu_item_view, name='delete_menu_item'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('settings/', views.settings_view, name='settings'),

    # --- Added/Corrected URLs for 404 errors ---
    path('firebase-messaging-sw.js', views.firebase_messaging_sw, name='firebase-messaging-sw'),
    path('api/subscribe-topic/', views.subscribe_to_topic, name='subscribe_to_topic'),
    path('analytics/data/', views.analytics_data_api, name='analytics_data_api'), # Added for analytics

    # API URLs (Keep existing + add generic menu item API for Flutter/JS)
    path('api/get_orders/', views.get_orders_api, name='get_orders_api'),
    path('api/update_order_status/', views.update_order_status, name='update_order_status'),
    path('api/menu-items/', views.api_menu_items, name='api_menu_items'), # List/Create Menu Items
    path('api/menu-items/<int:item_id>/', views.api_menu_item_detail, name='api_menu_item_detail'), # Get/Update/Delete single item
    path('api/place-order/', views.api_place_order, name='api_place_order'), # Customer order placement
]