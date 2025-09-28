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
    // Cart functionality
    document.getElementById('cartBtn').addEventListener('click', toggleCart);
    document.getElementById('closeCartBtn').addEventListener('click', toggleCart);
    document.getElementById('cartOverlay').addEventListener('click', toggleCart);
    document.getElementById('payNowBtn').addEventListener('click', handleOrderSubmit);
    
    // --- ADDED: Event Listeners for Search and Filters ---
    document.getElementById('searchInput').addEventListener('input', handleSearch);
    document.querySelectorAll('.category-filter').forEach(button => {
        button.addEventListener('click', handleCategoryFilter);
    });
    document.querySelectorAll('.veg-filter').forEach(button => {
        button.addEventListener('click', handleVegFilter);
    });

    // OTP functionality
    document.getElementById('customerForm').addEventListener('submit', (e) => e.preventDefault());
    document.getElementById('sendOtpBtn').addEventListener('click', handleSendOtp);
}

// Load menu items from the backend API
async function loadMenuItems() {
    const menuContainer = document.getElementById('menu-container');
    try {
        const response = await fetch('/api/menu');
        if (!response.ok) throw new Error('Failed to load menu');
        
        menuItems = await response.json();
        applyFilters(); // Apply default filters on load

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
        container.innerHTML = `<div class="col-span-full text-center py-12"><h3 class="text-lg font-medium">No items found</h3></div>`;
        return;
    }

    filteredMenuItems.forEach(item => {
        // --- FIX: Use item.image_url ---
        const imageUrl = item.image_url || `https://placehold.co/600x400/f3f4f6/6b7280?text=No+Image`;
        
        const card = document.createElement('div');
        card.className = 'bg-white rounded-lg shadow-md overflow-hidden transform hover:scale-105 transition-transform duration-300';
        card.innerHTML = `
            <img src="${imageUrl}" alt="${item.item_name}" class="h-48 w-full object-cover">
            <div class="p-4">
                <h4 class="text-lg font-bold">${item.item_name}</h4>
                <p class="text-sm text-gray-600 mt-1">${item.description || ''}</p>
                <div class="flex justify-between items-center mt-4">
                    <span class="text-lg font-bold text-orange-600">₹${parseFloat(item.price).toFixed(2)}</span>
                    <button class="add-to-cart-btn bg-orange-100 text-orange-700 font-semibold px-4 py-2 rounded-lg hover:bg-orange-200 transition-colors text-sm" onclick="addToCart(${item.id})">Add to Cart</button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

// --- ADDED: Functions to handle searching and filtering ---
function applyFilters() {
    filteredMenuItems = menuItems.filter(item => {
        const categoryMatch = currentCategory === 'all' || (item.category && item.category.toLowerCase() === currentCategory);
        const vegMatch = currentVegFilter === 'all' || (item.veg_nonveg && item.veg_nonveg.toLowerCase().replace('-', '_') === currentVegFilter.replace('-', '_'));
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
    document.querySelectorAll('.veg-filter').forEach(btn => btn.classList.remove('active'));
    const clickedButton = e.currentTarget;
    clickedButton.classList.add('active');
    currentVegFilter = clickedButton.dataset.type;
    applyFilters();
}
// --- END of new search/filter functions ---


// Cart Logic (No changes here, but included for completeness)
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
    const itemName = item ? item.name : 'Item';
    cart = cart.filter(i => i.id !== itemId);
    updateCartDisplay();
    saveCartToStorage();
    showToast(`${itemName} removed from cart.`, 'info');
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
                    <button onclick="updateQuantity(${item.id}, -1)">-</button>
                    <span class="mx-2">${item.quantity}</span>
                    <button onclick="updateQuantity(${item.id}, 1)">+</button>
                    <button class="text-red-500 ml-auto" onclick="removeFromCart(${item.id})">Remove</button>
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

async function handleSendOtp() {
    const mobileInput = document.getElementById('customerMobileCart');
    const sendOtpBtn = document.getElementById('sendOtpBtn');
    const otpMessage = document.getElementById('otpMessage');
    const payNowBtn = document.getElementById('payNowBtn');
    const mobileNumber = mobileInput.value.trim();

    if (!/^\d{10}$/.test(mobileNumber)) {
        showToast('Please enter a valid 10-digit mobile number.', 'error');
        return;
    }

    sendOtpBtn.disabled = true;
    sendOtpBtn.textContent = 'Sending...';

    try {
        const response = await fetch('/api/send-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mobile: mobileNumber })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Server error');
        
        document.getElementById('otp-container').classList.remove('hidden');
        otpMessage.textContent = 'OTP sent successfully.';
        otpMessage.className = 'text-xs text-green-600 mt-1';
        payNowBtn.disabled = false;
        payNowBtn.classList.remove('bg-orange-300', 'cursor-not-allowed');
        payNowBtn.classList.add('bg-orange-500', 'hover:bg-orange-600');
        showToast('OTP sent!', 'success');
    } catch (error) {
        otpMessage.textContent = error.message;
        otpMessage.className = 'text-xs text-red-600 mt-1';
        showToast(error.message, 'error');
    } finally {
        sendOtpBtn.disabled = false;
        sendOtpBtn.textContent = 'Send OTP';
    }
}

async function handleOrderSubmit() {
    const submitBtn = document.getElementById('payNowBtn');
    const originalText = submitBtn.querySelector('span').textContent;
    submitBtn.querySelector('span').textContent = 'Placing...';
    submitBtn.disabled = true;
    
    const customerName = document.getElementById('customerNameCart').value.trim();
    const customerMobile = document.getElementById('customerMobileCart').value.trim();
    const customerAddress = document.getElementById('customerAddress').value.trim();
    const otp = document.getElementById('customerOtp').value.trim();

    if (!customerName || !customerMobile || !customerAddress || !otp) {
        showToast('Please fill all fields and enter OTP.', 'error');
        submitBtn.querySelector('span').textContent = originalText;
        submitBtn.disabled = false;
        return;
    }

    const orderData = {
        name: customerName,
        mobile: customerMobile,
        address: customerAddress,
        otp: otp,
        cart_items: cart.map(item => ({ id: item.id, quantity: item.quantity })),
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
        submitBtn.querySelector('span').textContent = originalText;
        submitBtn.disabled = true;
        submitBtn.classList.add('bg-orange-300', 'cursor-not-allowed');
        submitBtn.classList.remove('bg-orange-500', 'hover:bg-orange-600');
    }
}

function clearCart() {
    cart = [];
    updateCartDisplay();
    saveCartToStorage();
}

function resetCheckoutForm() {
    document.getElementById('customerForm').reset();
    document.getElementById('otp-container').classList.add('hidden');
    document.getElementById('otpMessage').textContent = '';
}

function saveCartToStorage() {
    localStorage.setItem('vanita_cart', JSON.stringify(cart));
}

function loadCartFromStorage() {
    const savedCart = localStorage.getItem('vanita_cart');
    if (savedCart) {
        try {
            cart = JSON.parse(savedCart);
            updateCartDisplay();
        } catch (error) {
            cart = [];
        }
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
