from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Order, OrderItem, MenuItems
import json
from django.contrib import messages
from datetime import timedelta
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

# Custom decorator to check for admin user
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('login') # Or some 'access-denied' page
        return view_func(request, *args, **kwargs)
    return wrapper

# Authentication views
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'OrderMaster/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


# Dashboard and Management Views
@admin_required
def dashboard_view(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # Key Metrics
    total_revenue = Order.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_orders = Order.objects.count()
    
    # Metrics for today
    revenue_today = Order.objects.filter(created_at__date=today).aggregate(Sum('amount'))['amount__sum'] or 0
    orders_today = Order.objects.filter(created_at__date=today).count()
    
    # Recent Orders
    recent_orders = Order.objects.order_by('-created_at')[:10]

    # Top Selling Items (Example: based on quantity sold)
    top_items = OrderItem.objects.values('item_name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:5]

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'revenue_today': revenue_today,
        'orders_today': orders_today,
        'recent_orders': recent_orders,
        'top_items': top_items
    }
    return render(request, 'OrderMaster/dashboard.html', context)

@admin_required
def order_management_view(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'OrderMaster/order_management.html', {'orders': orders})

@admin_required
def menu_management_view(request):
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category = request.POST.get('category')
        veg_nonveg = request.POST.get('veg_nonveg')
        image = request.FILES.get('image')

        # Basic validation
        if not all([item_name, price, category, veg_nonveg]):
            messages.error(request, "Please fill all required fields.")
        else:
            try:
                menu_item = MenuItems(
                    item_name=item_name,
                    description=description,
                    price=price,
                    category=category,
                    veg_nonveg=veg_nonveg
                )
                if image:
                    menu_item.image = image
                
                menu_item.save()
                messages.success(request, f"'{item_name}' has been added successfully.")
                return redirect('menu_management')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")

    # Corrected line is here
    menu_items = MenuItems.objects.all().order_by('item_name') 
    return render(request, 'OrderMaster/menu_management.html', {'menu_items': menu_items})


@admin_required
def edit_menu_item_view(request, item_id):
    item = get_object_or_404(MenuItems, id=item_id)
    if request.method == 'POST':
        item.item_name = request.POST.get('item_name')
        item.description = request.POST.get('description')
        item.price = request.POST.get('price')
        item.category = request.POST.get('category')
        item.veg_nonveg = request.POST.get('veg_nonveg')

        if request.FILES.get('image'):
            # Delete old image if it exists
            if item.image:
                if os.path.exists(item.image.path):
                    os.remove(item.image.path)
            item.image = request.FILES.get('image')

        item.save()
        messages.success(request, "Item updated successfully.")
        return redirect('menu_management')
        
    return render(request, 'OrderMaster/edit_menu_item.html', {'item': item})


@admin_required
def delete_menu_item_view(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(MenuItems, id=item_id)
        # Optional: Delete the image file from storage
        if item.image:
            if os.path.exists(item.image.path):
                os.remove(item.image.path)
        item.delete()
        messages.success(request, "Item deleted successfully.")
    return redirect('menu_management')

@admin_required
def analytics_view(request):
    return render(request, 'OrderMaster/analytics.html')

@admin_required
def settings_view(request):
    return render(request, 'OrderMaster/settings.html')


# API Endpoints (for customer-facing app)
@csrf_exempt
def get_menu_api(request):
    items = MenuItems.objects.all().values('id', 'item_name', 'description', 'price', 'category', 'veg_nonveg', 'image')
    
    # Manually handle image URL
    menu_list = []
    for item in items:
        if item['image']:
            item['image'] = request.build_absolute_uri(settings.MEDIA_URL + item['image'])
        else:
            item['image'] = '' # or provide a default image URL
        menu_list.append(item)

    return JsonResponse(menu_list, safe=False)


@csrf_exempt
def place_order_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['name', 'mobile', 'address', 'cart_items', 'amount', 'payment_id']
            if not all(field in data for field in required_fields):
                return JsonResponse({'success': False, 'error': 'Missing required order data.'}, status=400)

            # Create the order
            order = Order.objects.create(
                name=data['name'],
                mobile=data['mobile'],
                address=data['address'],
                amount=data['amount'],
                payment_id=data['payment_id']
            )

            # Create order items
            for item_data in data['cart_items']:
                OrderItem.objects.create(
                    order=order,
                    item_name=item_data['name'],
                    quantity=item_data['quantity'],
                    price=item_data['price']
                )

            return JsonResponse({'success': True, 'order_id': order.id})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            # Log the exception e for debugging
            return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

# Customer facing page (optional, if you want to serve it from Django)
def customer_order_view(request):
    return render(request, 'OrderMaster/customer_order.html')
