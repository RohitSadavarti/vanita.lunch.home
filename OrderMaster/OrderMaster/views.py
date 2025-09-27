# =================================================================================
# IMPORTS
# =================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import MenuItem, Order, VlhAdmin
import json
import uuid
from decimal import Decimal

# =================================================================================
# DECORATORS & AUTHENTICATION
# =================================================================================

def admin_required(view_func):
    """
    Custom decorator to ensure that a user is an authenticated admin.
    If not authenticated, they are redirected to the login page.
    """
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.warning(request, 'You must be logged in to view this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def login_view(request):
    """Handles the admin login functionality."""
    if request.method == 'POST':
        mobile = request.POST.get('username')  # Using 'username' for mobile
        password = request.POST.get('password')
        
        try:
            # Authenticate against the custom VlhAdmin model
            admin_user = VlhAdmin.objects.get(mobile=mobile)
            if admin_user.check_password(password):
                # Set session variables for custom authentication state
                request.session['admin_id'] = admin_user.id
                request.session['admin_mobile'] = admin_user.mobile
                request.session['is_authenticated'] = True
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid mobile number or password.')
        except VlhAdmin.DoesNotExist:
            messages.error(request, 'Invalid mobile number or password.')
            
    return render(request, 'OrderMaster/login.html')

def logout_view(request):
    """Clears the session to log the admin out."""
    request.session.flush()
    messages.info(request, 'You have been successfully logged out.')
    return redirect('login')

# =================================================================================
# ADMIN DASHBOARD & ORDER MANAGEMENT VIEWS
# =================================================================================

@admin_required
def dashboard(request):
    """Renders the main admin dashboard page."""
    # You can add context data here like recent orders, sales stats, etc.
    recent_orders = Order.objects.order_by('-order_time')[:5]
    context = {
        'recent_orders': recent_orders,
        'total_orders': Order.objects.count()
    }
    return render(request, 'OrderMaster/dashboard.html', context)

@admin_required
def order_management(request):
    """Displays and manages current orders ('preparing' and 'ready')."""
    preparing_orders = Order.objects.filter(status='preparing').order_by('order_time')
    ready_orders = Order.objects.filter(status='ready').order_by('-ready_time')

    # Safely parse the JSON data stored in the 'items' field for display
    for order in preparing_orders:
        try:
            order.parsed_items = json.loads(order.items)
        except (json.JSONDecodeError, TypeError):
            order.parsed_items = {} # Default to empty dict on failure

    for order in ready_orders:
        try:
            order.parsed_items = json.loads(order.items)
        except (json.JSONDecodeError, TypeError):
            order.parsed_items = {}
            
    context = {
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
    }
    return render(request, 'OrderMaster/order_management.html', context)

@csrf_exempt
@admin_required
@require_http_methods(["POST"])
def update_order_status(request):
    """API endpoint for admins to update the status of an order."""
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_status = data.get('status')

        if not all([order_id, new_status]):
            return JsonResponse({'success': False, 'error': 'Missing order_id or status.'}, status=400)

        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        if new_status == 'ready':
            order.ready_time = timezone.now()
        
        order.save()
        return JsonResponse({'success': True, 'message': f'Order status updated to {new_status}.'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# =================================================================================
# ADMIN MENU MANAGEMENT VIEWS
# =================================================================================

@admin_required
def menu_management(request):
    """Handles adding new menu items and displaying the list of all items."""
    if request.method == 'POST':
        # Create a new menu item from form data
        MenuItem.objects.create(
            item_name=request.POST['item_name'],
            description=request.POST['description'],
            price=request.POST['price'],
            category=request.POST['category'],
            veg_nonveg=request.POST['veg_nonveg'],
            meal_type=request.POST['meal_type'],
            availability_time=request.POST['availability_time'],
            image=request.FILES.get('image')
        )
        messages.success(request, 'Menu item added successfully!')
        return redirect('menu_management')
        
    menu_items = MenuItem.objects.all().order_by('-created_at')
    context = {'menu_items': menu_items}
    return render(request, 'OrderMaster/menu_management.html', context)

@admin_required
def edit_menu_item(request, item_id):
    """Handles editing an existing menu item."""
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        item.item_name = request.POST['item_name']
        item.description = request.POST['description']
        item.price = request.POST['price']
        item.category = request.POST['category']
        item.veg_nonveg = request.POST['veg_nonveg']
        item.meal_type = request.POST['meal_type']
        item.availability_time = request.POST['availability_time']
        if 'image' in request.FILES:
            item.image = request.FILES['image']
        item.save()
        messages.success(request, 'Menu item updated successfully!')
        return redirect('menu_management')
        
    return render(request, 'OrderMaster/edit_menu_item.html', {'item': item})

@admin_required
@require_http_methods(["POST"])
def delete_menu_item(request, item_id):
    """Handles deleting a menu item."""
    item = get_object_or_404(MenuItem, id=item_id)
    item.delete()
    messages.success(request, 'Menu item deleted successfully!')
    return redirect('menu_management')

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
        
        # Convert Decimal to float for JSON serialization
        items_list = [
            {**item, 'price': float(item['price'])} for item in menu_items
        ]
        
        return JsonResponse(items_list, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_place_order(request):
    """
    API endpoint for customers to place a new order.
    This is now compatible with the cash-on-delivery JavaScript.
    """
    try:
        data = json.loads(request.body)
        
        # --- 1. Validate required fields from frontend ---
        required_fields = ['customer_name', 'customer_mobile', 'customer_address', 'items', 'total_amount']
        if not all(field in data and data[field] for field in required_fields):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)
        
        # --- 2. Sanitize and validate customer data ---
        mobile = data['customer_mobile']
        if not (mobile.isdigit() and len(mobile) == 10):
            return JsonResponse({'error': 'Invalid 10-digit mobile number format.'}, status=400)
            
        items = data['items'] # This is now a list of dicts, NOT a string
        if not isinstance(items, list) or not items:
            return JsonResponse({'error': 'Cart items are missing or invalid.'}, status=400)

        # --- 3. Server-side calculation to prevent price tampering ---
        calculated_subtotal = Decimal('0.00')
        validated_items_for_db = []
        
        for item in items:
            try:
                menu_item = MenuItem.objects.get(id=item['id'])
                quantity = int(item['quantity'])
                if quantity <= 0: continue # Skip items with zero or negative quantity
                
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
            except (KeyError, ValueError):
                return JsonResponse({'error': 'Invalid data format in cart items.'}, status=400)

        # --- 4. Calculate delivery fee and final total ---
        delivery_fee = Decimal('0.00') if calculated_subtotal >= 300 else Decimal('40.00')
        final_total_server = calculated_subtotal + delivery_fee
        
        # Compare with the total submitted from the client
        if abs(final_total_server - Decimal(data['total_amount'])) > Decimal('0.01'):
            return JsonResponse({'error': 'Total amount mismatch. Please try again.'}, status=400)
        
        # --- 5. Create and save the order ---
        order_id = f"VLH{timezone.now().strftime('%y%m%d%H%M')}{str(uuid.uuid4())[:4].upper()}"
        
        # Structure the data to be saved in the JSON 'items' field
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
            payment_id=data.get('payment_id', 'N/A'), # Save the COD payment ID
            status='preparing'
        )
        
        return JsonResponse({'success': True, 'order_id': order_id, 'message': 'Order placed successfully!'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data in request body.'}, status=400)
    except Exception as e:
        # Log the exception e for debugging
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)

# =================================================================================
# OTHER PAGES (Analytics, Settings, etc.)
# =================================================================================

@admin_required
def analytics(request):
    """Renders the analytics page."""
    return render(request, 'OrderMaster/analytics.html')

@admin_required
def settings(request):
    """Renders the settings page."""
    return render(request, 'OrderMaster/settings.html')
