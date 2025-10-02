# OrderMaster/OrderMaster/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('orders/', views.order_management_view, name='order_management'),
    path('menu/', views.menu_management_view, name='menu_management'),
    path('menu/edit/<int:item_id>/', views.edit_menu_item, name='edit_menu_item'),
    path('menu/delete/<int:item_id>/', views.delete_menu_item, name='delete_menu_item'),
    
    # --- THIS IS THE CORRECTED PART ---
    # The line pointing to the deleted 'analytics_view' has been removed.
    # ------------------------------------

    # API URLs
    path('api/create-order/', views.create_order_api, name='create_order_api'),
    path('api/get-orders/', views.get_orders_api, name='get_orders_api'),
    path('api/update-order-status/', views.update_order_status, name='update_order_status'),
    path('api/handle-order-action/', views.handle_order_action, name='handle_order_action'),
    path('api/acknowledge-order/', views.acknowledge_order, name='acknowledge_order'),
]
