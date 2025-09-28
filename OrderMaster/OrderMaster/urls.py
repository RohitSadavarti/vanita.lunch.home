# OrderMaster/OrderMaster/urls.py

from django.urls import path, include
from . import views
from django.contrib import admin
from .views import firebase_messaging_sw
urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw'),
    path('', views.login_view, name='login'),
    path('', include('OrderMaster.urls')),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.order_management_view, name='order_management'),
    path('menu/', views.menu_management_view, name='menu_management'),
    path('menu/delete/<int:item_id>/', views.delete_menu_item_view, name='delete_menu_item'),
    
    # --- ADDED MISSING URLS ---
    path('analytics/', views.analytics_view, name='analytics'),
    path('settings/', views.settings_view, name='settings'),
    
    # API URLs
    path('api/menu-item/<int:item_id>/', views.api_menu_item_detail, name='api_menu_item_detail'),
    path('api/update-order-status/', views.update_order_status, name='update_order_status'),
    path('api/get_orders/', views.get_orders_api, name='get_orders_api'),
    path('api/menu-items/', views.api_menu_items, name='api_menu_items'),
    path('api/place-order/', views.api_place_order, name='api_place_order'),

    # Customer-facing URL
    path('customer-order/', views.customer_home, name='customer_home'),
]

