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
    """Displays and manages current orders with date filtering."""
    date_filter = request.GET.get('date_filter', 'today')
    start_date = None
    end_date = None
    today = now().date()

    if date_filter == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
    elif date_filter == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today
    elif date_filter == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
    elif date_filter == 'this_month':
        start_date = today.replace(day=1)
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = next_month
    elif date_filter == 'custom':
        try:
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')
            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() + timedelta(days=1)
        except (ValueError, TypeError):
            date_filter = 'today'
            start_date = today
            end_date = today + timedelta(days=1)

    base_queryset = Order.objects.all()
    if start_date and end_date:
        base_queryset = base_queryset.filter(created_at__gte=start_date, created_at__lt=end_date)
    
    preparing_orders_qs = base_queryset.filter(order_status='open').order_by('created_at')
    ready_orders_qs = base_queryset.filter(order_status='ready').order_by('-created_at')

    # Parse the JSON 'items' string into a Python list for the template
    for order in preparing_orders_qs:
        try:
            order.items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
        except (json.JSONDecodeError, TypeError):
            order.items_list = []
            
    for order in ready_orders_qs:
        try:
            order.items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
        except (json.JSONDecodeError, TypeError):
            order.items_list = []

    # ** THIS IS THE CORRECTED PART **
    context = {
        'preparing_orders': preparing_orders_qs,  # Use the filtered and processed queryset
        'ready_orders': ready_orders_qs,      # Use the filtered and processed queryset
        'selected_filter': date_filter,
        'start_date_val': request.GET.get('start_date', ''),
        'end_date_val': request.GET.get('end_date', ''),
    }
    return render(request, 'OrderMaster/order_management.html', context)

@admin_required
def menu_management_view(request):
    """Handles adding and displaying menu items."""
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES or None)
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

# Add other views like analytics_view, settings_view, etc. if they exist in your project

# =================================================================================
# API ENDPOINTS
# =================================================================================

@csrf_exempt
@admin_required
@require_POST
def update_order_status(request):
    """API to update an order's order_status to 'ready' or 'pickedup'."""
    try:
        data = json.loads(request.body)
        order_pk = data.get('id')
        new_status = data.get('status')

        if not all([order_pk, new_status]):
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

        order = get_object_or_404(Order, pk=order_pk)
        order.order_status = new_status
        order.save(update_fields=['order_status', 'updated_at'])
        
        return JsonResponse({'success': True, 'message': f'Order status updated to {new_status}'})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'}, status=500)
        
@admin_required
def get_orders_api(request):
    """API endpoint to fetch recent orders for the dashboard's live feed."""
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
