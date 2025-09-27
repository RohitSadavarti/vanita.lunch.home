// Customer Interface JavaScript - static/js/customer.js

// Global variables
let menuItems = [];
let cart = [];
let filteredItems = [];
let currentCategory = 'all';
let currentVegFilter = 'all';
let currentSearchTerm = '';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
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
    
    // Search functionality
    document.getElementById('searchInput').addEventListener('input', handleSearch);
    
    // Category filters
    document.querySelectorAll('.category-filter').forEach(button => {
        button.addEventListener('click', handleCategoryFilter);
    });
    
    // Veg/Non-veg filters
    document.querySelectorAll('.veg-filter').forEach(button => {
        button.addEventListener('click', handleVegFilter);
    });

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
                <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                <h4>Unable to load menu</h4>
                <p class="text-muted">Please check your connection and try again</p>
                <button class="btn btn-primary" onclick="loadMenuItems()">Retry</button>
            </div>
        `;
    }
}

// Handle search functionality
function handleSearch(e) {
    currentSearchTerm = e.target.value.toLowerCase();
    applyFilters();
}

// Handle category filter
function handleCategoryFilter(e) {
    document.querySelectorAll('.category-filter').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');
    currentCategory = e.target.getAttribute('data-category');
    applyFilters();
}

// Handle veg/non-veg filter
function handleVegFilter(e) {
    document.querySelectorAll('.veg-filter').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');
    currentVegFilter = e.target.getAttribute('data-type');
    applyFilters();
}

// Apply all filters
function applyFilters() {
    filteredItems = menuItems.filter(item => {
        // Category filter
        const matchesCategory = currentCategory === 'all' || item.category === currentCategory;
        
        // Veg/Non-veg filter
        const matchesVeg = currentVegFilter === 'all' || item.veg_nonveg === currentVegFilter;
        
        // Search filter
        const matchesSearch = currentSearchTerm === '' || 
            item.item_name.toLowerCase().includes(currentSearchTerm) ||
            item.description.toLowerCase().includes(currentSearchTerm);
        
        return matchesCategory && matchesVeg && matchesSearch;
    });
    
    renderMenuItems();
}

// Render menu items
function renderMenuItems() {
    const container = document.getElementById('menuContainer');
    
    if (filteredItems.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4>No items found</h4>
                <p class="text-muted">Try adjusting your search or filters</p>
            </div>
        `;
        return;
    }

    let menuHTML = '';
    filteredItems.forEach(item => {
        const vegClass = item.veg_nonveg === 'veg' ? 'veg' : 'non-veg';
        const vegLabel = item.veg_nonveg === 'veg' ? 'VEG' : 'NON-VEG';
        const imageUrl = item.image || 'https://via.placeholder.com/300x200/cccccc/ffffff?text=No+Image';
        
        menuHTML += `
            <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
                <div class="menu-card animate-pop">
                    <img src="${imageUrl}" alt="${item.item_name}" class="card-img-top">
                    <div class="card-body p-3">
                        <div class="d-flex align-items-center mb-2">
                            <span class="veg-indicator ${vegClass}"></span>
                            <small class="text-muted fw-bold">${vegLabel}</small>
                        </div>
                        <h6 class="card-title">${item.item_name}</h6>
                        <p class="card-text small text-muted">${item.description}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="price">₹${parseFloat(item.price).toFixed(2)}</span>
                            <button class="add-to-cart-btn" onclick="addToCart(${item.id})">
                                <i class="fas fa-plus me-1"></i>
                                Add
                            </button>
                        </div>
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
    const emptyMessage = document.getElementById('emptyCartMessage');
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
        cartSummary.classList.add('d-none');
        proceedBtn.classList.add('d-none');
        return;
    }

    cartSummary.classList.remove('d-none');
    proceedBtn.classList.remove('d-none');

    let cartHTML = '';
    cart.forEach(item => {
        const itemTotal = parseFloat(item.price) * item.quantity;
        cartHTML += `
            <div class="cart-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${item.name}</h6>
                        <p class="text-muted small mb-2">₹${parseFloat(item.price).toFixed(2)} each</p>
                        <div class="quantity-controls">
                            <button class="quantity-btn" onclick="updateQuantity(${item.id}, -1)">
                                <i class="fas fa-minus"></i>
                            </button>
                            <span class="mx-2 fw-bold">${item.quantity}</span>
                            <button class="quantity-btn" onclick="updateQuantity(${item.id}, 1)">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                    <div class="text-end">
                        <button class="btn btn-sm btn-outline-danger" onclick="removeFromCart(${item.id})" title="Remove item">
                            <i class="fas fa-trash"></i>
                        </button>
                        <div class="fw-bold mt-2 text-primary">₹${itemTotal.toFixed(2)}</div>
                    </div>
                </div>
            </div>
        `;
    });

    cartItems.innerHTML = cartHTML;

    // Update summary
    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
    const deliveryFee = subtotal >= 300 ? 0 : 40;
    const total = subtotal + deliveryFee;

    document.getElementById('subtotal').textContent = `₹${subtotal.toFixed(2)}`;
    document.getElementById('delivery').textContent = deliveryFee === 0 ? 'FREE' : `₹${deliveryFee.toFixed(2)}`;
    document.getElementById('total').textContent = `₹${total.toFixed(2)}`;

    const deliveryNote = document.getElementById('deliveryNote');
    if (subtotal < 300) {
        deliveryNote.textContent = `Add ₹${(300 - subtotal).toFixed(2)} more for free delivery!`;
        deliveryNote.classList.remove('d-none');
    } else {
        deliveryNote.classList.add('d-none');
    }
}

// Toggle cart sidebar
function toggleCart() {
    const cartSidebar = document.getElementById('cartSidebar');
    const cartOverlay = document.getElementById('cartOverlay');
    
    cartSidebar.classList.toggle('open');
    cartOverlay.classList.toggle('open');
    
    // Prevent body scroll when cart is open
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
    const originalText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Placing Order...';
    
    const customerName = document.getElementById('customerName').value.trim();
    const customerMobile = document.getElementById('customerMobile').value.trim();
    const customerAddress = document.getElementById('customerAddress').value.trim();

    // Validation
    if (!customerName || !customerMobile || !customerAddress) {
        showToast('Please fill in all details', 'error');
        resetSubmitButton();
        return;
    }

    if (!/^[0-9]{10}$/.test(customerMobile)) {
        showToast('Please enter a valid 10-digit mobile number', 'error');
        resetSubmitButton();
        return;
    }

    // Calculate totals
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
            showOrderSuccess(result.order_id);
            clearCart();
            resetCheckoutForm();
        } else {
            throw new Error(result.error || 'Failed to place order');
        }
    } catch (error) {
        console.error('Error placing order:', error);
        showToast(error.message || 'Failed to place order. Please try again.', 'error');
    } finally {
        resetSubmitButton();
    }
    
    function resetSubmitButton() {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// Show order success message
function showOrderSuccess(orderId) {
    const successHTML = `
        <div class="order-success-modal animate-pop">
            <i class="fas fa-check-circle fa-4x text-success mb-3"></i>
            <h3 class="text-success mb-2">Order Placed Successfully!</h3>
            <p class="text-muted mb-3">Your order ID is: <strong>${orderId}</strong></p>
            <p class="small text-muted mb-4">You will receive a confirmation call shortly. Thank you for choosing Vanita Lunch Home!</p>
            <button class="btn btn-primary" onclick="closeOrderSuccess()">Continue Shopping</button>
        </div>
    `;
    
    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'orderSuccessOverlay';
    overlay.innerHTML = successHTML;
    document.body.appendChild(overlay);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

// Close order success modal
function closeOrderSuccess() {
    const overlay = document.getElementById('orderSuccessOverlay');
    if (overlay) {
        overlay.remove();
    }
    document.body.style.overflow = '';
    toggleCart(); // Close cart
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
    try {
        localStorage.setItem('vanita_cart', JSON.stringify(cart));
    } catch (e) {
        console.log('Could not save cart to storage');
    }
}

// Load cart from localStorage
function loadCartFromStorage() {
    try {
        const savedCart = localStorage.getItem('vanita_cart');
        if (savedCart) {
            cart = JSON.parse(savedCart);
            updateCartDisplay();
        }
    } catch (e) {
        console.log('Could not load cart from storage');
        cart = [];
    }
}

// Show toast notification using Bootstrap Toast
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toastTitle');
    const toastMessage = document.getElementById('toastMessage');
    const toastIcon = document.getElementById('toastIcon');
    
    // Set content based on type
    switch(type) {
        case 'success':
            toastTitle.textContent = 'Success';
            toastIcon.className = 'fas fa-check-circle text-success me-2';
            break;
        case 'error':
            toastTitle.textContent = 'Error';
            toastIcon.className = 'fas fa-exclamation-circle text-danger me-2';
            break;
        case 'warning':
            toastTitle.textContent = 'Warning';
            toastIcon.className = 'fas fa-exclamation-triangle text-warning me-2';
            break;
        default:
            toastTitle.textContent = 'Info';
            toastIcon.className = 'fas fa-info-circle text-info me-2';
    }
    
    toastMessage.textContent = message;
    
    // Show toast using Bootstrap
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
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

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // ESC to close cart
    if (e.key === 'Escape') {
        const cartSidebar = document.getElementById('cartSidebar');
        if (cartSidebar.classList.contains('open')) {
            toggleCart();
        }
    }
    
    // Ctrl+K or Cmd+K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('searchInput').focus();
    }
});

// Auto-save cart on page unload
window.addEventListener('beforeunload', function() {
    saveCartToStorage();
});
