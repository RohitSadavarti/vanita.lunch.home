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
import json
import uuid
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings # Import settings
import os # Import os

logger = logging.getLogger(__name__)

# =================================================================================
# FIREBASE INITIALIZATION (Run only once)
# =================================================================================
try:
    # Construct the full path to the credentials file
    cred_path = os.path.join(settings.BASE_DIR, 'vanita-lunch-home-firebase-adminsdk-hdk0i-9b377484a9.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
    else:
        logger.error(f"Firebase credentials file not found at: {cred_path}")
except Exception as e:
    logger.error(f"Error initializing Firebase Admin SDK: {e}")

# =================================================================================
# DECORATORS & AUTHENTICATION
# =================================================================================

def admin_required(view_func):
    """
    Custom decorator to ensure that a user is an authenticated admin.
    """
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.warning(request, 'You must be logged in to view this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def login_view(request):
    """Handles the admin login with the custom VlhAdmin model."""
    if request.method == 'POST':
        mobile = request.POST.get('username')  # The form uses 'username' for the mobile field
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
    """Clears the session to log the admin out."""
    request.session.flush()
    messages.info(request, 'You have been successfully logged out.')
    return redirect('login')


# =================================================================================
# FIREBASE MESSAGING SERVICE WORKER VIEW
# =================================================================================

# This needs correct indentation
@require_GET # Ensure this is a GET request
def firebase_messaging_sw(request):
    """
    Serves the Firebase Messaging Service Worker file.
    Ensure this file exists in your templates directory.
    """
    try:
        # Assuming 'firebase-messaging-sw.js' is in the root of your templates dir
        # or within OrderMaster/templates/firebase-messaging-sw.js
        # Adjust the path if necessary.
        return render(request, 'firebase-messaging-sw.js', content_type='application/javascript')
    except Exception as e:
        logger.error(f"Error serving firebase-messaging-sw.js: {e}")
        return HttpResponse("Error serving service worker.", status=500, content_type="text/plain")


# =================================================================================
# CUSTOMER-FACING VIEWS
# =================================================================================

def customer_order_view(request):
    """
    Renders the customer order page and handles order placement via POST request.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items')
            customer_name = data.get('customer_name', 'Anonymous')
            total_amount = data.get('total_amount')

            if not all([items, customer_name, total_amount]):
                 return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

            order = Order.objects.create(
                order_id=str(uuid.uuid4()).split('-')[0].upper(),
                customer_name=customer_name,
                items=items,
                total_amount=total_amount,
                payment_id=data.get('payment_id', 'COD'),
                created_at=timezone.now(),
                status='Pending' # New orders are always 'Pending'
            )

            # Send push notification
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title='New Order Received!',
                        body=f'Order #{order.order_id} from {customer_name} for ₹{total_amount}.'
                    ),
                    topic='new_orders' # Send to the 'new_orders' topic
                )
                response = messaging.send(message)
                logger.info(f'Successfully sent FCM message: {response}')
            except Exception as e:
                logger.error(f"Error sending FCM notification: {e}")


            return JsonResponse({'status': 'success', 'order_id': order.order_id})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Customer order placement error: {e}")
            return JsonResponse({'status': 'error', 'message': 'Server error'}, status=500)

    menu_items = MenuItem.objects.all()
    return render(request, 'OrderMaster/customer_order.html', {'menu_items': menu_items})

# =================================================================================
# ADMIN PAGES
# =================================================================================

@admin_required
def dashboard_view(request):
    """Renders the main admin dashboard page."""
    return render(request, 'OrderMaster/dashboard.html')

@admin_required
def order_management_view(request):
    """Renders the order management page which will be updated in real-time."""
    return render(request, 'OrderMaster/order_management.html')

@admin_required
def menu_management_view(request):
    """Handles adding new menu items and displaying all items."""
    if request.method == 'POST':
        MenuItem.objects.create(
            name=request.POST['name'],
            price=request.POST['price'],
            image=request.FILES.get('image')
        )
        messages.success(request, 'Menu item added successfully!')
        return redirect('menu_management')

    menu_items = MenuItem.objects.all()
    return render(request, 'OrderMaster/menu_management.html', {'menu_items': menu_items})

@admin_required
def edit_menu_item_view(request, item_id):
    """Handles editing an existing menu item."""
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        item.name = request.POST.get('name')
        item.price = request.POST.get('price')
        if 'image' in request.FILES:
            item.image = request.FILES.get('image')
        item.save()
        messages.success(request, 'Menu item updated successfully!')
        return redirect('menu_management')
    return render(request, 'OrderMaster/edit_menu_item.html', {'item': item})

@admin_required
def delete_menu_item_view(request, item_id):
    """Handles deleting a menu item."""
    # Ensure this is a POST request for safety
    if request.method == 'POST':
        try:
            item = get_object_or_404(MenuItem, id=item_id)
            item.delete()
            messages.success(request, 'Menu item deleted successfully!')
        except Exception as e:
             logger.error(f"Error deleting menu item {item_id}: {e}")
             messages.error(request, 'Error deleting menu item.')
    else:
        messages.error(request, 'Invalid request method for deleting.')
    return redirect('menu_management')


@admin_required
def analytics_view(request):
    """Renders the analytics page."""
    return render(request, 'OrderMaster/analytics.html')

@admin_required
def settings_view(request):
    """Renders the settings page."""
    return render(request, 'OrderMaster/settings.html')

# =================================================================================
# API FOR REAL-TIME ORDER BOARD & TOKEN MANAGEMENT
# =================================================================================

@admin_required
def get_orders_api(request):
    """API to fetch and separate orders for the Kanban board."""
    try:
        # Orders that are new and need preparation
        preparing = Order.objects.filter(status='Pending').order_by('created_at')

        # Orders that are ready for pickup
        ready = Order.objects.filter(status='Ready').order_by('-ready_time')

        preparing_data = [{
            'id': order.id, # Use the actual PK for updates
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'items': order.items,
            'total_amount': f"{order.total_amount:.2f}",
            'created_at_iso': order.created_at.isoformat(),
            'created_at_formatted': order.created_at.strftime('%b %d, %Y, %I:%M %p') # Added formatted time
        } for order in preparing]

        ready_data = [{
            'id': order.id,
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'items': order.items,
            'total_amount': f"{order.total_amount:.2f}",
            'ready_time_iso': order.ready_time.isoformat() if order.ready_time else '',
            'ready_time_formatted': order.ready_time.strftime('%b %d, %Y, %I:%M %p') if order.ready_time else '' # Added formatted time
        } for order in ready]

        return JsonResponse({'preparing_orders': preparing_data, 'ready_orders': ready_data})
    except Exception as e:
        logger.error(f"API get_orders error: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)


@csrf_exempt # Exempt CSRF for this API endpoint if called via JS fetch
@admin_required
@require_POST
def update_order_status(request):
    """API to update an order's status, e.g., from 'Pending' to 'Ready' or 'Completed'."""
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
        order.status = new_status

        if new_status == 'Ready':
            order.ready_time = timezone.now()
        # You might add logic here if 'Completed' needs a timestamp too

        order.save()
        return JsonResponse({'success': True, 'message': f'Order status updated to {new_status}'})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'}, status=500)


@csrf_exempt # Exempt CSRF for API endpoint
@require_POST
def subscribe_to_topic(request):
    """Subscribes a device token to the 'new_orders' topic."""
    try:
        data = json.loads(request.body)
        token = data.get('token')
        if not token:
            return JsonResponse({'success': False, 'error': 'Token is required.'}, status=400)

        # Subscribe the token to the 'new_orders' topic
        response = messaging.subscribe_to_topic([token], 'new_orders')
        logger.info(f'Successfully subscribed token to new_orders topic: {response}')
        return JsonResponse({'success': True, 'message': 'Successfully subscribed to notifications.'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        logger.error(f"Error subscribing token to topic: {e}")
        return JsonResponse({'success': False, 'error': 'Failed to subscribe.'}, status=500)
