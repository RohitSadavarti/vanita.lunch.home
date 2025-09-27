from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import MenuItem, Order
import json


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'OrderMaster/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    return render(request, 'OrderMaster/dashboard.html')


@login_required
def order_management(request):
    preparing_orders = Order.objects.filter(status='preparing')
    ready_orders = Order.objects.filter(status='ready')
    
    context = {
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
    }
    return render(request, 'OrderMaster/order_management.html', context)


@csrf_exempt
@login_required
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


@login_required
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


@login_required
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


@login_required
def delete_menu_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(MenuItem, id=item_id)
        item.delete()
        messages.success(request, 'Menu item deleted successfully!')
        return redirect('menu_management')
    return redirect('menu_management')