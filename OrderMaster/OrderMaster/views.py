# =================================================================================
# IMPORTS
# =================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from .models import MenuItem, Order, VlhAdmin
from .forms import MenuItemForm
from datetime import datetime, timedelta
import json
import uuid
from decimal import Decimal
import logging

# Set up logging
logger = logging.getLogger(__name__)

# =================================================================================
# DECORATORS & AUTHENTICATION
# =================================================================================

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.warning(request, 'You must be logged in to view this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def login_view(request):
    if request.session.get('is_authenticated'):
        return redirect('dashboard')
    if request.method == 'POST':
        mobile = request.POST.get('username')
        password = request.POST.get('password')
        try:
            admin_user = VlhAdmin.objects.get(mobile=mobile)
            if admin_user.check_password(password):
                request.session['is_authenticated'] = True
                request.session['admin_mobile'] = admin_user.mobile
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid mobile number or password.')
        except VlhAdmin.DoesNotExist:
            messages.error(request, 'Invalid mobile number or password.')
    return render(request, 'OrderMaster/login.html')

@admin_required
def logout_view(request):
    request.session.flush()
    messages.info(request, 'You have been successfully logged out.')
    return redirect('login')

# =================================================================================
# ADMIN PAGES
# =================================================================================

@admin_required
def dashboard_view(request):
    """Renders the main admin dashboard page."""
    context = {
        'total_orders': Order.objects.count(),
        'preparing_orders_count': Order.objects.filter(order_status='open').count(),
        'ready_orders_count': Order.objects.filter(order_status='ready').count(),
        'menu_items_count': MenuItem.objects.count(),
        'recent_orders': Order.objects.order_by('-created_at')[:5],
    }
    return render(request, 'OrderMaster/dashboard.html', context)

@admin_required
def order_management_view(request):
    """Displays and manages current orders based on order_status."""
    context = {
        'preparing_orders': Order.objects.filter(order_status='open').order_by('created_at'),
        'ready_orders': Order.objects.filter(order_status='ready').order_by('-created_at'),
    }
    return render(request, 'OrderMaster/order_management.html', context)

@admin_required
def menu_management_view(request):
    """Handles adding and displaying menu items."""
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item added successfully!')
            return redirect('menu_management')
    else:
        form = MenuItemForm()
        
    context = {
        'menu_items': MenuItem.objects.all().order_by('-created_at'),
        'item_form': form
    }
    return render(request, 'OrderMaster/menu_management.html', context)

@admin_required
@require_POST
def delete_menu_item_view(request, item_id):
    """Handles deleting a menu item."""
    item = get_object_or_404(MenuItem, id=item_id)
    item.delete()
    messages.success(request, 'Menu item deleted successfully!')
    return redirect('menu_management')

@admin_required
def analytics_view(request):
    """Renders the analytics page."""
    # Note: Using 'order_status' = 'pickedup' as the equivalent of a completed order for revenue calculation
    completed_orders = Order.objects.filter(order_status='pickedup')
    total_revenue = completed_orders.aggregate(total=models.Sum('total_price'))['total'] or 0
    context = {
        'total_orders': Order.objects.count(),
        'completed_orders': completed_orders.count(),
        'total_revenue': total_revenue,
        'pending_orders': Order.objects.filter(order_status__in=['open', 'ready']).count(),
    }
    return render(request, 'OrderMaster/analytics.html', context)

@admin_required
def settings_view(request):
    """Renders the settings page."""
    return render(request, 'OrderMaster/settings.html')

# =================================================================================
# API ENDPOINTS
# =================================================================================

@csrf_exempt
@admin_required
@require_POST
def update_order_status(request):
    """API to update an order's order_status."""
    try:
        data = json.loads(request.body)
        order_pk = data.get('id')
        new_status = data.get('status')  # Expects 'ready' or 'pickedup'

        if not all([order_pk, new_status]):
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

        order = get_object_or_404(Order, pk=order_pk)
        order.order_status = new_status
        order.save()
        
        return JsonResponse({'success': True, 'message': f'Order status updated to {new_status}'})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'}, status=500)

@csrf_exempt
@admin_required
def api_menu_item_detail(request, item_id):
    """API endpoint to get or update a specific menu item."""
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'GET':
        data = {
            'id': item.id, 'item_name': item.item_name, 'description': item.description,
            'price': str(item.price), 'category': item.category, 'veg_nonveg': item.veg_nonveg,
            'meal_type': item.meal_type, 'availability_time': item.availability_time,
            'image_url': item.image.url if item.image else ''
        }
        return JsonResponse(data)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{item.item_name}' has been updated successfully.")
            return JsonResponse({'success': True, 'message': 'Item updated successfully!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return HttpResponseBadRequest("Invalid request method")

# =================================================================================
# CUSTOMER-FACING (No changes needed here based on your request)
# =================================================================================

def customer_home(request):
    return render(request, 'OrderMaster/customer_order.html')

@require_http_methods(["GET"])
def api_menu_items(request):
    # ... (This function is correct and doesn't need changes)
    pass

@csrf_exempt
@require_http_methods(["POST"])
def api_place_order(request):
    # ... (This function is correct and doesn't need changes)
    pass

@admin_required
def get_orders_api(request):
    # ... (This function is correct and doesn't need changes)
    pass
