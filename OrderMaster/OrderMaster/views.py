# OrderMaster/OrderMaster/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, MenuItemForm
from .models import Order, OrderItem, MenuItem, Category
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json
from firebase_admin import messaging
import logging

logger = logging.getLogger(__name__)

# --- THIS IS THE CORRECTED PART ---
# We have removed the problematic import:
# from .scripts.analytics_views import get_analytics_data  <-- THIS LINE WAS REMOVED
# ------------------------------------


@csrf_exempt
def acknowledge_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            order = Order.objects.get(id=order_id)
            order.is_acknowledged = True
            order.save()
            return JsonResponse({'success': True, 'message': 'Order acknowledged.'})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

@login_required
def dashboard(request):
    unacknowledged_order = Order.objects.filter(is_acknowledged=False, order_status='pending').order_by('created_at').first()
    
    unacknowledged_order_data = None
    if unacknowledged_order:
        items = list(unacknowledged_order.items.values('menu_item__name', 'quantity'))
        unacknowledged_order_data = {
            'id': unacknowledged_order.id,
            'order_id': unacknowledged_order.order_id,
            'customer_name': unacknowledged_order.customer_name,
            'total_price': float(unacknowledged_order.total_price),
            'items': json.dumps(items)
        }

    today = timezone.now().date()
    live_orders = Order.objects.filter(created_at__date=today, order_status__in=['pending', 'preparing']).order_by('-created_at')
    
    context = {
        'live_orders': live_orders,
        'unacknowledged_order': json.dumps(unacknowledged_order_data)
    }
    return render(request, 'OrderMaster/dashboard.html', context)


# In OrderMaster/OrderMaster/views.py

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'OrderMaster/login.html', {'form': form})

# (Keep all other functions in views.py exactly as they are)
def logout_view(request):
    logout(request)
    return redirect('login')
    
@login_required
def order_management_view(request):
    unacknowledged_order = Order.objects.filter(is_acknowledged=False, order_status='pending').order_by('created_at').first()
    unacknowledged_order_data = None
    if unacknowledged_order:
        items = list(unacknowledged_order.items.values('menu_item__name', 'quantity'))
        unacknowledged_order_data = {
            'id': unacknowledged_order.id,
            'order_id': unacknowledged_order.order_id,
            'customer_name': unacknowledged_order.customer_name,
            'total_price': float(unacknowledged_order.total_price),
            'items': json.dumps(items)
        }

    date_filter = request.GET.get('date_filter', 'today')
    today = timezone.now().date()
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if date_filter == 'today':
        orders = Order.objects.filter(created_at__date=today)
        date_display_str = "Today"
    elif date_filter == 'yesterday':
        orders = Order.objects.filter(created_at__date=today - timedelta(days=1))
        date_display_str = "Yesterday"
    elif date_filter == 'this_week':
        start_of_week = today - timedelta(days=today.weekday())
        orders = Order.objects.filter(created_at__date__gte=start_of_week)
        date_display_str = "This Week"
    elif date_filter == 'this_month':
        orders = Order.objects.filter(created_at__year=today.year, created_at__month=today.month)
        date_display_str = "This Month"
    elif date_filter == 'custom' and start_date_str and end_date_str:
        orders = Order.objects.filter(created_at__date__range=[start_date_str, end_date_str])
        date_display_str = f"{start_date_str} to {end_date_str}"
    else:
        orders = Order.objects.filter(created_at__date=today)
        date_display_str = "Today"

    pending_orders = orders.filter(order_status='pending').order_by('created_at')
    preparing_orders = orders.filter(order_status='preparing').order_by('created_at')
    ready_orders = orders.filter(order_status='ready').order_by('created_at')
    
    context = {
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'date_display_str': date_display_str,
        'start_date_val': start_date_str,
        'end_date_val': end_date_str,
        'unacknowledged_order': json.dumps(unacknowledged_order_data)
    }
    return render(request, 'OrderMaster/order_management.html', context)


@login_required
def menu_management_view(request):
    categories = Category.objects.all().prefetch_related('menu_items')
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('menu_management')
    else:
        form = MenuItemForm()
        
    context = {
        'categories': categories,
        'form': form
    }
    return render(request, 'OrderMaster/menu_management.html', context)

@login_required
def edit_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('menu_management')
    else:
        form = MenuItemForm(instance=item)
    return render(request, 'OrderMaster/edit_menu_item.html', {'form': form})

@login_required
def delete_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        item.delete()
        return redirect('menu_management')
    return redirect('menu_management')
    
# --- THIS IS THE CORRECTED PART ---
# The original analytics_view was causing the crash.
# The analytics page is now handled by the code in analytics_views.py,
# so this view is no longer needed here. It has been removed.
# ------------------------------------

# --- API VIEWS ---
def send_new_order_notification(order):
    try:
        items_list = list(order.items.values('menu_item__name', 'quantity'))
        
        message = messaging.Message(
            notification=messaging.Notification(
                title='New Order Received!',
                body=f'Order #{order.order_id} from {order.customer_name} for ₹{order.total_price}'
            ),
            data={
                'id': str(order.id),
                'order_id': order.order_id,
                'customer_name': order.customer_name,
                'total_price': str(order.total_price),
                'items': json.dumps(items_list)
            },
            topic='new_orders'
        )
        response = messaging.send(message)
        logger.info('Successfully sent message: %s', response)
    except Exception as e:
        logger.error('Error sending FCM message: %s', e)

@csrf_exempt
def create_order_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if not all(k in data for k in ['customer_name', 'customer_phone', 'total_price', 'items']):
                return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)

            new_order = Order.objects.create(
                customer_name=data['customer_name'],
                customer_phone=data['customer_phone'],
                total_price=data['total_price'],
                order_status='pending',
                is_acknowledged=False
            )

            for item_data in data['items']:
                menu_item = MenuItem.objects.get(id=item_data['id'])
                OrderItem.objects.create(
                    order=new_order,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    price=menu_item.price
                )
            
            send_new_order_notification(new_order)
            return JsonResponse({'success': True, 'order_id': new_order.order_id})
        
        except MenuItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid menu item ID.'}, status=400)
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return JsonResponse({'success': False, 'error': 'An internal error occurred.'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


@csrf_exempt
def handle_order_action(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('order_id')
        action = data.get('action')
        
        try:
            order = Order.objects.get(id=order_id)
            if action == 'accept':
                order.order_status = 'preparing'
            elif action == 'reject':
                order.order_status = 'cancelled'
            
            order.is_acknowledged = True
            order.save()
            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def get_orders_api(request):
    today = timezone.now().date()
    live_orders = Order.objects.filter(created_at__date=today, order_status__in=['pending', 'preparing']).order_by('-created_at')
    
    orders_data = []
    for order in live_orders:
        items = list(order.items.values('menu_item__name', 'quantity'))
        orders_data.append({
            'id': order.id,
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'total_price': order.total_price,
            'order_status': order.order_status,
            'items': items,
            'created_at': order.created_at.strftime('%I:%M %p')
        })
        
    return JsonResponse({'orders': orders_data})

@csrf_exempt
@login_required
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('id')
            new_status = data.get('status')
            
            order = Order.objects.get(id=order_id)
            order.order_status = new_status
            order.save()
            
            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Invalid Method'}, status=405)

