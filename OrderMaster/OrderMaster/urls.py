# OrderMaster/OrderMaster/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Existing admin URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('orders/', views.order_management, name='order_management'),
    path('menu/', views.menu_management, name='menu_management'),
    path('menu/edit/<int:item_id>/', views.edit_menu_item, name='edit_menu_item'),
    path('menu/delete/<int:item_id>/', views.delete_menu_item, name='delete_menu_item'),
    path('api/update-order-status/', views.update_order_status, name='update_order_status'),
    
    # Add these two new lines for Analytics and Settings
    path('analytics/', views.analytics, name='analytics'),
    path('settings/', views.settings, name='settings'),
    # New customer URLs
    path('order/', views.customer_home, name='customer_home'),
    path('api/menu-items/', views.api_menu_items, name='api_menu_items'),
    path('api/place-order/', views.api_place_order, name='api_place_order'),
    path('api/order-status/<str:order_id>/', views.api_order_status, name='api_order_status'),
]

