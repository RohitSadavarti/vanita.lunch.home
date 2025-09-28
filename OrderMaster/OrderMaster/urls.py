# OrderMaster/OrderMaster/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Admin URLs
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.order_management_view, name='order_management'),
    path('menu/', views.menu_management_view, name='menu_management'),
    
    # API URLs
    path('api/menu-item/<int:item_id>/', views.api_menu_item_detail, name='api_menu_item_detail'),
    path('api/update-order-status/', views.update_order_status, name='update_order_status'),
    path('api/get_orders/', views.get_orders_api, name='get_orders_api'),
    
    # ... (any other urls you have)
]
