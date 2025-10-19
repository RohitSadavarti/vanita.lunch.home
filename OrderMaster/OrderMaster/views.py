# =================================================================================
# IMPORTS
# =================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import MenuItem, Order, VlhAdmin
from .forms import MenuItemForm # Assuming you have forms.py
from .decorators import admin_required
from datetime import datetime, timedelta
from django.db.models import Count, Sum
from collections import Counter
import os
import json
import uuid
from decimal import Decimal
import logging

# Firebase Admin Imports
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

logger = logging.getLogger(__name__)

# =================================================================================
# FIREBASE INITIALIZATION
# =================================================================================
try:
    if not firebase_admin._apps:
        # Using environment variable set in Render
        firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
        if firebase_creds_json:
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK initialized with service account from ENV")
        else:
            # Fallback for local development (if file exists)
            cred_path = os.path.join(settings.BASE_DIR, 'vanita-lunch-home-firebase-adminsdk-hdk0i-9b377484a9.json')
            if os.path.exists(cred_path):
                 cred = credentials.Certificate(cred_path)
                 firebase_admin.initialize_app(cred)
                 logger.info("✅ Firebase Admin SDK initialized with service account from file (local)")
            else:
                logger.error("Firebase credentials not found in ENV or file.")
except Exception as e:
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
                request.session.set_expiry(1209600) # Optional: 2 weeks expiry
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
        # Assuming 'firebase-messaging-sw.js' is in your root templates directory
        # or OrderMaster/templates/firebase-messaging-sw.js
        return render(request, 'firebase-messaging-sw.js', content_type='application/javascript')
    except Exception as e:
        logger.error(f"Error serving firebase-messaging-sw.js: {e}")
        return HttpResponse("/* Error serving service worker. */", status=500, content_type="application/javascript")

# =================================================================================
# CUSTOMER-FACING VIEWS & API
# =================================================================================

def customer_order_view(request):
    """ Renders the main customer ordering page. """
    menu_items = MenuItem.objects.all()
    context = {'menu_items': menu_items}
    return render(request, 'OrderMaster/customer_order.html', context)

@require_GET
def api_menu_items(request):
    """ API endpoint providing the full menu list (e.g., for Flutter or JS). """
    try:
        menu_items = MenuItem.objects.all().values(
            'id', 'name', 'price', 'image'
        ).order_by('name')
        items_list = [
            {
                **item,
                'price': float(item['price']),
                # Construct absolute URL for images
                'image_url': request.build_absolute_uri(settings.MEDIA_URL + item['image']) if item.get('image') else None
            }
            for item in menu_items
        ]
        return JsonResponse(items_list, safe=False)
    except Exception as e:
        logger.error(f"API menu items error: {e}")
        return JsonResponse({'error': 'Server error occurred.'}, status=500)

@csrf_exempt # CSRF needed if using session auth, but exempt if using tokens (like for mobile app)
@require_http_methods(["GET", "PUT", "DELETE"]) # Handle different methods for detail view
def api_menu_item_detail(request, item_id):
    """ API endpoint for retrieving, updating, or deleting a single menu item. """
    try:
        item = get_object_or_404(MenuItem, pk=item_id)
    except Http404:
        return JsonResponse({'error': 'Menu item not found.'}, status=404)

    if request.method == 'GET':
        data = {
            'id': item.id,
            'name': item.name,
            'price': float(item.price),
            'image_url': request.build_absolute_uri(settings.MEDIA_URL + item.image.name) if item.image else None
        }
        return JsonResponse(data)

    # --- Add PUT and DELETE methods if needed for Flutter ---
    # Example PUT (Update):
    # elif request.method == 'PUT':
    #     try:
    #         data = json.loads(request.body)
    #         # Update item fields based on data...
    #         # form = MenuItemForm(data, instance=item) # If using forms
    #         # if form.is_valid(): form.save(); return JsonResponse({...})
    #         item.name = data.get('name', item.name)
    #         item.price = data.get('price', item.price)
    #         item.save()
    #         return JsonResponse({'success': True, 'message': 'Item updated.'})
    #     except Exception as e:
    #         return JsonResponse({'error': f'Update failed: {e}'}, status=400)

    # Example DELETE:
    # elif request.method == 'DELETE':
    #     try:
    #         item.delete()
    #         return JsonResponse({'success': True, 'message': 'Item deleted.'})
    #     except Exception as e:
    #          return JsonResponse({'error': f'Delete failed: {e}'}, status=500)

    else:
        return JsonResponse({'error': 'Method not allowed.'}, status=405)


@csrf_exempt
@require_POST
def api_place_order(request):
    """ API endpoint for customers placing orders. """
    try:
        data = json.loads(request.body)
        items_data = data.get('items') # Expecting list like [{'id': 1, 'quantity': 2}, ...]
        customer_name = data.get('customer_name', 'Anonymous')
        total_amount_client = Decimal(str(data.get('total_amount', '0.00')))

        if not items_data or total_amount_client <= 0:
            return JsonResponse({'status': 'error', 'message': 'Missing items or invalid total.'}, status=400)

        # Server-side calculation
        calculated_total = Decimal('0.00')
        validated_items_for_db = {}
        item_ids = [item.get('id') for item in items_data if item.get('id')]
        menu_items_from_db = MenuItem.objects.filter(id__in=item_ids)
        menu_items_dict = {item.id: item for item in menu_items_from_db}

        for item_data in items_data:
            item_id = item_data.get('id')
            quantity = int(item_data.get('quantity', 0))
            db_item = menu_items_dict.get(item_id)

            if db_item and quantity > 0:
                calculated_total += db_item.price * quantity
                validated_items_for_db[db_item.name] = quantity
            else:
                 logger.warning(f"Invalid item or quantity skipped: ID {item_id}, Qty {quantity}")

        if abs(calculated_total - total_amount_client) > Decimal('0.01'):
            logger.error(f"Total mismatch. Client: {total_amount_client}, Server: {calculated_total}")
            return JsonResponse({'status': 'error', 'message': 'Total amount mismatch.'}, status=400)

        # Create Order
        order = Order.objects.create(
            order_id=str(uuid.uuid4()).split('-')[0].upper(),
            customer_name=customer_name,
            items=validated_items_for_db,
            total_amount=calculated_total,
            payment_id=data.get('payment_id', 'COD'),
            created_at=timezone.now(),
            status='Pending'
        )

        # Send push notification
        try:
            if firebase_admin._apps:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title='New Order Received!',
                        body=f'Order #{order.order_id} from {customer_name} for ₹{calculated_total:.2f}.'
                    ),
                    topic='new_orders'
                )
                messaging.send(message)
                logger.info('Successfully sent FCM message')
            else:
                logger.warning("Firebase not initialized, skipping notification.")
        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}")

        return JsonResponse({'status': 'success', 'order_id': order.order_id})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        logger.error(f"Place order API error: {e}")
        return JsonResponse({'status': 'error', 'message': 'Server error.'}, status=500)

# =================================================================================
# ADMIN PAGES
# =================================================================================

@admin_required
def dashboard_view(request):
    """ Renders the main admin dashboard page. """
    context = {} # Add dashboard data if needed
    return render(request, 'OrderMaster/dashboard.html', context)

@admin_required
def order_management_view(request):
    """ Renders the order management page (Kanban board). """
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
            messages.error(request, 'Error adding item.')
    else:
        form = MenuItemForm()

    menu_items = MenuItem.objects.all().order_by('name')
    context = {'menu_items': menu_items, 'form': form}
    return render(request, 'OrderMaster/menu_management.html', context)

@admin_required
def edit_menu_item_view(request, item_id):
    """ Handles editing an existing menu item via web form. """
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated successfully!')
            return redirect('menu_management')
        else:
            messages.error(request, 'Error updating item.')
    else:
        form = MenuItemForm(instance=item)

    return render(request, 'OrderMaster/edit_menu_item.html', {'form': form, 'item': item})

@admin_required
@require_POST # Ensure delete is only via POST
def delete_menu_item_view(request, item_id):
    """ Handles deleting a menu item via web form. """
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
    return render(request, 'OrderMaster/analytics.html')

@admin_required
def settings_view(request):
    """ Renders the settings page. """
    return render(request, 'OrderMaster/settings.html')

# =================================================================================
# API VIEWS needed for 404 errors
# =================================================================================

@admin_required
@require_GET
def analytics_data_api(request):
    """ Placeholder API view for analytics data. """
    # Replace with your actual analytics data logic
    try:
        # Example Data
        total_orders = Order.objects.count()
        completed_orders = Order.objects.filter(status='Completed').count()
        pending_orders = Order.objects.filter(status='Pending').count()
        ready_orders = Order.objects.filter(status='Ready').count()
        total_revenue = Order.objects.filter(status='Completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # Example: Most popular items
        all_items = []
        completed_orders_list = Order.objects.filter(status='Completed').values_list('items', flat=True)
        for items_dict in completed_orders_list:
            if isinstance(items_dict, dict): # Check if it's the expected dict
                 all_items.extend(items_dict.keys()) # Add item names
        item_counts = Counter(all_items)
        popular_items = item_counts.most_common(5) # Top 5 items

        data = {
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'ready_orders': ready_orders,
            'total_revenue': float(total_revenue),
            'popular_items': popular_items,
            # Add more data as needed (e.g., daily/weekly trends)
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Analytics data API error: {e}")
        return JsonResponse({'error': 'Failed to fetch analytics data'}, status=500)


@admin_required
@require_GET
def get_orders_api(request):
    """ API to fetch and separate orders for the Kanban board. """
    try:
        preparing = Order.objects.filter(status='Pending').order_by('created_at')
        ready = Order.objects.filter(status='Ready').order_by('-ready_time')

        preparing_data = [{
            'id': order.id,
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'items': order.items,
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
            'ready_time_formatted': order.ready_time.strftime('%I:%M %p') if order.ready_time else ''
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

        order = get_object_or_404(Order, pk=order_pk)

        # Basic state validation
        if order.status == 'Pending' and new_status == 'Ready':
            order.status = new_status
            order.ready_time = timezone.now()
        elif order.status == 'Ready' and new_status == 'Completed':
            order.status = new_status
            # Add completion time if needed: order.completed_time = timezone.now()
        elif new_status == 'Cancelled': # Allow cancellation from Pending or Ready
             if order.status in ['Pending', 'Ready']:
                 order.status = new_status
             else:
                  return JsonResponse({'success': False, 'error': f'Cannot cancel order with status {order.status}.'}, status=400)
        else:
            # Invalid transition
            return JsonResponse({'success': False, 'error': f'Invalid status transition from {order.status} to {new_status}.'}, status=400)

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

        if firebase_admin._apps:
            response = messaging.subscribe_to_topic([token], 'new_orders')
            logger.info(f'Successfully subscribed token to new_orders topic: {response}')
            return JsonResponse({'success': True, 'message': 'Successfully subscribed.'})
        else:
            logger.warning("Firebase not initialized.")
            return JsonResponse({'success': False, 'error': 'Notification service unavailable.'}, status=503)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        logger.error(f"Error subscribing token: {e}")
        return JsonResponse({'success': False, 'error': 'Failed to subscribe.'}, status=500)