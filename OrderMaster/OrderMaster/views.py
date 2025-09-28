# =================================================================================
# IMPORTS
# =================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.utils.timezone import now
from .models import MenuItem, Order, VlhAdmin, models
from .forms import MenuItemForm
from datetime import datetime, timedelta
import json
import logging
from decimal import Decimal

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
        'active_page': 'dashboard',
    }
    return render(request, 'OrderMaster/dashboard.html', context)

@admin_required
def order_management_view(request):
    """Displays and manages current orders with date filtering."""
    date_filter = request.GET.get('date_filter', 'today')
    start_date, end_date = None, None
    today = now().date()
    date_display_str = "Today"

    if date_filter == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
        date_display_str = start_date.strftime('%b %d, %Y')
    elif date_filter == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today
        date_display_str = start_date.strftime('%b %d, %Y')
    elif date_filter == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
        date_display_str = f"{start_date.strftime('%b %d')} - { (end_date - timedelta(days=1)).strftime('%b %d, %Y')}"
    elif date_filter == 'this_month':
        start_date = today.replace(day=1)
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = next_month
        date_display_str = start_date.strftime('%B %Y')
    elif date_filter == 'custom':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        date_display_str = "Custom Range"
        try:
            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() + timedelta(days=1)
                date_display_str = f"{start_date.strftime('%b %d')} - { (end_date - timedelta(days=1)).strftime('%b %d, %Y')}"
        except (ValueError, TypeError):
            date_filter = 'today'
            start_date = today
            end_date = today + timedelta(days=1)
            date_display_str = start_date.strftime('%b %d, %Y')

    base_queryset = Order.objects.all()
    if start_date and end_date:
        base_queryset = base_queryset.filter(created_at__gte=start_date, created_at__lt=end_date)
    
    # Correctly sort each category of orders by most recent first
    preparing_orders_qs = base_queryset.filter(order_status='open').order_by('-created_at')
    ready_orders_qs = base_queryset.filter(order_status='ready').order_by('-ready_time')
    pickedup_orders_qs = base_queryset.filter(order_status='pickedup').order_by('-pickup_time')

    # Parse the JSON 'items' string into a Python list for the template
    for order_list in [preparing_orders_qs, ready_orders_qs, pickedup_orders_qs]:
        for order in order_list:
            try:
                order.items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
            except (json.JSONDecodeError, TypeError):
                order.items_list = []

    context = {
        'preparing_orders': preparing_orders_qs,
        'ready_orders': ready_orders_qs,
        'pickedup_orders': pickedup_orders_qs,
        'selected_filter': date_filter,
        'date_display_str': date_display_str,
        'start_date_val': request.GET.get('start_date', ''),
        'end_date_val': request.GET.get('end_date', ''),
        'active_page': 'order_management',
    }
    return render(request, 'OrderMaster/order_management.html', context)

@admin_required
def menu_management_view(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request, 'New menu item added successfully!')
            return redirect('menu_management')
    else:
        form = MenuItemForm()
    context = {
        'menu_items': MenuItem.objects.all().order_by('item_name'),
        'add_item_form': form,
        'active_page': 'menu_management',
    }
    return render(request, 'OrderMaster/menu_management.html', context)

@admin_required
@require_POST
def delete_menu_item_view(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item.delete()
    messages.success(request, 'Menu item deleted successfully!')
    return redirect('menu_management')

@admin_required
def analytics_view(request):
    """Renders the analytics page."""
    completed_orders = Order.objects.filter(order_status='pickedup')
    total_revenue = completed_orders.aggregate(total=models.Sum('total_price'))['total'] or 0
    context = {
        'total_orders': Order.objects.count(),
        'completed_orders': completed_orders.count(),
        'total_revenue': total_revenue,
        'pending_orders': Order.objects.filter(order_status__in=['open', 'ready']).count(),
        'active_page': 'analytics',
    }
    return render(request, 'OrderMaster/analytics.html', context)

@admin_required
def settings_view(request):
    """Renders the settings page."""
    context = {
        'active_page': 'settings',
    }
    return render(request, 'OrderMaster/settings.html', context)

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
        new_status = data.get('status')
        if not all([order_pk, new_status]):
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)
        order = get_object_or_404(Order, pk=order_pk)
        order.order_status = new_status
        # Set the timestamp when the status changes
        if new_status == 'ready':
            order.ready_time = now()
        elif new_status == 'pickedup':
            order.pickup_time = now()
        order.save()
        return JsonResponse({'success': True, 'message': f'Order status updated to {new_status}'})
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
        }
        return JsonResponse(data)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, None, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{item.item_name}' has been updated.")
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return HttpResponseBadRequest("Invalid request method")

@admin_required
def get_orders_api(request):
    """API for the live order feed on the dashboard."""
    try:
        orders = Order.objects.order_by('-created_at')[:20]
        data = []
        for order in orders:
            try:
                items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
            except (json.JSONDecodeError, TypeError):
                items_list = []
            order_data = {
                'order_id': order.order_id,
                'items': items_list,
                'total_price': float(order.total_price),
                'order_status': order.order_status,
            }
            data.append(order_data)
        return JsonResponse({'orders': data})
    except Exception as e:
        logger.error(f"API get_orders error: {e}")
        return JsonResponse({'error': 'Server error occurred.'}, status=500)



@require_http_methods(["GET"])
def api_menu_items(request):
    """API endpoint that provides the full menu to the customer frontend."""
    try:
        menu_items = MenuItem.objects.all().values(
            'id', 'item_name', 'description', 'price', 'category',
            'veg_nonveg', 'meal_type', 'availability_time'
        ).order_by('category', 'item_name')
        items_list = [{**item, 'price': float(item['price'])} for item in menu_items]
        return JsonResponse(items_list, safe=False)
    except Exception as e:
        logger.error(f"API menu items error: {e}")
        return JsonResponse({'error': 'Server error occurred.'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_place_order(request):
    """API endpoint for customers to place a new order."""
    try:
        data = json.loads(request.body)
        # Your order placement logic here...
        return JsonResponse({'success': True, 'message': 'Order placed successfully!'})
    except Exception as e:
        logger.error(f"Place order error: {e}")
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)

def customer_home(request):
    return render(request, 'OrderMaster/customer_order.html')




