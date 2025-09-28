# =================================================================================
# IMPORTS
# =================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import MenuItem, Order, VlhAdmin
from .forms import MenuItemForm # Import the form
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

def customer_order_view(request):
    """Serves the main customer-facing order page."""
    menu_items = MenuItem.objects.all()
    return render(request, 'OrderMaster/customer_order.html', {'menu_items': menu_items})

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.warning(request, 'You must be logged in to view this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Admin Login/Logout
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
# ADMIN DASHBOARD & ORDER MANAGEMENT VIEWS
# =================================================================================

@admin_required
def dashboard_view(request):
    """Renders the main admin dashboard page."""
    context = {
        'total_orders': Order.objects.count(),
        'preparing_orders_count': Order.objects.filter(status='Preparing').count(),
        'ready_orders_count': Order.objects.filter(status='Ready').count(),
        'menu_items_count': MenuItem.objects.count(),
        'recent_orders': Order.objects.order_by('-created_at')[:5],
    }
    return render(request, 'OrderMaster/dashboard.html', context)
    
@admin_required
def order_management_view(request):
    """Displays and manages current orders."""
    context = {
        'preparing_orders': Order.objects.filter(status='Preparing').order_by('created_at'),
        'ready_orders': Order.objects.filter(status='Ready').order_by('-created_at'),
    }
    return render(request, 'OrderMaster/order_management.html', context)
    
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
        order.status = new_status
        
        if new_status == 'Ready':
            order.ready_time = timezone.now()
        
        order.save()
        return JsonResponse({'success': True})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'}, status=500)

# =================================================================================
# ADMIN MENU MANAGEMENT VIEWS
# =================================================================================

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
        'item_form': form  # Pass the form to the template
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

# --- THIS IS THE MISSING FUNCTION ---
@csrf_exempt
@admin_required
def api_menu_item_detail(request, item_id):
    """
    API endpoint to get or update a specific menu item.
    """
    try:
        item = get_object_or_404(MenuItem, id=item_id)
    except MenuItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)

    if request.method == 'GET':
        data = {
            'id': item.id,
            'item_name': item.item_name,
            'description': item.description,
            'price': str(item.price),
            'category': item.category,
            'veg_nonveg': item.veg_nonveg,
            'meal_type': item.meal_type,
            'availability_time': item.availability_time,
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
# CUSTOMER-FACING VIEWS & API ENDPOINTS
# =================================================================================

def customer_home(request):
    """Renders the main customer ordering page."""
    return render(request, 'OrderMaster/customer_order.html')

@require_http_methods(["GET"])
def api_menu_items(request):
    """API endpoint that provides the full menu to the frontend."""
    try:
        menu_items = MenuItem.objects.all().values(
            'id', 'item_name', 'description', 'price', 'category', 
            'veg_nonveg', 'meal_type', 'availability_time', 'image'
        ).order_by('category', 'item_name')
        
        items_list = [
            {**item, 'price': float(item['price'])} for item in menu_items
        ]
        
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
        
        required_fields = ['customer_name', 'customer_mobile', 'customer_address', 'items', 'total_amount']
        if not all(field in data and data[field] for field in required_fields):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)
        
        mobile = data['customer_mobile']
        if not (mobile.isdigit() and len(mobile) == 10):
            return JsonResponse({'error': 'Invalid 10-digit mobile number format.'}, status=400)
            
        items = data['items']
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid items format.'}, status=400)
        
        if not isinstance(items, list) or not items:
            return JsonResponse({'error': 'Cart items are missing or invalid.'}, status=400)

        calculated_subtotal = Decimal('0.00')
        validated_items_for_db = []
        
        for item in items:
            try:
                menu_item = MenuItem.objects.get(id=item['id'])
                quantity = int(item['quantity'])
                if quantity <= 0: continue
                
                item_total = menu_item.price * quantity
                calculated_subtotal += item_total
                
                validated_items_for_db.append({
                    'id': menu_item.id,
                    'name': menu_item.item_name,
                    'price': float(menu_item.price),
                    'quantity': quantity,
                })
            except MenuItem.DoesNotExist:
                return JsonResponse({'error': f'Invalid menu item ID: {item.get("id")}.'}, status=400)
            except (KeyError, ValueError, TypeError):
                return JsonResponse({'error': 'Invalid data format in cart items.'}, status=400)

        delivery_fee = Decimal('0.00') if calculated_subtotal >= 300 else Decimal('40.00')
        final_total_server = calculated_subtotal + delivery_fee
        
        if abs(final_total_server - Decimal(str(data['total_amount']))) > Decimal('0.01'):
            return JsonResponse({'error': 'Total amount mismatch. Please try again.'}, status=400)
        
        order_id = f"VLH{timezone.now().strftime('%y%m%d%H%M')}{str(uuid.uuid4())[:4].upper()}"
        
        order_details_json = {
            'customer_mobile': mobile,
            'customer_address': data['customer_address'],
            'items': validated_items_for_db,
            'delivery_fee': float(delivery_fee),
            'subtotal': float(calculated_subtotal)
        }
        
        Order.objects.create(
            order_id=order_id,
            customer_name=data['customer_name'],
            items=json.dumps(order_details_json),
            total_amount=final_total_server,
            payment_id=data.get('payment_id', 'COD'),
            status='Preparing'
        )
        
        return JsonResponse({'success': True, 'order_id': order_id, 'message': 'Order placed successfully!'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data in request body.'}, status=400)
    except Exception as e:
        logger.error(f"Place order error: {e}")
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)

# =================================================================================
# OTHER PAGES (Analytics, Settings, etc.)
# =================================================================================

@admin_required
def analytics_view(request):
    """Renders the analytics page."""
    completed_orders = Order.objects.filter(status='Completed')
    total_revenue = completed_orders.aggregate(total=models.Sum('total_amount'))['total'] or 0
    context = {
        'total_orders': Order.objects.count(),
        'completed_orders': completed_orders.count(),
        'total_revenue': total_revenue,
        'pending_orders': Order.objects.filter(status__in=['Preparing', 'Ready']).count(),
    }
    return render(request, 'OrderMaster/analytics.html', context)

@admin_required
def settings_view(request):
    """Renders the settings page."""
    return render(request, 'OrderMaster/settings.html')

# =================================================================================
# API FOR REAL-TIME UPDATES
# =================================================================================

@admin_required
def get_orders_api(request):
    """API endpoint to fetch recent orders for the admin dashboard."""
    try:
        orders = Order.objects.all().order_by('-created_at')[:20]
        data = [{
            'id': order.id,
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'items': order.items,
            'total_amount': float(order.total_amount),
            'status': order.status,
            'created_at': order.created_at.strftime('%b %d, %Y, %I:%M %p')
        } for order in orders]
        return JsonResponse({'orders': data})
    except Exception as e:
        logger.error(f"API get_orders error: {e}")
        return JsonResponse({'error': 'Server error occurred.'}, status=500)
