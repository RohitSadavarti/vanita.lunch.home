# OrderMaster/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from .models import MenuItem, Order, VlhAdmin, models
from .forms import MenuItemForm
from datetime import datetime, timedelta
import os
import json
import uuid
from decimal import Decimal
import logging

# Firebase Admin Imports
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

# ==============================================================================
#  Firebase Admin SDK Initialization
# ==============================================================================
# IMPORTANT: This setup assumes you have your service account JSON file
# and have set the GOOGLE_APPLICATION_CREDENTIALS environment variable.
# If not, you can load it directly:
# cred = credentials.Certificate("path/to/your/serviceAccountKey.json")


# Firebase Admin SDK Initialization
try:
    if not firebase_admin._apps:
        # Check if running on Render (has environment variable)
        firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
        
        if firebase_creds:
            # Parse JSON credentials from environment variable
            cred_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK initialized with service account")
            logger.info("Firebase Admin SDK initialized successfully")
        else:
            # Fallback for local development
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': "vanita-lunch-home",
            })
            print("⚠️ Firebase Admin SDK initialized with default credentials")
except Exception as e:
    logger.error(f"❌ Failed to initialize Firebase Admin SDK: {e}")
    print(f"ERROR: Failed to initialize Firebase Admin SDK: {e}")
    # ==============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def subscribe_to_topic(request):
    """Subscribe FCM token to new_orders topic"""
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({'error': 'Token required'}, status=400)
        
        # Subscribe token to topic
        response = messaging.subscribe_to_topic([token], 'new_orders')
        
        if response.failure_count > 0:
            logger.error(f"Failed to subscribe token: {response.errors}")
            return JsonResponse({'error': 'Subscription failed'}, status=500)
        
        logger.info(f"Successfully subscribed token to new_orders topic")
        return JsonResponse({'success': True, 'message': 'Subscribed to notifications'})
        
    except Exception as e:
        logger.error(f"Topic subscription error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def customer_order_view(request):
    menu_items = MenuItem.objects.all()
    return render(request, 'OrderMaster/customer_order.html', {'menu_items': menu_items})

@csrf_exempt
def firebase_messaging_sw(request):
    # This view correctly serves the service worker file.
    return render(request, 'firebase-messaging-sw.js', content_type='application/javascript')


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.warning(request, 'You must be logged in to view this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# ... (login_view, logout_view, and dashboard_view remain the same) ...

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
    date_filter = request.GET.get('date_filter', 'today')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    now = timezone.now()
    if date_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif date_filter == 'yesterday':
        start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif date_filter == 'this_week':
        start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif date_filter == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif date_filter == 'custom' and start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
    else: # Default to today
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        date_filter = 'today'

    preparing_orders = Order.objects.filter(order_status='open', created_at__range=(start_date, end_date))
    ready_orders = Order.objects.filter(order_status='ready', created_at__range=(start_date, end_date))
    pickedup_orders = Order.objects.filter(order_status='pickedup', created_at__range=(start_date, end_date))

    for order in preparing_orders:
        order.items_list = order.items if isinstance(order.items, list) else json.loads(order.items)
    for order in ready_orders:
        order.items_list = order.items if isinstance(order.items, list) else json.loads(order.items)
    for order in pickedup_orders:
        order.items_list = order.items if isinstance(order.items, list) else json.loads(order.items)

    context = {
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'pickedup_orders': pickedup_orders,
        'date_display_str': date_filter.replace('_', ' ').title(),
        'selected_filter': date_filter,
        'start_date_val': start_date_str if date_filter == 'custom' else '',
        'end_date_val': end_date_str if date_filter == 'custom' else '',
        'active_page': 'order_management',
    }
    return render(request, 'OrderMaster/order_management.html', context)


@csrf_exempt
@admin_required
@require_POST
def update_order_status(request):
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
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ... (menu_management_view, delete_menu_item_view, api_menu_item_detail remain the same) ...
@admin_required
def menu_management_view(request):
    if request.method == 'POST':
        # REMOVED: request.FILES, as we are no longer uploading files
        form = MenuItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item added successfully!')
            return redirect('menu_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MenuItemForm()
    
    context = {
        'menu_items': MenuItem.objects.all().order_by('-created_at'),
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

@csrf_exempt
@admin_required
def api_menu_item_detail(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    
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
            # FIXED: Changed from item.image.url to item.image_url
            'image_url': item.image_url if item.image_url else ''
        }
        return JsonResponse(data)
        
    if request.method == 'POST':
        # REMOVED: request.FILES from the form instance
        form = MenuItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Item updated successfully!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def api_menu_items(request):
    try:
        # FIXED: Select 'image_url' instead of 'image'
        menu_items = MenuItem.objects.all().values(
            'id', 'item_name', 'description', 'price', 'category',
            'veg_nonveg', 'meal_type', 'availability_time', 'image_url'
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
    try:
        data = json.loads(request.body)
        required_fields = ['customer_name', 'customer_mobile', 'items', 'total_price']
        if not all(field in data and data[field] for field in required_fields):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        mobile = data['customer_mobile']
        if not (mobile.isdigit() and len(mobile) == 10):
            return JsonResponse({'error': 'Invalid 10-digit mobile number format.'}, status=400)

        items = data['items']
        if not isinstance(items, list) or not items:
            return JsonResponse({'error': 'Cart items are missing or invalid.'}, status=400)

        calculated_subtotal = Decimal('0.00')
        validated_items_for_db = []
        for item in items:
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

        final_total_server = Decimal(str(data['total_price']))

        order_id = f"VLH{timezone.now().strftime('%y%m%d%H%M')}{str(uuid.uuid4())[:4].upper()}"

        # Create the order with correct fields
        new_order = Order.objects.create(
            order_id=order_id,
            customer_name=data['customer_name'],
            customer_mobile=data['customer_mobile'],
            items=validated_items_for_db,  # Store as list, JSONField will handle it
            subtotal=calculated_subtotal,
            discount=Decimal('0.00'),
            total_price=final_total_server,
            status='pending',
            payment_method='COD',
            payment_id=data.get('payment_id', 'COD'),
            order_status='open'
        )

        # Send Firebase Cloud Messaging notification
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title='🔔 New Order Received!',
                    body=f'Order #{new_order.order_id} from {new_order.customer_name} - ₹{new_order.total_price}'
                ),
                topic='new_orders'
            )
            response = messaging.send(message)
            logger.info(f'Successfully sent FCM message: {response}')
        except Exception as e:
            logger.error(f"Error sending FCM message: {e}")

        return JsonResponse({
            'success': True, 
            'order_id': order_id, 
            'message': 'Order placed successfully!'
        })

    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        logger.warning(f"Invalid order request: {e}")
        return JsonResponse({'error': 'Invalid data format.'}, status=400)
    except MenuItem.DoesNotExist:
        return JsonResponse({'error': 'Invalid menu item in the order.'}, status=400)
    except Exception as e:
        logger.error(f"Place order error: {e}")
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)
        
# ... (analytics_view, settings_view, get_orders_api remain the same) ...
@admin_required
def analytics_view(request):
    """Renders the analytics page."""
    completed_orders = Order.objects.filter(order_status='pickedup') # Use final status
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
    """Renders the settings page."""
    return render(request, 'OrderMaster/settings.html')

@admin_required
def get_orders_api(request):
    """API endpoint to fetch recent orders for the admin dashboard."""
    try:
        orders = Order.objects.all().order_by('-created_at')[:20]
        data = [{
            'id': order.id, 'order_id': order.order_id,
            'customer_name': order.customer_name, 'items': order.items,
            'total_price': float(order.total_price),
            'status': order.order_status, # Use correct status field
            'created_at': order.created_at.strftime('%b %d, %Y, %I:%M %p')
        } for order in orders]
        return JsonResponse({'orders': data})
    except Exception as e:
        logger.error(f"API get_orders error: {e}")
        return JsonResponse({'error': 'Server error occurred.'}, status=500)


