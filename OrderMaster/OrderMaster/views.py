# Complete OrderMaster/views.py file - replace your existing file with this

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import MenuItem, Order, VlhAdmin
import json
import uuid


def admin_required(view_func):
    """Custom decorator to check if admin is authenticated"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def login_view(request):
    if request.method == 'POST':
        mobile = request.POST['username']  # Using username field for mobile
        password = request.POST['password']
        
        try:
            # Check against your custom admin table
            admin_user = VlhAdmin.objects.get(mobile=mobile)
            if admin_user.check_password(password):
                # Store admin info in session since we're not using Django's User model
                request.session['admin_id'] = admin_user.id
                request.session['admin_mobile'] = admin_user.mobile
                request.session['is_authenticated'] = True
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid mobile number or password')
        except VlhAdmin.DoesNotExist:
            messages.error(request, 'Invalid mobile number or password')
    
    return render(request, 'OrderMaster/login.html')


def logout_view(request):
    # Clear custom session data
    request.session.flush()
    return redirect('login')


@admin_required
def dashboard(request):
    return render(request, 'OrderMaster/dashboard.html')


@admin_required
def order_management(request):
    preparing_orders = Order.objects.filter(status='preparing').order_by('-order_time')
    ready_orders = Order.objects.filter(status='ready').order_by('-ready_time', '-order_time')
    
    # Parse order items to display properly
    for order in preparing_orders:
        try:
            order.parsed_items = json.loads(order.items)
        except:
            order.parsed_items = {'items': [], 'customer_mobile': '', 'customer_address': ''}
    
    for order in ready_orders:
        try:
            order.parsed_items = json.loads(order.items)
        except:
            order.parsed_items = {'items': [], 'customer_mobile': '', 'customer_address': ''}
    
    context = {
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
    }
    return render(request, 'OrderMaster/order_management.html', context)


@csrf_exempt
@admin_required
def update_order_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        try:
            order = Order.objects.get(id=order_id)
            order.status = new_status
            if new_status == 'ready':
                order.ready_time = timezone.now()
            order.save()
            
            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@admin_required
def menu_management(request):
    if request.method == 'POST':
        item_name = request.POST['item_name']
        description = request.POST['description']
        price = request.POST['price']
        category = request.POST['category']
        veg_nonveg = request.POST['veg_nonveg']
        meal_type = request.POST['meal_type']
        availability_time = request.POST['availability_time']
        image = request.FILES.get('image')
        
        MenuItem.objects.create(
            item_name=item_name,
            description=description,
            price=price,
            category=category,
            veg_nonveg=veg_nonveg,
            meal_type=meal_type,
            availability_time=availability_time,
            image=image
        )
        messages.success(request, 'Menu item added successfully!')
        return redirect('menu_management')
    
    menu_items = MenuItem.objects.all().order_by('-created_at')
    context = {
        'menu_items': menu_items,
    }
    return render(request, 'OrderMaster/menu_management.html', context)


@admin_required
def edit_menu_item(request, item_id):
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
    
    context = {'item': item}
    return render(request, 'OrderMaster/edit_menu_item.html', context)


@admin_required
def delete_menu_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(MenuItem, id=item_id)
        item.delete()
        messages.success(request, 'Menu item deleted successfully!')
        return redirect('menu_management')
    return redirect('menu_management')


# NEW CUSTOMER VIEWS BELOW

def customer_home(request):
    """Render the customer ordering interface"""
    return render(request, 'OrderMaster/customer_order.html')


@require_http_methods(["GET"])
def api_menu_items(request):
    """API endpoint to get all available menu items"""
    try:
        menu_items = MenuItem.objects.all().order_by('category', 'item_name')
        items_data = []
        
        for item in menu_items:
            item_data = {
                'id': item.id,
                'item_name': item.item_name,
                'description': item.description,
                'price': float(item.price),
                'category': item.category,
                'veg_nonveg': item.veg_nonveg,
                'meal_type': item.meal_type,
                'availability_time': item.availability_time,
                'image': item.image.url if item.image else None,
                'created_at': item.created_at.isoformat()
            }
            items_data.append(item_data)
        
        return JsonResponse(items_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_place_order(request):
    """API endpoint to place a new order"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['customer_name', 'customer_mobile', 'customer_address', 'items', 'total_amount']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Validate mobile number
        mobile = data['customer_mobile']
        if not mobile.isdigit() or len(mobile) != 10:
            return JsonResponse({'error': 'Invalid mobile number format'}, status=400)
        
        # Parse and validate items
        try:
            items = json.loads(data['items']) if isinstance(data['items'], str) else data['items']
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid items format'}, status=400)
        
        if not items or not isinstance(items, list):
            return JsonResponse({'error': 'No items in order'}, status=400)
        
        # Validate items exist and calculate total
        calculated_total = 0
        validated_items = []
        
        for item in items:
            try:
                menu_item = MenuItem.objects.get(id=item['id'])
                item_total = float(menu_item.price) * int(item['quantity'])
                calculated_total += item_total
                
                validated_items.append({
                    'id': menu_item.id,
                    'name': menu_item.item_name,
                    'price': float(menu_item.price),
                    'quantity': int(item['quantity']),
                    'total': item_total
                })
            except MenuItem.DoesNotExist:
                return JsonResponse({'error': f'Menu item with ID {item["id"]} not found'}, status=400)
            except (ValueError, KeyError):
                return JsonResponse({'error': 'Invalid item data'}, status=400)
        
        # Add delivery fee if applicable
        delivery_fee = 0 if calculated_total >= 300 else 40
        final_total = calculated_total + delivery_fee
        
        # Verify total amount (allow small floating point differences)
        submitted_total = float(data['total_amount'])
        if abs(final_total - submitted_total) > 0.01:
            return JsonResponse({'error': 'Total amount mismatch'}, status=400)
        
        # Generate unique order ID
        order_id = f"VLH{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        
        # Create order with customer details in items JSON
        order_data = {
            'customer_mobile': mobile,
            'customer_address': data['customer_address'],
            'items': validated_items,
            'delivery_fee': delivery_fee,
            'subtotal': calculated_total
        }
        
        order = Order.objects.create(
            order_id=order_id,
            customer_name=data['customer_name'],
            items=json.dumps(order_data),
            total_amount=final_total,
            status='preparing'
        )
        
        return JsonResponse({
            'success': True,
            'order_id': order.order_id,
            'message': 'Order placed successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_order_status(request, order_id):
    """API endpoint to check order status"""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        order_data = {
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'status': order.status,
            'total_amount': float(order.total_amount),
            'order_time': order.order_time.isoformat(),
            'ready_time': order.ready_time.isoformat() if order.ready_time else None
        }
        
        return JsonResponse(order_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
