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

// Update cart display
function updateCartDisplay() {
    const cartCount = document.getElementById('cartCount');
    const cartItems = document.getElementById('cartItems');
    const cartSummary = document.getElementById('cartSummary');
    const proceedBtn = document.getElementById('proceedToCheckout');

    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

    // Update cart count badge
    if (totalItems > 0) {
        cartCount.textContent = totalItems;
        cartCount.classList.remove('d-none');
    } else {
        cartCount.classList.add('d-none');
    }

    // Update cart items
    if (cart.length === 0) {
        cartItems.innerHTML = '<p class="text-muted text-center py-4" id="emptyCartMessage">Your cart is empty</p>';
        cartSummary.innerHTML = '';
        proceedBtn.classList.add('d-none');
        return;
    }

    proceedBtn.classList.remove('d-none');

    let cartHTML = '';
    cart.forEach(item => {
        const itemTotal = parseFloat(item.price) * item.quantity;
        cartHTML += `
            <div class="cart-item py-2 border-bottom">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-0">${item.name}</h6>
                        <small class="text-muted">₹${parseFloat(item.price).toFixed(2)} x ${item.quantity}</small>
                    </div>
                    <div class="fw-bold">₹${itemTotal.toFixed(2)}</div>
                </div>
                <div class="d-flex align-items-center mt-2">
                     <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, -1)">-</button>
                     <span class="mx-2">${item.quantity}</span>
                     <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, 1)">+</button>
                    <button class="btn btn-sm btn-outline-danger ms-auto" onclick="removeFromCart(${item.id})">Remove</button>
                </div>
            </div>
        `;
    });

    cartItems.innerHTML = cartHTML;

    // Update summary
    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
    const deliveryFee = subtotal >= 300 ? 0 : 40;
    const total = subtotal + deliveryFee;

    cartSummary.innerHTML = `
        <div class="d-flex justify-content-between">
            <span>Subtotal</span>
            <span>₹${subtotal.toFixed(2)}</span>
        </div>
        <div class="d-flex justify-content-between">
            <span>Delivery Fee</span>
            <span>${deliveryFee === 0 ? 'FREE' : '₹' + deliveryFee.toFixed(2)}</span>
        </div>
        <div class="d-flex justify-content-between fw-bold mt-2">
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
    
    const customerName = document.getElementById('customerName').value.trim();
    const customerMobile = document.getElementById('customerMobile').value.trim();
    const customerAddress = document.getElementById('customerAddress').value.trim();

    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
    const deliveryFee = subtotal >= 300 ? 0 : 40;
    const totalAmount = subtotal + deliveryFee;

    const orderData = {
        customer_name: customerName,
        customer_mobile: customerMobile,
        customer_address: customerAddress,
        items: JSON.stringify(cart),
        total_amount: totalAmount
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
            showToast('Order placed successfully!', 'success');
            clearCart();
            resetCheckoutForm();
            toggleCart();
        } else {
            throw new Error(result.error || 'Failed to place order');
        }
    } catch (error) {
        showToast(error.message || 'Failed to place order. Please try again.', 'error');
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
        cart = JSON.parse(savedCart);
        updateCartDisplay();
    }
}

// Show toast notification using Bootstrap Toast
function showToast(message, type = 'success') {
    const toastEl = document.getElementById('toast');
    const toastBody = document.getElementById('toastMessage');
    const toastTitle = document.getElementById('toastTitle');

    toastTitle.textContent = type.charAt(0).toUpperCase() + type.slice(1);
    toastBody.textContent = message;

    const toast = new bootstrap.Toast(toastEl);
    toast.show();
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
