// Application state
let cart = [];
let menuItems = [];
let filteredMenuItems = [];
let currentCategory = 'all';
let currentVegFilter = 'all';
let currentSearchTerm = '';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
    loadMenu();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Cart functionality
    document.getElementById('cartBtn').addEventListener('click', showCartPage);
    document.getElementById('backToMenuBtn').addEventListener('click', showHomePage);
    document.getElementById('payNowBtn').addEventListener('click', processPayment);
    
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
}

// Load menu items from API
async function loadMenu() {
    try {
        const response = await fetch('/api/menu');
        if (!response.ok) {
            throw new Error('Failed to load menu');
        }
        menuItems = await response.json();
        filteredMenuItems = [...menuItems];
        renderMenu();
    } catch (error) {
        console.error('Error loading menu:', error);
        showToast('Failed to load menu. Please refresh the page.', 'error');
    }
}

// Handle search functionality
function handleSearch(e) {
    currentSearchTerm = e.target.value.toLowerCase();
    applyFilters();
}

// Handle category filter
function handleCategoryFilter(e) {
    // Update active button
    document.querySelectorAll('.category-filter').forEach(btn => {
        btn.classList.remove('active', 'bg-orange-500', 'text-white');
        btn.classList.add('bg-gray-200', 'text-gray-700');
    });
    e.target.classList.add('active', 'bg-orange-500', 'text-white');
    e.target.classList.remove('bg-gray-200', 'text-gray-700');
    
    currentCategory = e.target.getAttribute('data-category');
    applyFilters();
}

// Handle veg/non-veg filter
function handleVegFilter(e) {
    // Update active button
    document.querySelectorAll('.veg-filter').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');
    
    currentVegFilter = e.target.getAttribute('data-type');
    applyFilters();
}

// Apply all filters
function applyFilters() {
    filteredMenuItems = menuItems.filter(item => {
        // Category filter
        if (currentCategory !== 'all' && item.category !== currentCategory) {
            return false;
        }
        
        // Veg/Non-veg filter
        if (currentVegFilter !== 'all' && item.veg_nonveg !== currentVegFilter) {
            return false;
        }
        
        // Search filter
        if (currentSearchTerm && !item.item_name.toLowerCase().includes(currentSearchTerm) && 
            !item.description.toLowerCase().includes(currentSearchTerm)) {
            return false;
        }
        
        return true;
    });
    
    renderMenu();
}

// Render menu items
function renderMenu() {
    const menuContainer = document.getElementById('menu-container');
    menuContainer.innerHTML = '';
    
    if (filteredMenuItems.length === 0) {
        menuContainer.innerHTML = `
            <div class="col-span-full text-center py-12">
                <i data-lucide="search-x" class="mx-auto h-12 w-12 text-gray-400 mb-4"></i>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No items found</h3>
                <p class="text-gray-500">Try adjusting your search or filters</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    
    filteredMenuItems.forEach(item => {
        const menuCard = createMenuCard(item);
        menuContainer.appendChild(menuCard);
    });
    
    lucide.createIcons();
}

// Create menu card element
function createMenuCard(item) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300';
    
    // Determine category badge color
    const vegType = item.veg_nonveg && item.veg_nonveg.toLowerCase() === 'veg' ? 'veg' : 'non-veg';
    const vegIndicator = vegType === 'veg' ? 
        '<span class="w-3 h-3 bg-green-500 rounded-sm"></span>' : 
        '<span class="w-3 h-3 bg-red-500 rounded-sm"></span>';
    
    card.innerHTML = `
        <div class="relative">
            <img src="https://placehold.co/300x200/f3f4f6/6b7280?text=${encodeURIComponent(item.item_name || 'Food')}" 
                 alt="${escapeHtml(item.item_name)}" 
                 class="w-full h-48 object-cover">
            <div class="absolute top-2 left-2 flex items-center space-x-1 bg-white px-2 py-1 rounded-full">
                ${vegIndicator}
                <span class="text-xs font-medium">${vegType.toUpperCase()}</span>
            </div>
        </div>
        <div class="p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">${escapeHtml(item.item_name)}</h3>
            <p class="text-gray-600 text-sm mb-3 line-clamp-2">${escapeHtml(item.description || 'Delicious food item')}</p>
            <div class="flex items-center justify-between">
                <span class="text-2xl font-bold text-orange-500">₹${parseFloat(item.price).toFixed(2)}</span>
                <button onclick="addToCart(${item.id})" 
                        class="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors duration-300 flex items-center space-x-2">
                    <i data-lucide="plus" class="h-4 w-4"></i>
                    <span>Add</span>
                </button>
            </div>
        </div>
    `;
    
    return card;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
    
    updateCartCount();
    showToast(`${item.item_name} added to cart!`);
}

// Remove item from cart
function removeFromCart(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    updateCartCount();
    if (document.getElementById('cartView').style.display !== 'none') {
        renderCartPage();
    }
}

// Update quantity in cart
function updateQuantity(itemId, change) {
    const item = cart.find(i => i.id === itemId);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            removeFromCart(itemId);
        } else {
            updateCartCount();
            if (document.getElementById('cartView').style.display !== 'none') {
                renderCartPage();
            }
        }
    }
}

// Update cart count in header
function updateCartCount() {
    const cartCount = document.getElementById('cartCount');
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    
    if (totalItems > 0) {
        cartCount.textContent = totalItems;
        cartCount.classList.remove('hidden');
    } else {
        cartCount.classList.add('hidden');
    }
}

// Show cart page
function showCartPage() {
    if (cart.length === 0) {
        showToast('Your cart is empty!', 'error');
        return;
    }
    
    document.getElementById('homeView').classList.add('hidden');
    document.getElementById('cartView').classList.remove('hidden');
    renderCartPage();
}

// Show home page
function showHomePage() {
    document.getElementById('cartView').classList.add('hidden');
    document.getElementById('homeView').classList.remove('hidden');
}

// Render cart page
function renderCartPage() {
    const cartItemsContainer = document.getElementById('cart-page-items');
    const cartSummaryContainer = document.getElementById('cart-page-summary');
    
    // Render cart items
    cartItemsContainer.innerHTML = '';
    
    if (cart.length === 0) {
        cartItemsContainer.innerHTML = `
            <div class="text-center py-12">
                <i data-lucide="shopping-cart" class="mx-auto h-12 w-12 text-gray-400 mb-4"></i>
                <h3 class="text-lg font-medium text-gray-900 mb-2">Your cart is empty</h3>
                <button onclick="showHomePage()" class="text-orange-500 hover:text-orange-600">Continue shopping</button>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    
    cart.forEach(item => {
        const cartItem = document.createElement('div');
        cartItem.className = 'bg-white p-4 rounded-lg shadow-md';
        cartItem.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <h4 class="font-medium text-gray-900">${escapeHtml(item.name)}</h4>
                    <p class="text-sm text-gray-600">₹${parseFloat(item.price).toFixed(2)} each</p>
                </div>
                <div class="flex items-center space-x-3">
                    <div class="flex items-center space-x-2">
                        <button onclick="updateQuantity(${item.id}, -1)" class="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center hover:bg-gray-300">
                            <i data-lucide="minus" class="h-4 w-4"></i>
                        </button>
                        <span class="w-8 text-center font-medium">${item.quantity}</span>
                        <button onclick="updateQuantity(${item.id}, 1)" class="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center hover:bg-gray-300">
                            <i data-lucide="plus" class="h-4 w-4"></i>
                        </button>
                    </div>
                    <button onclick="removeFromCart(${item.id})" class="text-red-500 hover:text-red-700 p-1">
                        <i data-lucide="trash-2" class="h-4 w-4"></i>
                    </button>
                </div>
            </div>
            <div class="mt-2 text-right">
                <span class="font-semibold">₹${(parseFloat(item.price) * item.quantity).toFixed(2)}</span>
            </div>
        `;
        cartItemsContainer.appendChild(cartItem);
    });
    
    // Render cart summary
    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
    const deliveryFee = subtotal > 300 ? 0 : 40;
    const total = subtotal + deliveryFee;
    
    cartSummaryContainer.innerHTML = `
        <div class="flex justify-between">
            <span>Subtotal</span>
            <span>₹${subtotal.toFixed(2)}</span>
        </div>
        <div class="flex justify-between">
            <span>Delivery Fee</span>
            <span>${deliveryFee === 0 ? 'FREE' : '₹' + deliveryFee.toFixed(2)}</span>
        </div>
        <div class="flex justify-between font-semibold text-lg border-t pt-3">
            <span>Total</span>
            <span>₹${total.toFixed(2)}</span>
        </div>
        ${subtotal <= 300 ? '<p class="text-sm text-gray-500 mt-2">Add ₹' + (300 - subtotal).toFixed(2) + ' more for free delivery!</p>' : ''}
    `;
    
    lucide.createIcons();
}

// Process payment
async function processPayment() {
    const name = document.getElementById('customerNameCart').value.trim();
    const mobile = document.getElementById('customerMobileCart').value.trim();
    const address = document.getElementById('customerAddress').value.trim();
    
    if (!name || !mobile || !address) {
        showToast('Please fill in all delivery details', 'error');
        return;
    }
    
    if (!/^[0-9]{10}$/.test(mobile)) {
        showToast('Please enter a valid 10-digit mobile number', 'error');
        return;
    }
    
    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
    const deliveryFee = subtotal > 300 ? 0 : 40;
    const total = (subtotal + deliveryFee) * 100; // Amount in paise for Razorpay
    
    const options = {
        "key": "rzp_test_1234567890", // Replace with your Razorpay Key ID
        "amount": total,
        "currency": "INR",
        "name": "Vanita Lunch Home",
        "description": "Food Order Payment",
        "image": "/static/logo.png",
        "handler": function (response) {
            handlePaymentSuccess(response, {
                name: name,
                mobile: mobile,
                address: address,
                amount: total / 100
            });
        },
        "prefill": {
            "name": name,
            "email": "",
            "contact": mobile
        },
        "notes": {
            "address": address
        },
        "theme": {
            "color": "#f97316"
        },
        "modal": {
            "ondismiss": function(){
                showToast('Payment cancelled', 'error');
            }
        }
    };
    
    const rzp = new Razorpay(options);
    rzp.open();
}

// Handle payment success
async function handlePaymentSuccess(response, customerDetails) {
    try {
        const orderData = {
            name: customerDetails.name,
            mobile: customerDetails.mobile,
            address: customerDetails.address,
            cart_items: cart,
            payment_id: response.razorpay_payment_id,
            amount: customerDetails.amount
        };
        
        const apiResponse = await fetch('/api/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });
        
        if (!apiResponse.ok) {
            throw new Error('Failed to place order');
        }
        
        const result = await apiResponse.json();
        
        if (result.success) {
            showToast('Order placed successfully! You will receive a confirmation call shortly.');
            cart = [];
            updateCartCount();
            showHomePage();
            
            // Clear form
            document.getElementById('customerDetailsForm').reset();
        } else {
            throw new Error(result.message || 'Failed to place order');
        }
    } catch (error) {
        console.error('Error placing order:', error);
        showToast('Order placed but there was an issue. Please contact us if needed.', 'error');
    }
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    
    toastMessage.textContent = message;
    
    // Set toast color based on type
    if (type === 'error') {
        toast.className = 'fixed bottom-5 right-5 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg animate-pop';
    } else {
        toast.className = 'fixed bottom-5 right-5 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg animate-pop';
    }
    
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4000);
}