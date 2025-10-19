# =================================================================================
# IMPORTS
# =================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from .models import MenuItem, Order, VlhAdmin
from .forms import MenuItemForm # Assuming you have forms.py
import json
import uuid
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
from decimal import Decimal

logger = logging.getLogger(__name__)

# =================================================================================
# FIREBASE INITIALIZATION (Run only once)
# =================================================================================
try:
    cred_path = os.path.join(settings.BASE_DIR, 'vanita-lunch-home-firebase-adminsdk-hdk0i-9b377484a9.json')
    if os.path.exists(cred_path) and not firebase_admin._apps: # Check if already initialized
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
    elif not os.path.exists(cred_path):
        logger.error(f"Firebase credentials file not found at: {cred_path}")
except Exception as e:
    # Log error but don't prevent app startup if Firebase fails init
    logger.error(f"Error initializing Firebase Admin SDK: {e}")

# =================================================================================
# DECORATORS & AUTHENTICATION
# =================================================================================

def admin_required(view_func):
    """ Custom decorator for admin authentication. """
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.warning(request, 'You must be logged in to view this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def login_view(request):
    """ Handles admin login using the custom VlhAdmin model. """
    if request.method == 'POST':
        mobile = request.POST.get('username')
        password = request.POST.get('password')
        try:
            admin_user = VlhAdmin.objects.get(mobile=mobile)
            if admin_user.check_password(password):
                request.session['is_authenticated'] = True
                request.session['admin_mobile'] = admin_user.mobile
                request.session.set_expiry(1209600) # Optional: Set session expiry (e.g., 2 weeks)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid mobile number or password.')
        except VlhAdmin.DoesNotExist:
            messages.error(request, 'Invalid mobile number or password.')
    return render(request, 'OrderMaster/login.html')

@admin_required
def logout_view(request):
    """ Clears the session to log the admin out. """
    request.session.flush()
    messages.info(request, 'You have been successfully logged out.')
    return redirect('login')

# =================================================================================
# FIREBASE MESSAGING SERVICE WORKER VIEW
# =================================================================================

@require_GET
def firebase_messaging_sw(request):
    """ Serves the Firebase Messaging Service Worker file. """
    try:
        # Ensure the template exists at the specified path
        return render(request, 'firebase-messaging-sw.js', content_type='application/javascript')
    except Exception as e:
        logger.error(f"Error serving firebase-messaging-sw.js: {e}")
        return HttpResponse("Error serving service worker.", status=500, content_type="text/plain")

# =================================================================================
# CUSTOMER-FACING VIEWS & API
# =================================================================================

def customer_order_view(request):
    """ Renders the main customer ordering page. """
    # This view now primarily renders the page. Order placement is handled by api_place_order.
    menu_items = MenuItem.objects.all()
    # Pass Firebase config if needed by customer page JS
    context = {
        'menu_items': menu_items,
        'firebase_config': settings.FIREBASE_CONFIG if hasattr(settings, 'FIREBASE_CONFIG') else None
    }
    return render(request, 'OrderMaster/customer_order.html', context)

@require_GET
def api_menu_items(request):
    """ API endpoint providing the menu to the customer frontend. """
    try:
        menu_items = MenuItem.objects.all().values(
            'id', 'name', 'price', 'image' # Add other fields if needed by JS
        ).order_by('name')
        items_list = [
            {**item, 'price': float(item['price']), 'image': request.build_absolute_uri(settings.MEDIA_URL + item['image']) if item.get('image') else None}
            for item in menu_items
        ]
        return JsonResponse(items_list, safe=False)
    except Exception as e:
        logger.error(f"API menu items error: {e}")
        return JsonResponse({'error': 'Server error occurred.'}, status=500)

@csrf_exempt # CSRF exemption for the API endpoint
@require_POST
def api_place_order(request):
    """ API endpoint for customers placing orders. """
    try:
        data = json.loads(request.body)
        items_data = data.get('items')
        customer_name = data.get('customer_name', 'Anonymous')
        total_amount_client = Decimal(str(data.get('total_amount', '0.00'))) # Convert client total

        if not items_data or total_amount_client <= 0:
            return JsonResponse({'status': 'error', 'message': 'Missing items or invalid total.'}, status=400)

        # --- Server-side calculation to prevent price tampering ---
        calculated_total = Decimal('0.00')
        validated_items_for_db = {} # Use dict for better structure in JSON
        item_ids = [item.get('id') for item in items_data if item.get('id')]
        menu_items_from_db = MenuItem.objects.filter(id__in=item_ids)
        menu_items_dict = {item.id: item for item in menu_items_from_db}

        for item_data in items_data:
            item_id = item_data.get('id')
            quantity = int(item_data.get('quantity', 0))
            db_item = menu_items_dict.get(item_id)

            if db_item and quantity > 0:
                item_price = db_item.price
                calculated_total += item_price * quantity
                # Store item name along with quantity for clarity
                validated_items_for_db[db_item.name] = quantity
            else:
                 logger.warning(f"Invalid item or quantity skipped: ID {item_id}, Qty {quantity}")
                 # Optionally return error if strict validation needed:
                 # return JsonResponse({'status': 'error', 'message': f'Invalid item ID {item_id} or quantity.'}, status=400)

        # Compare calculated total with client total (allow small difference for potential float issues)
        if abs(calculated_total - total_amount_client) > Decimal('0.01'):
            logger.error(f"Total amount mismatch. Client: {total_amount_client}, Server: {calculated_total}")
            return JsonResponse({'status': 'error', 'message': 'Total amount mismatch. Please refresh and try again.'}, status=400)

        # --- Create and save the order ---
        order = Order.objects.create(
            order_id=str(uuid.uuid4()).split('-')[0].upper(),
            customer_name=customer_name,
            items=validated_items_for_db, # Save the validated name:quantity dict
            total_amount=calculated_total, # Use server-calculated total
            payment_id=data.get('payment_id', 'COD'),
            created_at=timezone.now(),
            status='Pending'
        )

        # --- Send push notification ---
        try:
            if firebase_admin._apps: # Check if Firebase is initialized
                message = messaging.Message(
                    notification=messaging.Notification(
                        title='New Order Received!',
                        body=f'Order #{order.order_id} from {customer_name} for ₹{calculated_total:.2f}.'
                    ),
                    topic='new_orders'
                )
                response = messaging.send(message)
                logger.info(f'Successfully sent FCM message: {response}')
            else:
                logger.warning("Firebase not initialized, skipping notification.")
        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}")

        return JsonResponse({'status': 'success', 'order_id': order.order_id})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        logger.error(f"Place order API error: {e}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected server error occurred.'}, status=500)


# =================================================================================
# ADMIN PAGES
# =================================================================================

@admin_required
def dashboard_view(request):
    """ Renders the main admin dashboard page. """
    try:
        # Example data for dashboard (customize as needed)
        recent_orders = Order.objects.order_by('-created_at')[:5]
        context = {
            'recent_orders': recent_orders,
            'total_orders': Order.objects.count(),
            'pending_orders_count': Order.objects.filter(status='Pending').count(),
            'ready_orders_count': Order.objects.filter(status='Ready').count(),
        }
        return render(request, 'OrderMaster/dashboard.html', context)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        messages.error(request, 'Error loading dashboard data.')
        return render(request, 'OrderMaster/dashboard.html', {})


@admin_required
def order_management_view(request):
    """ Renders the order management page (Kanban board). """
    # This view now just renders the template. Data is loaded via API.
    return render(request, 'OrderMaster/order_management.html')

@admin_required
def menu_management_view(request):
    """ Handles adding new menu items and displaying the list. """
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item added successfully!')
            return redirect('menu_management')
        else:
            messages.error(request, 'Error adding menu item. Please check the form.')
    else:
        form = MenuItemForm() # For displaying the empty form on GET

    menu_items = MenuItem.objects.all().order_by('name')
    context = {'menu_items': menu_items, 'form': form}
    return render(request, 'OrderMaster/menu_management.html', context)

@admin_required
def edit_menu_item_view(request, item_id):
    """ Handles editing an existing menu item. """
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated successfully!')
            return redirect('menu_management')
        else:
            messages.error(request, 'Error updating menu item. Please check the form.')
    else:
        form = MenuItemForm(instance=item) # Pre-populate form on GET

    return render(request, 'OrderMaster/edit_menu_item.html', {'form': form, 'item': item})

@admin_required
@require_POST # Ensure delete is only via POST
def delete_menu_item_view(request, item_id):
    """ Handles deleting a menu item. """
    try:
        item = get_object_or_404(MenuItem, id=item_id)
        item.delete()
        messages.success(request, 'Menu item deleted successfully!')
    except Exception as e:
        logger.error(f"Error deleting menu item {item_id}: {e}")
        messages.error(request, 'Error deleting menu item.')
    return redirect('menu_management')


@admin_required
def analytics_view(request):
    """ Renders the analytics page. """
    # Basic analytics data (can be expanded)
    context = {
        'total_orders': Order.objects.count(),
        'completed_orders': Order.objects.filter(status='Completed').count(),
    }
    return render(request, 'OrderMaster/analytics.html', context)

@admin_required
def settings_view(request):
    """ Renders the settings page. """
    # Add context for settings if needed
    return render(request, 'OrderMaster/settings.html')

# =================================================================================
# API FOR REAL-TIME ORDER BOARD & TOKEN MANAGEMENT
# =================================================================================

@admin_required
@require_GET
def get_orders_api(request):
    """ API to fetch and separate orders for the Kanban board. """
    try:
        preparing = Order.objects.filter(status='Pending').order_by('created_at')
        ready = Order.objects.filter(status='Ready').order_by('-ready_time') # Show newest ready first

        preparing_data = [{
            'id': order.id,
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'items': order.items, # Already a dict {name: qty} from api_place_order
            'total_amount': f"{order.total_amount:.2f}",
            'created_at_iso': order.created_at.isoformat(),
            'created_at_formatted': order.created_at.strftime('%b %d, %I:%M %p')
        } for order in preparing]

        ready_data = [{
            'id': order.id,
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'items': order.items,
            'total_amount': f"{order.total_amount:.2f}",
            'ready_time_iso': order.ready_time.isoformat() if order.ready_time else '',
            'ready_time_formatted': order.ready_time.strftime('%I:%M %p') if order.ready_time else '' # Shorter time format
        } for order in ready]

        return JsonResponse({'preparing_orders': preparing_data, 'ready_orders': ready_data})
    except Exception as e:
        logger.error(f"API get_orders error: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)


@csrf_exempt
@admin_required
@require_POST
def update_order_status(request):
    """ API to update an order's status ('Pending' -> 'Ready' or 'Ready' -> 'Completed'). """
    try:
        data = json.loads(request.body)
        order_pk = data.get('id')
        new_status = data.get('status')

        if not all([order_pk, new_status]):
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
             return JsonResponse({'success': False, 'error': 'Invalid status provided'}, status=400)

        order = get_object_or_404(Order, pk=order_pk)

        # Basic state transition validation
        if order.status == 'Pending' and new_status != 'Ready':
             return JsonResponse({'success': False, 'error': 'Can only mark Pending orders as Ready.'}, status=400)
        if order.status == 'Ready' and new_status != 'Completed':
             return JsonResponse({'success': False, 'error': 'Can only mark Ready orders as Completed.'}, status=400)
        if order.status == 'Completed' or order.status == 'Cancelled':
             return JsonResponse({'success': False, 'error': 'Order is already finalized.'}, status=400)


        order.status = new_status
        if new_status == 'Ready':
            order.ready_time = timezone.now()
        # Add logic for 'Completed' timestamp if needed

        order.save()
        return JsonResponse({'success': True, 'message': f'Order status updated to {new_status}'})

    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'}, status=500)


@csrf_exempt
@require_POST
def subscribe_to_topic(request):
    """ Subscribes a device token to the 'new_orders' topic. """
    try:
        data = json.loads(request.body)
        token = data.get('token')
        if not token:
            return JsonResponse({'success': False, 'error': 'Token is required.'}, status=400)

        if firebase_admin._apps: # Check if initialized
            response = messaging.subscribe_to_topic([token], 'new_orders')
            logger.info(f'Successfully subscribed token to new_orders topic: {response}')
            return JsonResponse({'success': True, 'message': 'Successfully subscribed to notifications.'})
        else:
            logger.warning("Firebase not initialized, cannot subscribe token.")
            return JsonResponse({'success': False, 'error': 'Notification service not available.'}, status=503)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        logger.error(f"Error subscribing token to topic: {e}")
        return JsonResponse({'success': False, 'error': 'Failed to subscribe.'}, status=500)
