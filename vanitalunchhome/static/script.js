// Global variables
let menuItems = [];
let cart = [];
let filteredMenuItems = [];
let currentCategory = 'all';
let currentVegFilter = 'all';
let currentSearchTerm = '';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
    loadMenuItems();
    setupEventListeners();
    loadCartFromStorage();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('cartBtn').addEventListener('click', toggleCart);
    document.getElementById('closeCartBtn').addEventListener('click', toggleCart);
    document.getElementById('cartOverlay').addEventListener('click', toggleCart);
    document.getElementById('payNowBtn').addEventListener('click', handleOrderSubmit);
    
    document.getElementById('searchInput').addEventListener('input', handleSearch);
    document.querySelectorAll('.category-filter').forEach(button => {
        button.addEventListener('click', handleCategoryFilter);
    });
    document.querySelectorAll('.veg-filter').forEach(button => {
        button.addEventListener('click', handleVegFilter);
    });

    document.getElementById('customerForm').addEventListener('submit', (e) => e.preventDefault());
}

// Load menu items from the backend API

async function loadMenuItems() {
    const menuContainer = document.getElementById('menu-container');
    try {
        // --- THIS URL IS NOW CORRECTED ---
        const response = await fetch('/api/menu-items'); // Changed from /api/menu
        if (!response.ok) throw new Error('Failed to load menu');
        
        menuItems = await response.json();
        applyFilters();

    } catch (error) {
        console.error('Error loading menu:', error);
        menuContainer.innerHTML = `<p class="col-span-full text-center text-red-500">Could not load menu.</p>`;
    }
}

// Render menu items on the page
function renderMenu() {
    const container = document.getElementById('menu-container');
    container.innerHTML = ''; 

    if (filteredMenuItems.length === 0) {
        container.innerHTML = `<div class="col-span-full text-center py-12"><h3 class="text-lg font-medium">No items found matching your criteria.</h3></div>`;
        return;
    }

    filteredMenuItems.forEach(item => {
        const imageUrl = item.image_url || `https://placehold.co/600x400/f3f4f6/6b7280?text=No+Image`;
        
        const card = document.createElement('div');
        card.className = 'bg-white rounded-lg shadow-md overflow-hidden transform hover:scale-105 transition-transform duration-300';
        card.innerHTML = `
            <img src="${imageUrl}" alt="${item.item_name}" class="h-48 w-full object-cover">
            <div class="p-4">
                <h4 class="text-lg font-bold">${item.item_name}</h4>
                <p class="text-sm text-gray-600 mt-1 h-10 overflow-hidden">${item.description || ''}</p>
                <div class="flex justify-between items-center mt-4">
                    <span class="text-lg font-bold text-orange-600">₹${parseFloat(item.price).toFixed(2)}</span>
                    <button class="add-to-cart-btn bg-orange-100 text-orange-700 font-semibold px-4 py-2 rounded-lg hover:bg-orange-200" onclick="addToCart(${item.id})">Add to Cart</button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

// --- THIS FUNCTION IS FIXED ---
// It now safely checks for null values before calling .toLowerCase()
function applyFilters() {
    filteredMenuItems = menuItems.filter(item => {
        const categoryMatch = currentCategory === 'all' || (item.category && item.category.toLowerCase() === currentCategory);
        
        const vegMatch = currentVegFilter === 'all' || (item.veg_nonveg && item.veg_nonveg.toLowerCase().replace(/ /g, '-') === currentVegFilter);

        const searchMatch = !currentSearchTerm ||
            (item.item_name && item.item_name.toLowerCase().includes(currentSearchTerm)) ||
            (item.description && item.description.toLowerCase().includes(currentSearchTerm));
            
        return categoryMatch && vegMatch && searchMatch;
    });
    renderMenu();
}

function handleSearch(e) {
    currentSearchTerm = e.target.value.toLowerCase();
    applyFilters();
}

function handleCategoryFilter(e) {
    document.querySelectorAll('.category-filter').forEach(btn => {
        btn.classList.remove('active', 'bg-orange-500', 'text-white');
        btn.classList.add('bg-gray-200', 'text-gray-700');
    });
    const clickedButton = e.currentTarget;
    clickedButton.classList.add('active', 'bg-orange-500', 'text-white');
    clickedButton.classList.remove('bg-gray-200', 'text-gray-700');
    currentCategory = clickedButton.dataset.category;
    applyFilters();
}

function handleVegFilter(e) {
    document.querySelectorAll('.veg-filter').forEach(btn => {
        btn.classList.remove('active');
        btn.classList.remove('bg-green-100', 'text-green-800');
        btn.classList.remove('bg-red-100', 'text-red-800');
        btn.classList.add('bg-gray-100', 'text-gray-700');
    });
    const clickedButton = e.currentTarget;
    clickedButton.classList.add('active');
    clickedButton.classList.remove('bg-gray-100', 'text-gray-700');
    if (clickedButton.dataset.type === 'veg') {
        clickedButton.classList.add('bg-green-100', 'text-green-800');
    } else if (clickedButton.dataset.type === 'non-veg') {
         clickedButton.classList.add('bg-red-100', 'text-red-800');
    }

    currentVegFilter = clickedButton.dataset.type;
    applyFilters();
}

// Cart and Order functions
function addToCart(itemId) {
    const item = menuItems.find(i => i.id === itemId);
    if (!item) return;
    const existingItem = cart.find(i => i.id === itemId);
    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({ id: item.id, name: item.item_name, price: item.price, quantity: 1 });
    }
    updateCartDisplay();
    saveCartToStorage();
    showToast(`${item.item_name} added to cart!`);
}

function updateQuantity(itemId, change) {
    const item = cart.find(i => i.id === itemId);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            cart = cart.filter(i => i.id !== itemId);
        }
    }
    updateCartDisplay();
    saveCartToStorage();
}

function removeFromCart(itemId) {
    const item = cart.find(i => i.id === itemId);
    cart = cart.filter(i => i.id !== itemId);
    updateCartDisplay();
    saveCartToStorage();
    showToast(`${item.name} removed from cart.`, 'info');
}

function updateCartDisplay() {
    const cartCount = document.getElementById('cartCount');
    const cartItems = document.getElementById('cart-page-items');
    const cartSummary = document.getElementById('cart-page-summary');
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

    cartCount.textContent = totalItems;
    cartCount.classList.toggle('hidden', totalItems === 0);

    if (cart.length === 0) {
        cartItems.innerHTML = '<p class="text-gray-500 text-center py-4">Your cart is empty</p>';
        cartSummary.innerHTML = '';
        return;
    }
    
    let cartHTML = '';
    cart.forEach(item => {
        cartHTML += `
            <div class="py-3 border-b">
                <div class="flex justify-between items-center">
                    <div>
                        <h6 class="font-semibold">${item.name}</h6>
                        <small class="text-gray-500">₹${parseFloat(item.price).toFixed(2)} x ${item.quantity}</small>
                    </div>
                    <div class="font-bold">₹${(item.price * item.quantity).toFixed(2)}</div>
                </div>
                <div class="flex items-center mt-2">
                    <button class="bg-gray-200 w-7 h-7 rounded-full font-bold" onclick="updateQuantity(${item.id}, -1)">-</button>
                    <span class="mx-3">${item.quantity}</span>
                    <button class="bg-gray-200 w-7 h-7 rounded-full font-bold" onclick="updateQuantity(${item.id}, 1)">+</button>
                    <button class="text-red-500 hover:text-red-700 ml-auto text-sm font-medium" onclick="removeFromCart(${item.id})">Remove</button>
                </div>
            </div>`;
    });
    cartItems.innerHTML = cartHTML;
    
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    cartSummary.innerHTML = `<div class="flex justify-between font-bold mt-2 text-lg"><span>Total</span><span>₹${subtotal.toFixed(2)}</span></div>`;
}

function toggleCart() {
    const cartSidebar = document.getElementById('cartSidebar');
    const cartOverlay = document.getElementById('cartOverlay');
    cartSidebar.classList.toggle('translate-x-full');
    cartOverlay.classList.toggle('hidden');
    document.body.style.overflow = cartSidebar.classList.contains('translate-x-full') ? '' : 'hidden';
}

async function handleOrderSubmit() {
    const submitBtn = document.getElementById('payNowBtn');
    submitBtn.querySelector('span').textContent = 'Placing...';
    submitBtn.disabled = true;

    // --- CRITICAL FIX: Check cart before proceeding ---
    if (cart.length === 0) {
        showToast('Your cart is empty. Please add items first.', 'error');
        submitBtn.querySelector('span').textContent = 'Place Order (Cash)';
        submitBtn.disabled = false;
        return;
    }
    
    const customerName = document.getElementById('customerNameCart').value.trim();
    const customerMobile = document.getElementById('customerMobileCart').value.trim();
    const customerAddress = document.getElementById('customerAddress').value.trim();

    if (!customerName || !customerMobile || !customerAddress) {
        showToast('Please fill in all delivery details.', 'error');
        submitBtn.querySelector('span').textContent = 'Place Order (Cash)';
        submitBtn.disabled = false;
        return;
    }

    // --- FIXED: Match the field names expected by Flask backend ---
    const orderData = {
        customer_name: customerName,     // Changed from 'name'
        customer_mobile: customerMobile, // Changed from 'mobile'
        customer_address: customerAddress, // Changed from 'address'
        items: cart.map(item => ({       // Changed from 'cart_items'
            id: item.id, 
            quantity: item.quantity
        }))
    };

    try {
        const response = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Failed to place order.');
        
        showToast(result.message, 'success');
        clearCart();
        resetCheckoutForm();
        toggleCart();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.querySelector('span').textContent = 'Place Order (Cash)';
        submitBtn.disabled = false;
    }
}
// Helper functions
function clearCart() {
    cart = [];
    updateCartDisplay();
    saveCartToStorage();
}
function resetCheckoutForm() {
    document.getElementById('customerForm').reset();
}
function saveCartToStorage() {
    localStorage.setItem('vanita_cart', JSON.stringify(cart));
}
function loadCartFromStorage() {
    const savedCart = localStorage.getItem('vanita_cart');
    if (savedCart) {
        cart = JSON.parse(savedCart);
        updateCartDisplay();
    }
}
function showToast(message, type = 'success') {
    const toastEl = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    toastMessage.textContent = message;
    
    const colors = { success: 'bg-green-500', error: 'bg-red-500', info: 'bg-blue-500' };
    toastEl.className = `fixed bottom-5 right-5 text-white px-6 py-3 rounded-lg shadow-lg animate-pop z-50 ${colors[type] || colors.success}`;

    toastEl.classList.remove('hidden');
    setTimeout(() => {
        toastEl.classList.add('hidden');
    }, 3000);
}

