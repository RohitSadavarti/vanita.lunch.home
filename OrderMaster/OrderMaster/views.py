# OrderMaster/views.py

# =================================================================================
# IMPORTS
# =================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.cache import cache_control
from django.utils.timezone import now
from .models import MenuItem, Order, VlhAdmin, models
from .forms import MenuItemForm
from datetime import datetime, timedelta
import json
import logging
import os
from decimal import Decimal


# Set up logging
logger = logging.getLogger(__name__)

@cache_control(max_age=60 * 60 * 24 * 30)
def firebase_messaging_sw(request):
    try:
        # --- THIS PATH IS FIXED ---
        # It now correctly constructs the path to the file inside your app's static directory.
        sw_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), # This now correctly points to BASE_DIR/OrderMaster
            'OrderMaster',
            'static',
            'firebase-messaging-sw.js'
        )
        with open(sw_path, 'r') as f:
            return HttpResponse(f.read(), content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse("Service worker not found.", status=404, content_type='application/javascript')



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
    """
    Handles the display of orders in three stages: Preparing, Ready, and Picked Up.
    Also includes robust date filtering logic.
    """
    date_filter = request.GET.get('date_filter', 'today')
    start_date, end_date = None, None
    today = timezone.now().date()
    date_display_str = "Today"

    # --- Date Filtering Logic ---
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
        date_display_str = f"{start_date.strftime('%b %d')} - {(end_date - timedelta(days=1)).strftime('%b %d, %Y')}"
    elif date_filter == 'this_month':
        start_date = today.replace(day=1)
        # Go to the next month and then subtract a day to get the end of the current month
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
                date_display_str = f"{start_date.strftime('%b %d')} - {(end_date - timedelta(days=1)).strftime('%b %d, %Y')}"
        except (ValueError, TypeError):
            # Fallback to 'today' if custom dates are invalid
            date_filter = 'today'
            start_date = today
            end_date = today + timedelta(days=1)
            date_display_str = start_date.strftime('%b %d, %Y')

    # --- Database Queries ---
    base_queryset = Order.objects.all()
    if start_date and end_date:
        # Make the datetime objects timezone-aware for comparison
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
        base_queryset = base_queryset.filter(created_at__gte=start_datetime, created_at__lt=end_datetime)

    # Filter orders by status
    preparing_orders_qs = base_queryset.filter(order_status='open').order_by('-created_at')
    ready_orders_qs = base_queryset.filter(order_status='ready').order_by('-created_at') # Assuming you add a 'ready_at' field later
    pickedup_orders_qs = base_queryset.filter(order_status='pickedup').order_by('-created_at') # Assuming you add a 'picked_up_at' field later

    # Process items JSON for display
    for order_list in [preparing_orders_qs, ready_orders_qs, pickedup_orders_qs]:
        for order in order_list:
            try:
                order.items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
            except (json.JSONDecodeError, TypeError):
                order.items_list = [] # Failsafe for malformed JSON

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
        form = MenuItemForm(request.POST)
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
    """API to update an order's status."""
    try:
        data = json.loads(request.body)
        order_pk = data.get('id')
        new_status = data.get('status')

        if not all([order_pk, new_status]):
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

        order = get_object_or_404(Order, pk=order_pk)
        order.order_status = new_status
        
        if new_status == 'ready':
            order.ready_time = timezone.now()
        elif new_status == 'pickedup':
            order.pickup_time = timezone.now()
            
        order.save()
        return JsonResponse({'success': True})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'}, status=500)


@csrf_exempt
@admin_required
def api_menu_item_detail(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'GET':
        data = {
            'id': item.id, 'item_name': item.item_name, 'description': item.description,
            'price': str(item.price), 'category': item.category, 'veg_nonveg': item.veg_nonveg,
            'meal_type': item.meal_type, 'availability_time': item.availability_time,
            'image_url': item.image_url,
        }
        return JsonResponse(data)
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
            
    return HttpResponseBadRequest("Invalid request method")


@admin_required
def get_orders_api(request):
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
            'veg_nonveg', 'meal_type', 'availability_time', 'image_url'
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
        
        # Extract customer details and cart items from the request
        customer_name = data.get('customerName')
        customer_mobile = data.get('customerMobile')
        cart_items = data.get('cart')

        if not all([customer_name, customer_mobile, cart_items]):
            return JsonResponse({'success': False, 'error': 'Missing required order data.'}, status=400)

        # Calculate total price and prepare items for the Order model
        total_price = sum(Decimal(item['price']) * item['quantity'] for item in cart_items)
        
        # Create a new Order instance
        new_order = Order(
            customer_name=customer_name,
            customer_mobile=customer_mobile,
            items=cart_items,  # Save the cart items directly as JSON
            subtotal=total_price,
            total_price=total_price,
            status='pending', # You can set an initial status
            payment_method='cash_on_delivery', # Set a default or get from request
            order_status='open'
        )
        new_order.save()

        # Return a success response with the new order_id
        return JsonResponse({
            'success': True, 
            'message': 'Order placed successfully!',
            'order_id': new_order.order_id
        })

    except json.JSONDecodeError:
        logger.error("Place order error: Invalid JSON received.")
        return JsonResponse({'success': False, 'error': 'Invalid data format.'}, status=400)
    except Exception as e:
        logger.error(f"Place order error: {e}")
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)


def customer_home(request):
    return render(request, 'OrderMaster/customer_order.html')
    









