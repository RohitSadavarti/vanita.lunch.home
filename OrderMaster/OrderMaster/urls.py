# OrderMaster/OrderMaster/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Admin URLs
    path('', views.customer_order_view, name='customer_order'),
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.order_management_view, name='order_management'),
    path('menu/', views.menu_management_view, name='menu_management'),
    path('menu/edit/<int:item_id>/', views.edit_menu_item_view, name='edit_menu_item'),
    path('menu/delete/<int:item_id>/', views.delete_menu_item_view, name='delete_menu_item'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('settings/', views.settings_view, name='settings'),
    
    
    # API URLs
    path('api/update-order-status/', views.update_order_status, name='update_order_status'),
    path('api/menu-items/', views.api_menu_items, name='api_menu_items'),
    path('api/place-order/', views.api_place_order, name='api_place_order'),

    # Customer-facing URL (previously 'order/')
    path('customer-order/', views.customer_home, name='customer_home'),
    path('api/get_orders/', views.get_orders_api, name='get_orders_api'),
    
    # The line below was causing the error and has been removed, as the view no longer exists.
    # path('api/order-status/<str:order_id>/', views.api_order_status, name='api_order_status'),
]

