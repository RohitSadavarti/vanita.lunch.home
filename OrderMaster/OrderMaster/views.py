# OrderMaster/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
# Import ensure_csrf_cookie
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.utils import timezone
# Import models from .models
# --- FIX: Removed 'Customer' which does not exist in models.py ---
from .models import MenuItem, Order, VlhAdmin, models
from .forms import MenuItemForm
from .decorators import admin_required
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q
from collections import Counter
import os
import io
import json
import random
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
try:
    if not firebase_admin._apps:
        firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')

        if firebase_creds:
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
    return render(request, 'firebase-messaging-sw.js', content_type='application/javascript')


# --- CLEANUP: Removed duplicate `handle_order_action` function ---
# The other version at line 498 is the "Updated" one.

# --- CLEANUP: Removed redundant `admin_required` function ---
# This was already imported from .decorators
# def admin_required(view_func):
# ... (removed) ...


# ============================================================================
# --- CRITICAL FIX: Updated login_view to handle JSON and 'mobile' ---
# ============================================================================
@ensure_csrf_cookie # Ensure CSRF cookie is set for API calls
def login_view(request):
    """
    Handles login for both web (form-data) and app (JSON).
    """
    if request.session.get('is_authenticated'):
        logger.debug("User already authenticated, redirecting to dashboard.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        data = {}
        mobile = None
        password = None

        try:
            # Check if data is JSON (from Flutter app)
            if 'application/json' in request.content_type:
                data = json.loads(request.body)
                mobile = data.get('mobile') # Use 'mobile' key
                password = data.get('password')
                logger.info(f"API Login attempt for mobile: {mobile}")
            # Else, assume form data (from web)
            else:
                mobile = request.POST.get('mobile') # Use 'mobile' key
                password = request.POST.get('password')
                logger.info(f"Web Login attempt for mobile: {mobile}")
        
        except json.JSONDecodeError:
            logger.warning("Login attempt failed: Invalid JSON")
            if 'application/json' in request.content_type:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            else:
                messages.error(request, 'Invalid request.')
                return render(request, 'OrderMaster/login.html')

        if not mobile or not password:
             logger.warning("Login attempt failed: Missing mobile or password.")
             if 'application/json' in request.content_type:
                 return JsonResponse({'error': 'Mobile and password are required.'}, status=400)
             else:
                messages.error(request, 'Mobile number and password are required.')
                return render(request, 'OrderMaster/login.html')

        try:
            admin_user = VlhAdmin.objects.get(mobile=mobile) 
            logger.debug(f"Found admin user for mobile: {mobile}")
            
            if admin_user.check_password(password):
                request.session['is_authenticated'] = True
                request.session['admin_mobile'] = admin_user.mobile
                logger.info(f"Login successful for mobile: {mobile}")
                
                if 'application/json' in request.content_type:
                    # For Flutter app, return JSON success
                    return JsonResponse({'success': True, 'message': 'Login successful'})
                else:
                    # For web, redirect to dashboard
                    return redirect('dashboard') 
            else:
                logger.warning(f"Login failed: Incorrect password for mobile: {mobile}")
                if 'application/json' in request.content_type:
                    return JsonResponse({'error': 'Invalid mobile number or password.'}, status=401)
                else:
                    messages.error(request, 'Invalid mobile number or password.')
        except VlhAdmin.DoesNotExist:
            logger.warning(f"Login failed: No admin user found for mobile: {mobile}")
            if 'application/json' in request.content_type:
                return JsonResponse({'error': 'Invalid mobile number or password.'}, status=401)
            else:
                messages.error(request, 'Invalid mobile number or password.')
        except Exception as e:
             logger.error(f"Login error for mobile {mobile}: {e}", exc_info=True)
             if 'application/json' in request.content_type:
                 return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)
             else:
                messages.error(request, 'An unexpected error occurred during login.')

    # For GET request
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

from django.db.models.functions import TruncHour, TruncDay, Lower
from django.db.models import Count

def analytics_api_view(request):
    """API endpoint for analytics data with proper error handling."""
    try:
        # Get filters from the request
        date_filter = request.GET.get('date_filter', 'this_month')
        payment_filter = request.GET.get('payment_filter', 'Total')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        print(f"[v0] Analytics API called with filters: date={date_filter}, payment={payment_filter}")

        now = timezone.now()
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
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
        else:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        counter_orders_q = Q(order_placed_by='counter')
        customer_orders_q = Q(order_placed_by='customer', order_status='pickedup')
        combined_q = counter_orders_q | customer_orders_q
        base_completed_orders = Order.objects.filter(
            created_at__range=(start_date, end_date)
            ).filter(combined_q)
        
        filtered_orders = base_completed_orders
        if payment_filter != 'Total':
            filtered_orders = base_completed_orders.filter(payment_method__iexact=payment_filter)

        total_revenue = filtered_orders.aggregate(total=Sum('total_price'))['total'] or 0
        total_orders_count = filtered_orders.count()
        average_order_value = total_revenue / total_orders_count if total_orders_count > 0 else 0

        item_counter = Counter()
        for order in filtered_orders:
            items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
            if isinstance(items_list, list):
                for item in items_list:
                    item_counter[item.get('name', 'Unknown')] += item.get('quantity', 0)
        most_common_items = item_counter.most_common(5)
        top_5_names = [item[0] for item in most_common_items]

        payment_distribution = filtered_orders.annotate(
            payment_method_lower=Lower('payment_method')
        ).values(
            'payment_method_lower'
        ).annotate(
            total=Sum('total_price')
        ).order_by('-total')
        order_source_distribution = base_completed_orders.values('order_placed_by').annotate(count=Count('id')).order_by('-count')
        orders_by_hour = filtered_orders.annotate(hour=TruncHour('created_at')).values('hour').annotate(count=Count('id')).order_by('hour')
        
        day_wise_revenue = filtered_orders.annotate(day=TruncDay('created_at')).values('day').annotate(
            revenue=Sum('total_price'),
            orders=Count('id')
        ).order_by('day')

        day_wise_menu_query = filtered_orders.annotate(day=TruncDay('created_at')).values('day').order_by('day').distinct()
        day_labels = [d['day'].strftime('%d %b') for d in day_wise_menu_query]
        
        datasets = {name: [0] * len(day_labels) for name in top_5_names}
        for i, day_label in enumerate(day_labels):
            day_date = datetime.strptime(day_label + f' {start_date.year}', '%d %b %Y').date()
            orders_on_day = filtered_orders.filter(created_at__date=day_date)
            daily_item_counter = Counter()
            for order in orders_on_day:
                items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
                if isinstance(items_list, list):
                    for item in items_list:
                        if item.get('name') in top_5_names:
                            daily_item_counter[item.get('name')] += item.get('quantity', 0)
            for name in top_5_names:
                datasets[name][i] = daily_item_counter[name]

        day_wise_menu_datasets = []
        colors = ['#1e40af', '#059669', '#d97706', '#9333ea', '#64748b']
        for i, name in enumerate(top_5_names):
            day_wise_menu_datasets.append({
                'label': name,
                'data': datasets[name],
                'backgroundColor': colors[i % len(colors)]
            })

        table_orders = filtered_orders.order_by('-created_at')[:100]
        table_data = []
        for order in table_orders:
            items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
            items_text = ", ".join([f"{item['quantity']}x {item['name']}" for item in items_list]) if isinstance(items_list, list) else ""
            table_data.append({
                'created_at': order.created_at.isoformat(),
                'order_id': order.order_id,
                'items_text': items_text,
                'total_price': float(order.total_price),
                'payment_method': order.payment_method,
                'order_status': order.status,
                'order_placed_by': order.order_placed_by,  # Include order source in analytics
            })
            
        data = {
            'key_metrics': {
                'total_revenue': float(total_revenue),
                'total_orders': total_orders_count,
                'average_order_value': float(average_order_value),
            },
            'most_ordered_items': {
                'labels': [item[0] for item in most_common_items],
                'data': [item[1] for item in most_common_items],
            },
            'payment_method_distribution': {
                'labels': [item['payment_method_lower'] for item in payment_distribution],
                'data': [float(item['total']) for item in payment_distribution],
            },
            'order_source_distribution': {
                'labels': [item['order_placed_by'] for item in order_source_distribution],
                'data': [item['count'] for item in order_source_distribution],
            },
            'orders_by_hour': {
                'labels': [h['hour'].strftime('%I %p').lstrip('0') if h['hour'] else 'N/A' for h in orders_by_hour],
                'data': [h['count'] for h in orders_by_hour],
            },
            'day_wise_revenue': {
                'labels': [d['day'].strftime('%d %b') for d in day_wise_revenue],
                'revenue_data': [float(d['revenue']) for d in day_wise_revenue],
                'orders_data': [d['orders'] for d in day_wise_revenue],
            },
            'day_wise_menu': {
                'labels': day_labels,
                'datasets': day_wise_menu_datasets,
            },
            'table_data': table_data,
        }
        logger.info(f"[v0] Analytics data prepared successfully")
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"[v0] Error in analytics_api_view: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Server error occurred while fetching analytics data.',
            'details': str(e)
        }, status=500)
    
@admin_required
def order_management_view(request):
    date_filter = request.GET.get('date_filter', 'today')
    # --- REMOVED source_filter ---
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
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        date_filter = 'today'

    base_orders = Order.objects.filter(created_at__range=(start_date, end_date))
    
    # --- NEW: Split queries by order_placed_by ---

    # 1. Online Orders (for 3-column layout)
    online_orders_base = base_orders.filter(order_placed_by='customer')
    preparing_orders = online_orders_base.filter(order_status='open')
    ready_orders = online_orders_base.filter(order_status='ready')
    pickedup_orders = online_orders_base.filter(order_status='pickedup')

    # 2. Counter Orders (for single list layout)
    counter_orders_all = base_orders.filter(order_placed_by='counter').order_by('-created_at')

    # --- Process items_list for all fetched orders ---
    for order in preparing_orders:
        order.items_list = order.items if isinstance(order.items, list) else json.loads(order.items)
    for order in ready_orders:
        order.items_list = order.items if isinstance(order.items, list) else json.loads(order.items)
    for order in pickedup_orders:
        order.items_list = order.items if isinstance(order.items, list) else json.loads(order.items)
    for order in counter_orders_all:
        order.items_list = order.items if isinstance(order.items, list) else json.loads(order.items)


    context = {
        # Online (Customer) Orders
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'pickedup_orders': pickedup_orders,
        
        # Counter Orders
        'counter_orders_all': counter_orders_all,

        # Filters and Page Metadata
        'date_display_str': date_filter.replace('_', ' ').title(),
        'selected_filter': date_filter,
        # 'source_filter': source_filter, # Removed
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

        response_data = {'success': True}
        
        if new_status == 'ready':
            order.ready_time = timezone.now()
            response_data['ready_time'] = order.ready_time.isoformat()
        elif new_status == 'pickedup':
            order.pickup_time = timezone.now()
            response_data['pickup_time'] = order.pickup_time.isoformat()

        order.save()
        return JsonResponse(response_data)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
@admin_required
def menu_management_view(request):
    if request.method == 'POST':
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

@csrf_exempt  # ← ADD THIS
@require_http_methods(['GET', 'PUT', 'POST', 'DELETE'])  # ← ADD THIS
def api_menu_item_detail(request, item_id):
    """
    API endpoint for menu item details.
    Handles GET, PUT, POST, and DELETE requests.
    """
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
            'image_url': item.image_url if item.image_url else ''
        }
        return JsonResponse(data)

    if request.method in ['POST', 'PUT']:
        # Parse request body
        try:
            if request.content_type and 'application/json' in request.content_type:
                data = json.loads(request.body)
            elif request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
                # Handle form-urlencoded data from Flutter
                data = {}
                for key, value in request.POST.items():
                    data[key] = value
            else:
                data = request.POST.dict()
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        
        # Update the menu item
        item.item_name = data.get('item_name', item.item_name)
        item.description = data.get('description', item.description)
        
        # Handle price conversion
        try:
            price_value = data.get('price', item.price)
            item.price = float(price_value) if price_value else item.price
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid price format'}, status=400)
        
        item.category = data.get('category', item.category)
        item.veg_nonveg = data.get('veg_nonveg', item.veg_nonveg)
        item.meal_type = data.get('meal_type', item.meal_type)
        item.availability_time = data.get('availability_time', item.availability_time)
        item.image_url = data.get('image_url', item.image_url)
        
        try:
            item.save()
            logger.info(f"[v0] Successfully updated menu item {item_id}")
            return JsonResponse({
                'success': True, 
                'message': 'Item updated successfully!', 
                'id': item.id
            })
        except Exception as e:
            logger.error(f"[v0] Error updating menu item {item_id}: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    if request.method == 'DELETE':
        try:
            item.delete()
            logger.info(f"[v0] Successfully deleted menu item {item_id}")
            return JsonResponse({'success': True, 'message': 'Item deleted successfully!'})
        except Exception as e:
            logger.error(f"[v0] Error deleting menu item {item_id}: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

# ============================================================================
# CRITICAL FIX: This is the endpoint your Flutter app is calling
# ============================================================================
@csrf_exempt  # ← ADD THIS
@require_http_methods(['GET', 'POST'])  # ← ADD THIS
def api_menu_items(request):
    """
    API endpoint for menu items.
    GET: Returns all menu items
    POST: Creates a new menu item
    """
    
    # GET request - fetch all menu items
    if request.method == 'GET':
        try:
            logger.info("📡 API /api/menu-items/ GET called")
            
            # Get all menu items from database
            menu_items = MenuItem.objects.all().order_by('category', 'item_name')
            
            logger.info(f"✅ Found {menu_items.count()} menu items in database")
            
            # Convert to list of dictionaries
            items_list = []
            for item in menu_items:
                items_list.append({
                    'id': item.id,
                    'item_name': item.item_name,
                    'description': item.description or '',
                    'price': float(item.price),
                    'category': item.category,
                    'veg_nonveg': item.veg_nonveg,
                    'meal_type': item.meal_type,
                    'availability_time': item.availability_time or '',
                    'image_url': item.image_url or ''
                })
            
            # Return in the format Flutter expects: {'menu_items': [...]}
            response_data = {'menu_items': items_list}
            
            logger.info(f"✅ Returning {len(items_list)} items in response")
            return JsonResponse(response_data, safe=False)
            
        except Exception as e:
            logger.error(f"❌ Error in api_menu_items GET: {e}", exc_info=True)
            return JsonResponse({
                'error': 'Server error occurred while fetching menu items.',
                'details': str(e)
            }, status=500)
    
    # POST request - create new menu item
    elif request.method == 'POST':
        try:
            # Check authentication
            if not request.session.get('is_authenticated'):
                logger.warning("[v0] Unauthorized add menu item attempt")
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            logger.info("📡 API /api/menu-items/ POST called")
            
            # Parse request body
            try:
                if request.content_type and 'application/json' in request.content_type:
                    data = json.loads(request.body)
                elif request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
                    data = {}
                    for key, value in request.POST.items():
                        data[key] = value
                else:
                    data = request.POST.dict()
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
            
            logger.info(f"[v0] Add menu data received: {data}")
            
            # Validate required fields
            required_fields = ['item_name', 'price', 'category']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False, 
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            # Convert price to float
            try:
                price = float(data.get('price'))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False, 
                    'error': 'Invalid price format'
                }, status=400)
            
            # Create new menu item
            new_item = MenuItem.objects.create(
                item_name=data.get('item_name'),
                description=data.get('description', ''),
                price=price,
                category=data.get('category'),
                veg_nonveg=data.get('veg_nonveg', 'Veg'),
                meal_type=data.get('meal_type', 'All Day'),
                availability_time=data.get('availability_time', ''),
                image_url=data.get('image_url', '')
            )
            
            logger.info(f"[v0] Successfully created menu item: {new_item.item_name} (ID: {new_item.id})")
            
            return JsonResponse({
                'success': True,
                'message': 'Menu item added successfully!',
                'id': new_item.id,
                'item': {
                    'id': new_item.id,
                    'item_name': new_item.item_name,
                    'description': new_item.description,
                    'price': float(new_item.price),
                    'category': new_item.category,
                    'veg_nonveg': new_item.veg_nonveg,
                    'meal_type': new_item.meal_type,
                    'availability_time': new_item.availability_time,
                    'image_url': new_item.image_url
                }
            }, status=201)
            
        except Exception as e:
            logger.error(f"[v0] Error adding menu item: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Server error occurred while adding menu item.',
                'details': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
    
@csrf_exempt
@require_http_methods(['GET', 'POST'])
def api_place_order(request):
    """
    Handles POST requests to place a new order from the customer app/web.
    Orders start in 'Pending' status and require admin acceptance.
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['customer_name', 'customer_mobile', 'items', 'total_price', 'payment_method']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Validate mobile number
        if not data['customer_mobile'].isdigit() or len(data['customer_mobile']) != 10:
            return JsonResponse({'error': 'Invalid mobile number format. Must be 10 digits.'}, status=400)
        
        # Validate items
        if not isinstance(data['items'], list) or len(data['items']) == 0:
            return JsonResponse({'error': 'Items must be a non-empty list.'}, status=400)

        # Validate and calculate total
        calculated_subtotal = Decimal('0.00')
        validated_items_for_db = []
        
        for item_data in data['items']:
            if not all(k in item_data for k in ['id', 'quantity']):
                return JsonResponse({'error': 'Each item must have id and quantity.'}, status=400)
            
            try:
                menu_item = MenuItem.objects.get(id=int(item_data['id']))
                quantity = int(item_data['quantity'])
                
                if quantity <= 0:
                    continue
                
                item_total = menu_item.price * quantity
                calculated_subtotal += item_total
                
                validated_items_for_db.append({
                    'id': menu_item.id,
                    'name': menu_item.item_name,
                    'price': float(menu_item.price),
                    'quantity': quantity,
                })
            except MenuItem.DoesNotExist:
                return JsonResponse({'error': f'Menu item with ID {item_data["id"]} not found.'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid item data format.'}, status=400)

        if not validated_items_for_db:
            return JsonResponse({'error': 'No valid items found in the order.'}, status=400)

        final_total_client = Decimal(str(data['total_price']))

        # Create order with 'Pending' status - REQUIRES ADMIN ACCEPTANCE
        new_order = Order.objects.create(
            customer_name=data['customer_name'],
            customer_mobile=data['customer_mobile'],
            items=validated_items_for_db,
            subtotal=calculated_subtotal,
            discount=Decimal('0.00'),
            total_price=final_total_client,
            status='Pending',  # ← This is the key change
            order_status='pending',  # ← Also set to pending
            order_placed_by='customer'
        )
        
        logger.info(f"✅ Initial Order (PK: {new_order.pk}) created for {new_order.customer_name}.")

        # Generate and save custom order_id
        try:
            while True:
                generated_id = str(random.randint(10000000, 99999999))
                if not Order.objects.filter(order_id=generated_id).exists():
                    new_order.order_id = generated_id
                    new_order.save(update_fields=['order_id'])
                    logger.info(f"✅ Assigned custom Order ID {new_order.order_id} to PK {new_order.pk}.")
                    break
        except Exception as e_genid:
            logger.error(f"❌ Failed to generate order_id for PK {new_order.pk}: {e_genid}", exc_info=True)
            return JsonResponse({'error': 'Failed to finalize order ID.'}, status=500)
        
        generated_order_id = new_order.order_id

        # Send Firebase notification
        try:
            items_json = json.dumps(new_order.items)
            order_db_id = str(new_order.pk)
            message_data = {
                'id': order_db_id,
                'order_id': generated_order_id,
                'customer_name': new_order.customer_name,
                'customer_mobile': new_order.customer_mobile,
                'total_price': str(new_order.total_price),
                'items': items_json,
                'order_source': 'customer',
                'status': 'pending'  # ← Include status
            }
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title='🔔 New Customer Order - Action Required!',
                    body=f'Order #{generated_order_id} from {new_order.customer_name} - ₹{new_order.total_price}'
                ),
                data=message_data,
                topic='new_orders'
            )
            response = messaging.send(message)
            logger.info(f'✅ Successfully sent FCM message for customer order {generated_order_id}: {response}')

        except Exception as e_fcm:
            logger.error(f"❌ Error sending FCM message for customer order ID {generated_order_id}: {e_fcm}", exc_info=True)

        return JsonResponse({
            'success': True,
            'order_id': generated_order_id,
            'message': 'Order placed successfully! Awaiting restaurant confirmation.'
        })

    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        logger.warning(f"⚠️ Invalid order request data format: {e}")
        return JsonResponse({'error': f'Invalid data format: {e}'}, status=400)
    except MenuItem.DoesNotExist as e:
        logger.warning(f"⚠️ Invalid menu item specified in order: {e}")
        return JsonResponse({'error': 'An invalid menu item was included in the order.'}, status=400)
    except Exception as e:
        logger.error(f"❌ Unexpected error during place customer order: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected server error occurred while placing the order.'}, status=500)
        
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
    context = {
        'active_page': 'settings',
    }
    return render(request, 'OrderMaster/settings.html', context)

@admin_required
def get_orders_api(request):
    """API endpoint to fetch recent orders for the admin dashboard."""
    try:
        orders = Order.objects.all().order_by('-created_at')[:20]
        data = [{
            'id': order.id, 'order_id': order.order_id,
            'customer_name': order.customer_name, 'items': order.items,
            'total_price': float(order.total_price),
            'status': order.order_status,
            'created_at': order.created_at.strftime('%b %d, %Y, %I:%M %p')
        } for order in orders]
        return JsonResponse({'orders': data})
    except Exception as e:
        logger.error(f"API get_orders error: {e}")
        return JsonResponse({'error': 'Server error occurred.'}, status=500)

@csrf_exempt
@admin_required
@require_GET  # Make sure this view only responds to GET
def get_pending_orders(request):
    """
    Returns a list of all active orders, separated for the Flutter app.
    This version sends 'total_price' as a float (number).
    """
    try:
        active_orders = Order.objects.filter(
            order_status__in=['open', 'ready']
        ).order_by('created_at')

        online_orders_data = []
        counter_orders_data = []

        for order in active_orders:
            try:
                items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
            except json.JSONDecodeError:
                items_list = [] # Handle malformed JSON

            order_data = {
                'id': order.id,
                'order_id': order.order_id,
                'customer_name': order.customer_name,
                'customer_mobile': order.customer_mobile,
                'items': items_list,
                'total_price': float(order.total_price), # <-- FIX IS HERE: Send as float
                'order_status': order.order_status,
                'status': order.status,
                'order_placed_by': order.order_placed_by,
                'created_at': order.created_at.isoformat(),
                'ready_time': order.ready_time.isoformat() if order.ready_time else None,
                'pickup_time': order.pickup_time.isoformat() if order.pickup_time else None,
            }
            
            if order.order_placed_by == 'counter':
                counter_orders_data.append(order_data)
            else:
                online_orders_data.append(order_data)

        return JsonResponse({
            'online_orders': online_orders_data,
            'counter_orders': counter_orders_data
        })
    
    except Exception as e:
        logger.error(f"Error fetching pending orders for Flutter: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
# --- START: Merged updates for getAllOrders ---
@csrf_exempt
@require_http_methods(['GET'])
def getAllOrders(request):
    """
    Fetch all orders for Flutter app with proper JSON response.
    Added proper date filter handling to accept 'this_month', 'today', 'this week' strings
    """
    try:
        logger.info("[v0] getAllOrders API called")
        
        date_filter = request.GET.get('date_filter') or request.GET.get('date') or 'this_month'
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        logger.info(f"[v0] Date filter received: {date_filter}")
        
        now = timezone.now()
        start_datetime = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_datetime = now
        
        try:
            if date_filter == 'today':
                start_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_datetime = start_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif date_filter == 'this_week':
                start_datetime = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now
            elif date_filter == 'this_month':
                start_datetime = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_datetime = now
            elif date_filter == 'custom' and start_date_str and end_date_str:
                try:
                    start_datetime = timezone.make_aware(
                        datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
                    )
                    end_datetime = timezone.make_aware(
                        datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
                    )
                except ValueError as ve:
                    logger.error(f"[v0] Invalid custom date format: {ve}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid custom date format. Use YYYY-MM-DD'
                    }, status=400)
            elif date_filter and date_filter not in ['today', 'this_week', 'this_month', 'custom']:
                try:
                    target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    start_datetime = timezone.make_aware(
                        datetime.combine(target_date, datetime.min.time())
                    )
                    end_datetime = timezone.make_aware(
                        datetime.combine(target_date, datetime.max.time())
                    )
                    logger.info(f"[v0] Parsed date string: {target_date}")
                except ValueError:
                    logger.warning(f"[v0] Invalid date format: {date_filter}, defaulting to this_month")
                    start_datetime = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_datetime = now
        
        except Exception as date_error:
            logger.error(f"[v0] Date parsing error: {date_error}", exc_info=True)
            start_datetime = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_datetime = now
        
        # Query orders for the date range
        orders = Order.objects.filter(
            created_at__range=(start_datetime, end_datetime)
        ).order_by('-created_at')
        
        logger.info(f"[v0] Found {orders.count()} orders between {start_datetime} and {end_datetime}")
        
        # Serialize orders for Flutter app
        orders_data = []
        for order in orders:
            try:
                # Safely parse items
                if isinstance(order.items, str):
                    try:
                        items_list = json.loads(order.items)
                    except json.JSONDecodeError:
                        logger.error(f"[v0] JSON decode error for order {order.id}")
                        items_list = []
                elif isinstance(order.items, list):
                    items_list = order.items
                else:
                    logger.warning(f"[v0] Unexpected items type for order {order.id}")
                    items_list = []
                
                # Format order data for Flutter
                orders_data.append({
                    'id': order.id,
                    'order_id': order.order_id if order.order_id else str(order.id),
                    'customer_name': order.customer_name,
                    'customer_mobile': order.customer_mobile,
                    'items': items_list,
                    'total_price': float(order.total_price),  # Ensure float
                    'status': order.status,
                    'order_status': order.order_status,
                    'order_placed_by': order.order_placed_by,
                    'payment_method': order.payment_method,
                    'created_at': order.created_at.isoformat(),
                    'ready_time': order.ready_time.isoformat() if order.ready_time else None,
                    'pickup_time': order.pickup_time.isoformat() if order.pickup_time else None,
                })
            except Exception as e:
                logger.error(f"[v0] Error serializing order {order.id}: {e}", exc_info=True)
                continue
        
        logger.info(f"[v0] Successfully serialized {len(orders_data)} orders")
        
        return JsonResponse({
            'success': True,
            'orders': orders_data,
            'count': len(orders_data),
            'date_filter': date_filter
        }, safe=False)
        
    except Exception as e:
        logger.error(f"[v0] Error in getAllOrders: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Server error occurred while fetching orders.',
            'details': str(e)
        }, status=500)
# --- END: Merged updates for getAllOrders ---
        
@csrf_exempt
@admin_required
@require_POST
def handle_order_action(request):
    """
    Handles 'accept' or 'reject' actions for new orders.
    """
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')  # This is the database ID (pk)
        action = data.get('action')

        order = get_object_or_404(Order, id=order_id)

        if action == 'accept':
            order.status = 'confirmed'
            order.order_status = 'open'  # Move to preparing
            message = f'Order #{order.order_id} accepted successfully.'
        elif action == 'reject':
            order.status = 'Rejected'
            order.order_status = 'cancelled'
            message = f'Order #{order.order_id} rejected.'
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)

        order.save()
        return JsonResponse({'success': True, 'message': message})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in handle_order_action: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
@admin_required
def take_order_view(request):
    """View for staff to manually take customer orders"""
    menu_items = MenuItem.objects.all().order_by('category', 'item_name')
    
    context = {
        'menu_items': menu_items,
        'active_page': 'take_order',
    }
    return render(request, 'OrderMaster/take_order.html', context)


@csrf_exempt
@require_POST
@admin_required
def create_manual_order(request):
    """
    Handles POST requests from the admin panel to create an order manually.
    """
    try:
        raw_body = request.body.decode('utf-8')
        logger.info(f"📥 Received raw data for manual order: {raw_body}")
        data = json.loads(raw_body)
        logger.info(f"✅ Parsed data for manual order: {data}")
    except Exception as e:
        logger.error(f"❌ Error reading/parsing request body for manual order: {e}")
        return JsonResponse({'error': 'Could not parse request data.'}, status=400)

    try:
        customer_name = data.get('customer_name')
        customer_mobile = data.get('customer_mobile')
        items_data = data.get('items')
        payment_method = data.get('payment_method')

        if not all([customer_name, customer_mobile, items_data, payment_method]):
            logger.warning(f"⚠️ Manual order missing required fields. Received: Name={customer_name}, Mobile={customer_mobile}, Items={items_data is not None}, Payment={payment_method}")
            return JsonResponse({'error': 'Missing required fields: customer_name, customer_mobile, items, payment_method.'}, status=400)

        if not (customer_mobile.isdigit() and len(customer_mobile) == 10):
            logger.warning(f"⚠️ Manual order invalid mobile: {customer_mobile}")
            return JsonResponse({'error': 'Invalid 10-digit mobile number format.'}, status=400)

        if not isinstance(items_data, list):
            logger.warning(f"⚠️ Manual order items data is not a list. Received: {type(items_data)}")
            return JsonResponse({'error': '"items" must be a list.'}, status=400)

        subtotal = Decimal('0.00')
        validated_items = []
        
        for item_data in items_data:
            logger.debug(f"🔍 Processing manual order item: {item_data}")
            if not all(k in item_data for k in ['id', 'quantity']):
                logger.warning(f"⚠️ Manual order invalid item data format: {item_data}")
                return JsonResponse({'error': 'Invalid item data format. Each item needs "id" and "quantity".'}, status=400)
            try:
                menu_item = MenuItem.objects.get(id=int(item_data['id']))
                quantity = int(item_data['quantity'])
                if quantity <= 0:
                    logger.warning(f"⚠️ Skipping manual order item ID {menu_item.id} with zero/negative quantity.")
                    continue
                item_total = menu_item.price * quantity
                subtotal += item_total
                validated_items.append({
                    'id': menu_item.id,
                    'name': menu_item.item_name,
                    'price': float(menu_item.price),
                    'quantity': quantity,
                })
            except MenuItem.DoesNotExist:
                logger.warning(f"⚠️ Manual order item ID {item_data['id']} not found.")
                return JsonResponse({'error': f'Menu item with ID {item_data["id"]} not found.'}, status=400)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Manual order invalid quantity for item ID {item_data.get('id', 'unknown')}.")
                return JsonResponse({'error': f'Invalid quantity for item ID {item_data.get("id", "unknown")}.'}, status=400)

        if not validated_items:
            logger.warning("⚠️ Manual order failed: No valid items found after validation.")
            return JsonResponse({'error': 'No valid items provided.'}, status=400)

        new_order = Order.objects.create(
            customer_name=customer_name,
            customer_mobile=customer_mobile,
            items=validated_items,
            subtotal=subtotal,
            discount=Decimal('0.00'),
            total_price=subtotal,
            status='confirmed',
            payment_method=payment_method,
            payment_id=payment_method,
            order_status='open',
            order_placed_by='counter'
        )

        try:
            while True:
                generated_id = str(random.randint(10000000, 99999999))
                if not Order.objects.filter(order_id=generated_id).exists():
                    new_order.order_id = generated_id
                    new_order.save(update_fields=['order_id'])
                    logger.info(f"✅ Assigned custom Order ID {new_order.order_id} to PK {new_order.pk}.")
                    break
        except Exception as e_genid:
            logger.error(f"❌ Failed to generate and save custom order_id for PK {new_ower.pk}: {e_genid}", exc_info=True)
            return JsonResponse({'error': 'Failed to finalize order ID.'}, status=500)

        generated_order_id = new_order.order_id

        # --- MODIFICATION: Changed FCM message for counter orders ---
        try:
            items_json = json.dumps(new_order.items)
            order_db_id = str(new_order.pk)
            message_data = {
                'id': order_db_id,
                'order_id': generated_order_id,
                'customer_name': customer_name,
                'total_price': str(subtotal),
                'items': items_json,
                'order_source': 'counter' # This tells the client *NOT* to show the popup
            }
            message = messaging.Message(
                notification=messaging.Notification(
                    title='✅ Counter Order Placed', # Changed title
                    body=f'Order #{generated_order_id} for {customer_name} created.' # Changed body
                ),
                data=message_data,
                topic='new_orders'
            )
            messaging.send(message)
            logger.info(f'✅ Successfully sent FCM message for manual order {generated_order_id}')
        except Exception as e_fcm:
            logger.error(f"❌ Error sending counter order notification for {generated_order_id}: {e_fcm}", exc_info=True)

        return JsonResponse({
            'success': True,
            'order_id': generated_order_id,
            'order_pk': new_order.pk,
            'total': float(subtotal),
            'message': 'Order created successfully!'
        })

    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        logger.warning(f"⚠️ Invalid manual order request data format: {e}")
        return JsonResponse({'error': f'Invalid data format: {e}'}, status=400)
    except MenuItem.DoesNotExist as e:
        logger.warning(f"⚠️ Invalid menu item specified in manual order: {e}")
        return JsonResponse({'error': 'An invalid menu item was included in the order.'}, status=400)
    except Exception as e:
        logger.error(f"❌ Error creating manual order: {e}", exc_info=True)
        return JsonResponse({'error': 'An internal server error occurred.'}, status=500)
        
@admin_required
def generate_invoice_view(request, order_id):
    """Generate printable invoice for an order"""
    order = get_object_or_404(Order, id=order_id)
    
    if isinstance(order.items, str):
        order.items_list = json.loads(order.items)
    else:
        order.items_list = order.items
    
    context = {
        'order': order,
        'print_date': timezone.now(),
    }
    
    return render(request, 'OrderMaster/invoice.html', context)

@csrf_exempt
@require_http_methods(['GET'])
def api_online_orders(request):
    """API endpoint specifically for fetching online orders (placed by customers)"""
    try:
        # Get date filtering parameters
        date_filter = request.GET.get('date_filter', 'today')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Apply date filtering logic (same as ordermanagementview)
        now = timezone.now()
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif date_filter == 'yesterday': # Added for completeness based on order_management_view
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
        else: # Default to today if no filter or invalid custom range
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            date_filter = 'today'
        
        # CRITICAL: Filter only customer orders
        online_orders = Order.objects.filter(
            created_at__range=(start_date, end_date),
            order_placed_by='customer'  # This is the key filter!
        ).order_by('-created_at')
        
        # Serialize orders data
        orders_data = []
        for order in online_orders:
            try:
                items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
            except json.JSONDecodeError:
                logger.warning(f"Could not decode items for online order {order.id}")
                items_list = [] # Handle malformed JSON

            orders_data.append({
                'id': order.id,
                'orderid': order.order_id,
                'customername': order.customer_name,
                'customermobile': order.customer_mobile,
                'items': items_list,
                'totalprice': float(order.total_price),
                'orderstatus': order.order_status,
                'status': order.status,
                'createdat': order.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'orders': orders_data,
            'count': len(orders_data)
        })
        
    except Exception as e:
        logger.error(f'Error in api_online_orders: {e}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Server error occurred while fetching online orders.'
        }, status=500)


@admin_required
def edit_menu_item_view(request, item_id):
    """Handles editing an existing menu item via web form."""
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
def invoice_view(request, order_id):
    """Renders a printable invoice for an order."""
    try:
        order = get_object_or_404(Order, id=order_id)
        context = {'order': order}
        return render(request, 'OrderMaster/invoice.html', context)
    except Http404:
        messages.error(request, "Order not found.")
        return redirect('dashboard')


@admin_required
@require_GET
def analytics_data_api(request):
    """API view for analytics data."""
    try:
        # Get filters from the request
        date_filter = request.GET.get('date_filter', 'this_month')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        now = timezone.now()
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
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
        else:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        # Filter for completed orders within the date range
        completed_orders = Order.objects.filter(order_status='pickedup', created_at__range=(start_date, end_date))

        total_revenue = completed_orders.aggregate(total=Sum('total_price'))['total'] or 0
        total_orders = Order.objects.count() # Total orders placed, not just completed
        completed_orders_count = completed_orders.count()

        # Extract all items from completed orders
        all_items = []
        for order in completed_orders:
            try:
                items_list = json.loads(order.items) if isinstance(order.items, str) else order.items
                if isinstance(items_list, list):
                    for item in items_list:
                        all_items.append(item.get('name', 'Unknown'))
            except json.JSONDecodeError:
                logger.warning(f"Could not decode items for order {order.id}")
                continue
                
        item_counts = Counter(all_items).most_common(5)

        data = {
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'completed_orders_count': completed_orders_count,
            'popular_items': item_counts,
            'date_range': {'start': start_date_str, 'end': end_date_str}
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Analytics data API error: {e}")
        # FIX IS HERE: It should be status=500
        return JsonResponse({'error': 'Failed to fetch analytics data'}, status=500)
