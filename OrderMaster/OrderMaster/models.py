# OrderMaster/views.py

# ... (keep other imports and functions) ...
from decimal import Decimal
import logging
import json
import random
# ... (Firebase imports etc.) ...

logger = logging.getLogger(__name__)

def analytics_api_view(request):
    # ... (keep the correct implementation for analytics API) ...
    # Placeholder for the structure
    try:
        # ... calculation logic ...
        data = {
            'key_metrics': {},
            'most_ordered_items': {},
            'payment_method_distribution': {},
            'order_status_distribution': {},
            'orders_by_hour': {},
            'day_wise_revenue': {},
            'day_wise_menu': {},
            'table_data': [],
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Analytics API error: {e}")
        return JsonResponse({'error': 'Failed to fetch analytics data'}, status=500)


def order_management_view(request):
    # ... (keep existing filtering logic) ...
    date_filter = request.GET.get('date_filter', 'today')
    source_filter = request.GET.get('source_filter', 'all')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    now = timezone.now()
    # ... (date range calculation logic remains the same) ...
    if date_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    # ... (handle other date filters: yesterday, this_week, this_month, custom) ...
    else: # Default to today
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        date_filter = 'today'


    base_orders = Order.objects.filter(created_at__range=(start_date, end_date))

    # Apply source filter (This part should now work correctly after model update)
    if source_filter == 'customer':
        base_orders = base_orders.filter(order_placed_by='customer')
    elif source_filter == 'counter':
        base_orders = base_orders.filter(order_placed_by='counter')
    # else 'all' - no additional filtering needed

    preparing_orders = base_orders.filter(order_status='open').order_by('-created_at') # Order by most recent
    ready_orders = base_orders.filter(order_status='ready').order_by('-created_at')
    pickedup_orders = base_orders.filter(order_status='pickedup').order_by('-created_at')

    # Safely parse items
    def parse_items(order):
        try:
            if isinstance(order.items, str):
                order.items_list = json.loads(order.items)
            elif isinstance(order.items, list):
                 order.items_list = order.items
            else:
                 order.items_list = []
        except (json.JSONDecodeError, TypeError):
            order.items_list = [] # Default to empty list on error
        return order

    preparing_orders = [parse_items(o) for o in preparing_orders]
    ready_orders = [parse_items(o) for o in ready_orders]
    pickedup_orders = [parse_items(o) for o in pickedup_orders]


    context = {
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'pickedup_orders': pickedup_orders,
        'date_display_str': date_filter.replace('_', ' ').title(),
        'selected_filter': date_filter,
        'source_filter': source_filter,
        'start_date_val': start_date_str if date_filter == 'custom' else start_date.strftime('%Y-%m-%d'),
        'end_date_val': end_date_str if date_filter == 'custom' else end_date.strftime('%Y-%m-%d'),
        'active_page': 'order_management',
    }
    return render(request, 'OrderMaster/order_management.html', context)


def update_order_status(request):
    # ... (keep existing implementation) ...
    try:
        data = json.loads(request.body)
        order_pk = data.get('id')
        new_status = data.get('status') # Should be 'ready' or 'pickedup'

        if not all([order_pk, new_status]):
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

        order = get_object_or_404(Order, pk=order_pk)

        # Validate status transition if needed (e.g., can only go from 'open' to 'ready')
        if new_status == 'ready' and order.order_status == 'open':
             order.order_status = 'ready'
             order.ready_time = timezone.now()
        elif new_status == 'pickedup' and order.order_status == 'ready':
             order.order_status = 'pickedup'
             order.pickup_time = timezone.now()
        else:
             # If status is invalid or transition not allowed
             return JsonResponse({'success': False, 'error': f'Invalid status transition from {order.order_status} to {new_status}'}, status=400)

        order.save()
        return JsonResponse({'success': True})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        logger.error(f"Update status error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def menu_management_view(request):
    # ... (keep existing implementation) ...
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

def api_place_order(request):
    # ... (keep existing validation logic) ...
    try:
        data = json.loads(request.body)
        # ... (validation for name, mobile, items, total_price) ...

        # --- MODIFIED: Set order_placed_by ---
        new_order = Order.objects.create(
            customer_name=data['customer_name'],
            customer_mobile=data['customer_mobile'],
            items=validated_items_for_db, # Use the validated list
            subtotal=calculated_subtotal,
            discount=Decimal('0.00'),
            total_price=final_total_server, # Use the total from request or recalculate strictly
            status='Pending', # Customer orders start as Pending
            payment_method=data.get('payment_method', 'COD'), # Assuming COD or similar field
            payment_id=data.get('payment_id', None),
            order_status='open', # Internal status
            order_placed_by='customer' # Set source to 'customer'
        )
        # --- END MODIFICATION ---

        generated_order_id = new_order.order_id # Use the auto-generated ID

        # ... (keep Firebase notification logic) ...
        try:
            items_json = json.dumps(new_order.items) # Ensure items are JSON serializable
            message = messaging.Message(
                 notification=messaging.Notification(
                     title='🔔 New Customer Order!',
                     body=f'Order #{generated_order_id} from {new_order.customer_name} - ₹{new_order.total_price}'
                 ),
                 data={
                     'id': str(new_order.id),
                     'order_id': generated_order_id,
                     'customer_name': new_order.customer_name,
                     'total_price': str(new_order.total_price),
                     'items': items_json,
                     'order_source': 'customer'
                 },
                 topic='new_orders'
             )
            response = messaging.send(message)
            logger.info(f'Successfully sent FCM message for customer order: {response}')
        except Exception as e:
            logger.error(f"Error sending FCM message for customer order: {e}")


        return JsonResponse({
            'success': True,
            'order_id': generated_order_id,
            'message': 'Order placed successfully!'
        })
    # ... (keep error handling) ...
    except Exception as e:
        logger.error(f"Place customer order error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)


def analytics_view(request):
    # ... (keep existing implementation) ...
    context = {
        'active_page': 'analytics',
    }
    return render(request, 'OrderMaster/analytics.html', context)


@admin_required
def settings_view(request):
    # ... (keep existing implementation) ...
     context = {
        'active_page': 'settings',
    }
     return render(request, 'OrderMaster/settings.html', context)


@admin_required
def get_orders_api(request):
    # ... (keep existing implementation) ...
     try:
        # Fetch orders, perhaps limit by status or date if needed
        orders = Order.objects.all().order_by('-created_at')[:20] # Example limit
        data = [{
            'id': order.id,
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'items': order.items if isinstance(order.items, list) else json.loads(order.items), # Ensure items are list
            'total_price': float(order.total_price),
            'order_status': order.order_status, # Use the internal status 'open', 'ready', 'pickedup'
            'created_at': order.created_at.strftime('%b %d, %Y, %I:%M %p')
        } for order in orders]
        return JsonResponse({'orders': data})
     except Exception as e:
        logger.error(f"API get_orders error: {e}")
        return JsonResponse({'error': 'Server error occurred.'}, status=500)


@admin_required
def get_pending_orders(request):
    # ... (keep existing implementation) ...
     try:
        pending_orders = Order.objects.filter(status='Pending').order_by('created_at')
        orders_data = []
        for order in pending_orders:
            try:
                items_list = order.items if isinstance(order.items, list) else json.loads(order.items)
            except (json.JSONDecodeError, TypeError):
                items_list = [] # Handle potential bad data
            orders_data.append({
                'id': order.id,
                'order_id': order.order_id,
                'customer_name': order.customer_name,
                'customer_mobile': order.customer_mobile,
                'items': items_list,
                'total_price': float(order.total_price),
                'created_at': order.created_at.strftime('%b %d, %Y, %I:%M %p')
            })
        return JsonResponse({'success': True, 'orders': orders_data})
     except Exception as e:
        logger.error(f"Error fetching pending orders: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@admin_required
def take_order_view(request):
    # ... (keep existing implementation) ...
    menu_items = MenuItem.objects.all().order_by('category', 'item_name')
    context = {
        'menu_items': menu_items,
        'active_page': 'take_order',
    }
    return render(request, 'OrderMaster/take_order.html', context)


@csrf_exempt
@require_POST
@admin_required # Ensure only admins can use this
def create_manual_order(request):
    # ... (keep existing validation logic) ...
    try:
        data = json.loads(request.body)
        # ... (validation for name, mobile, items, payment_method) ...

        # --- MODIFIED: Set order_placed_by ---
        new_order = Order.objects.create(
            # order_id field is handled by the model's save method
            customer_name=customer_name,
            customer_mobile=customer_mobile,
            items=validated_items,
            subtotal=subtotal,
            discount=Decimal('0.00'),
            total_price=subtotal, # Assuming no discount for manual orders yet
            status='Confirmed', # Manual orders are typically confirmed immediately
            payment_method=payment_method,
            payment_id=payment_method, # Simple ID for manual orders
            order_status='open', # Start as 'preparing'
            order_placed_by='counter' # Set source to 'counter'
        )
        # --- END MODIFICATION ---

        # ... (keep Firebase notification logic) ...
        try:
             items_json = json.dumps(new_order.items)
             message = messaging.Message(
                 notification=messaging.Notification(
                     title='✅ Counter Order Created',
                     body=f'Order #{new_order.order_id} - {customer_name} - ₹{subtotal}'
                 ),
                 data={
                     'id': str(new_order.id),
                     'order_id': new_order.order_id,
                     'customer_name': customer_name,
                     'total_price': str(subtotal),
                     'items': items_json,
                     'order_source': 'counter'
                 },
                 topic='new_orders'
             )
             messaging.send(message)
        except Exception as e:
            logger.error(f"Error sending counter order notification: {e}")


        return JsonResponse({
            'success': True,
            'order_id': new_order.order_id, # Return the generated ID
            'order_pk': new_order.id, # Also return DB primary key
            'total': float(subtotal),
            'message': 'Order created successfully!'
        })
    # ... (keep error handling) ...
    except Exception as e:
        logger.error(f"Error creating manual order: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        return JsonResponse({'error': 'An internal server error occurred.'}, status=500)


@admin_required
def generate_invoice_view(request, order_id):
    # ... (keep existing implementation) ...
     order = get_object_or_404(Order, id=order_id)
     try:
        if isinstance(order.items, str):
            order.items_list = json.loads(order.items)
        elif isinstance(order.items, list):
            order.items_list = order.items
        else:
            order.items_list = []
     except (json.JSONDecodeError, TypeError):
         order.items_list = []

     context = {
        'order': order,
        'print_date': timezone.now(),
     }
     return render(request, 'OrderMaster/invoice.html', context)









