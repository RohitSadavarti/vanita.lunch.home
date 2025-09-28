// Customer Interface JavaScript - static/js/customer.js

// Global variables
let menuItems = [];
let cart = [];
let filteredItems = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
    loadMenuItems();
    setupEventListeners();
    loadCartFromStorage();
});

// Setup event listeners
function setupEventListeners() {
    // Cart functionality
    document.getElementById('cartBtn').addEventListener('click', toggleCart);
    document.getElementById('closeCartBtn').addEventListener('click', toggleCart);
    document.getElementById('cartOverlay').addEventListener('click', toggleCart);

    // Checkout
    document.getElementById('proceedToCheckout').addEventListener('click', showCheckoutForm);
    document.getElementById('customerForm').addEventListener('submit', handleOrderSubmit);
}

// Load menu items from Django backend
async function loadMenuItems() {
    const loadingIndicator = document.getElementById('loadingIndicator');

    try {
        const response = await fetch('/api/menu-items/');

        if (!response.ok) {
            throw new Error('Failed to load menu items');
        }

        menuItems = await response.json();
        filteredItems = [...menuItems];

        loadingIndicator.style.display = 'none';
        renderMenuItems();

    } catch (error) {
        console.error('Error loading menu items:', error);
        loadingIndicator.innerHTML = `
            <div class="col-12 text-center py-5">
                <h4>Unable to load menu</h4>
                <p class="text-muted">Please check your connection and try again</p>
                <button class="btn btn-primary" onclick="loadMenuItems()">Retry</button>
            </div>
        `;
    }
}

// Render menu items
function renderMenuItems() {
    const container = document.getElementById('menuContainer');

    if (filteredItems.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <h4>No items found</h4>
            </div>
        `;
        return;
    }

    let menuHTML = '';
    filteredItems.forEach(item => {
        const imageUrl = item.image || 'https://placehold.co/600x400/f97316/ffffff?text=No+Image';
        menuHTML += `
            <div class="bg-white rounded-lg shadow-md overflow-hidden transform hover:scale-105 transition-transform duration-300">
                <img src="${imageUrl}" alt="${item.item_name}" class="h-48 w-full object-cover">
                <div class="p-4">
                    <h4 class="text-lg font-bold">${item.item_name}</h4>
                    <p class="text-sm text-gray-600 mt-1">${item.description}</p>
                    <div class="flex justify-between items-center mt-4">
                        <span class="text-lg font-bold text-orange-600">₹${parseFloat(item.price).toFixed(2)}</span>
                        <button class="add-to-cart-btn bg-orange-100 text-orange-700 font-semibold px-4 py-2 rounded-lg hover:bg-orange-200 transition-colors text-sm" onclick="addToCart(${item.id})">Add to Cart</button>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = menuHTML;
}

// Add item to cart
function addToCart(itemId) {
    const item = menuItems.find(i => i.id === itemId);
    if (!item) return;

    const existingItem = cart.find(i => i.id === itemId);
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: item.id,
            name: item.item_name,
            price: item.price,
            quantity: 1
        });
    }

    updateCartDisplay();
    saveCartToStorage();
    showToast(`${item.item_name} added to cart!`, 'success');
}

// Update cart quantity
function updateQuantity(itemId, change) {
    const item = cart.find(i => i.id === itemId);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            cart = cart.filter(i => i.id !== itemId);
        }
        updateCartDisplay();
        saveCartToStorage();
    }
}

// Remove item from cart
function removeFromCart(itemId) {
    const item = cart.find(i => i.id === itemId);
    const itemName = item ? item.name : 'Item';
    cart = cart.filter(i => i.id !== itemId);
    updateCartDisplay();
    saveCartToStorage();
    showToast(`${itemName} removed from cart`, 'warning');
}

// Update cart display - FIXED for CSS classes
function updateCartDisplay() {
    const cartCount = document.getElementById('cartCount');
    const cartItems = document.getElementById('cartItems');
    const cartSummary = document.getElementById('cartSummary');
    const proceedBtn = document.getElementById('proceedToCheckout');

    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

    // Update cart count badge - FIXED
    if (totalItems > 0) {
        cartCount.textContent = totalItems;
        cartCount.classList.remove('d-none', 'hidden'); // Handle both classes
        cartCount.style.display = 'flex';
    } else {
        cartCount.classList.add('d-none');
        cartCount.style.display = 'none';
    }

    // Update cart items
    if (cart.length === 0) {
        cartItems.innerHTML = '<p class="text-gray-500 text-center py-4" id="emptyCartMessage">Your cart is empty</p>';
        cartSummary.innerHTML = '';
        proceedBtn.classList.add('d-none');
        return;
    }

    proceedBtn.classList.remove('d-none');

    let cartHTML = '';
    cart.forEach(item => {
        const itemTotal = parseFloat(item.price) * item.quantity;
        cartHTML += `
            <div class="cart-item py-3">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex-1">
                        <h6 class="font-medium text-gray-900">${item.name}</h6>
                        <p class="text-sm text-gray-600">₹${parseFloat(item.price).toFixed(2)} × ${item.quantity}</p>
                    </div>
                    <div class="font-bold text-gray-900">₹${itemTotal.toFixed(2)}</div>
                </div>
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <button class="quantity-btn" onclick="updateQuantity(${item.id}, -1)">−</button>
                        <span class="w-8 text-center">${item.quantity}</span>
                        <button class="quantity-btn" onclick="updateQuantity(${item.id}, 1)">+</button>
                    </div>
                    <button class="text-sm text-red-600 hover:text-red-800" onclick="removeFromCart(${item.id})">Remove</button>
                </div>
            </div>
        `;
    });

    cartItems.innerHTML = cartHTML;

    // Update summary
    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
    // No delivery charges
    const total = subtotal;

    cartSummary.innerHTML = `
        <div class="flex justify-between">
            <span>Subtotal</span>
            <span>₹${subtotal.toFixed(2)}</span>
        </div>
        <div class="flex justify-between">
            <span>Delivery Fee</span>
            <span>FREE</span>
        </div>
        <div class="flex justify-between font-bold text-lg">
            <span>Total</span>
            <span>₹${total.toFixed(2)}</span>
        </div>
    `;
}

// Toggle cart sidebar
function toggleCart() {
    const cartSidebar = document.getElementById('cartSidebar');
    const cartOverlay = document.getElementById('cartOverlay');
    
    cartSidebar.classList.toggle('open');
    cartOverlay.classList.toggle('open');
    
    document.body.style.overflow = cartSidebar.classList.contains('open') ? 'hidden' : '';
}

// Show checkout form
function showCheckoutForm() {
    if (cart.length === 0) {
        showToast('Your cart is empty!', 'error');
        return;
    }
    
    document.getElementById('proceedToCheckout').classList.add('d-none');
    document.getElementById('checkoutForm').classList.remove('d-none');
}

// Handle order submission
async function handleOrderSubmit(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('placeOrderBtn');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Placing Order...';
    submitBtn.disabled = true;
    
    const customerName = document.getElementById('customerName').value.trim();
    const customerMobile = document.getElementById('customerMobile').value.trim();
    const customerAddress = document.getElementById('customerAddress').value.trim();

    // Validate inputs
    if (!customerName || !customerMobile || !customerAddress) {
        showToast('Please fill in all fields', 'error');
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        return;
    }

    if (!/^\d{10}$/.test(customerMobile)) {
        showToast('Please enter a valid 10-digit mobile number', 'error');
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        return;
    }

    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
    // No delivery charges
    const totalAmount = subtotal;

    const orderData = {
        customer_name: customerName,
        customer_mobile: customerMobile,
        customer_address: customerAddress,
        items: cart,  // Send as array, not stringified
        total_amount: totalAmount,
        payment_id: 'COD_' + Date.now()
    };

    try {
        const response = await fetch('/api/place-order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(orderData)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showToast('Order placed successfully! Order ID: ' + result.order_id, 'success');
            clearCart();
            resetCheckoutForm();
            toggleCart();
        } else {
            throw new Error(result.error || 'Failed to place order');
        }
    } catch (error) {
        console.error('Order placement error:', error);
        showToast(error.message || 'Failed to place order. Please try again.', 'error');
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

// Clear cart
function clearCart() {
    cart = [];
    updateCartDisplay();
    saveCartToStorage();
}

// Reset checkout form
function resetCheckoutForm() {
    document.getElementById('customerForm').reset();
    document.getElementById('proceedToCheckout').classList.remove('d-none');
    document.getElementById('checkoutForm').classList.add('d-none');
}

// Save cart to localStorage
function saveCartToStorage() {
    localStorage.setItem('vanita_cart', JSON.stringify(cart));
}

// Load cart from localStorage
function loadCartFromStorage() {
    const savedCart = localStorage.getItem('vanita_cart');
    if (savedCart) {
        try {
            cart = JSON.parse(savedCart);
            updateCartDisplay();
        } catch (error) {
            console.error('Error loading cart from storage:', error);
            cart = [];
        }
    }
}

// Show toast notification - SIMPLIFIED
function showToast(message, type = 'success') {
    // Create a simple toast if Bootstrap is not available
    const toast = document.getElementById('toast');
    if (!toast) {
        console.log(message); // Fallback
        return;
    }

    const toastBody = document.getElementById('toastMessage');
    const toastTitle = document.getElementById('toastTitle');

    if (toastTitle) toastTitle.textContent = type.charAt(0).toUpperCase() + type.slice(1);
    if (toastBody) toastBody.textContent = message;

    // Simple show/hide without Bootstrap dependency
    toast.style.display = 'block';
    toast.classList.remove('d-none', 'hidden');
    
    setTimeout(() => {
        toast.style.display = 'none';
        toast.classList.add('d-none');
    }, 3000);
}

// Get CSRF token for Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
