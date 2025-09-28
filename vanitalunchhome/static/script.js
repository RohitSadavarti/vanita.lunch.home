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
    document.getElementById('customerDetailsForm').addEventListener('submit', (e) => e.preventDefault()); // Prevent default form submission
    document.getElementById('payNowBtn').addEventListener('click', handleOrderSubmit);
    
    // --- OTP: Event Listener for the "Send OTP" button ---
    document.getElementById('sendOtpBtn').addEventListener('click', handleSendOtp);
}

// Load menu items from Django backend
async function loadMenuItems() {
    const loadingIndicator = document.getElementById('menu-container'); // Use container for loading

    try {
        // Assuming the Flask endpoint is /api/menu
        const response = await fetch('/api/menu');

        if (!response.ok) {
            throw new Error('Failed to load menu items');
        }

        menuItems = await response.json();
        filteredItems = [...menuItems];
        renderMenuItems();

    } catch (error) {
        console.error('Error loading menu items:', error);
        loadingIndicator.innerHTML = `
            <div class="col-span-full text-center py-5">
                <h4>Unable to load menu</h4>
                <p class="text-muted">Please check your connection and try again</p>
                <button class="btn btn-primary" onclick="loadMenuItems()">Retry</button>
            </div>
        `;
    }
}

// Render menu items
function renderMenuItems() {
    const container = document.getElementById('menu-container');

    if (filteredItems.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-5">
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
                    <p class="text-sm text-gray-600 mt-1">${item.description || ''}</p>
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
        const itemTotal = parseFloat(item.price) * item.quantity;
        cartHTML += `
            <div class="cart-item py-3 border-b">
                <div class="flex justify-between items-center">
                    <div>
                        <h6 class="font-semibold">${item.name}</h6>
                        <small class="text-gray-500">₹${parseFloat(item.price).toFixed(2)} x ${item.quantity}</small>
                    </div>
                    <div class="font-bold">₹${itemTotal.toFixed(2)}</div>
                </div>
                <div class="flex items-center mt-2">
                    <button class="bg-gray-200 w-7 h-7 rounded-full font-bold" onclick="updateQuantity(${item.id}, -1)">-</button>
                    <span class="mx-3">${item.quantity}</span>
                    <button class="bg-gray-200 w-7 h-7 rounded-full font-bold" onclick="updateQuantity(${item.id}, 1)">+</button>
                    <button class="text-red-500 hover:text-red-700 ml-auto text-sm font-medium" onclick="removeFromCart(${item.id})">Remove</button>
                </div>
            </div>
        `;
    });
    cartItems.innerHTML = cartHTML;

    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
    cartSummary.innerHTML = `
        <div class="flex justify-between">
            <span>Subtotal</span>
            <span>₹${subtotal.toFixed(2)}</span>
        </div>
        <div class="flex justify-between font-bold mt-2 text-lg">
            <span>Total</span>
            <span>₹${subtotal.toFixed(2)}</span>
        </div>
    `;
}

// Toggle cart sidebar
function toggleCart() {
    const cartSidebar = document.getElementById('cartSidebar');
    const cartOverlay = document.getElementById('cartOverlay');
    cartSidebar.classList.toggle('translate-x-full');
    cartOverlay.classList.toggle('hidden');
    document.body.style.overflow = cartSidebar.classList.contains('translate-x-full') ? '' : 'hidden';
}

// --- OTP: Function to handle sending the OTP ---
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

        if (response.ok && result.success) {
            document.getElementById('otp-container').classList.remove('hidden');
            otpMessage.textContent = 'OTP has been sent to your mobile number.';
            otpMessage.className = 'text-xs text-green-600 mt-1';
            
            // Enable the Place Order button
            payNowBtn.disabled = false;
            payNowBtn.classList.remove('bg-orange-300', 'cursor-not-allowed');
            payNowBtn.classList.add('bg-orange-500', 'hover:bg-orange-600');

            showToast('OTP sent successfully!', 'success');
        } else {
            throw new Error(result.error || 'Failed to send OTP.');
        }
    } catch (error) {
        console.error('Send OTP error:', error);
        otpMessage.textContent = error.message;
        otpMessage.className = 'text-xs text-red-600 mt-1';
        showToast(error.message, 'error');
    } finally {
        sendOtpBtn.disabled = false;
        sendOtpBtn.textContent = 'Send OTP';
    }
}


// Handle order submission
async function handleOrderSubmit() {
    const submitBtn = document.getElementById('payNowBtn');
    const originalText = submitBtn.querySelector('span').textContent;
    submitBtn.querySelector('span').textContent = 'Placing Order...';
    submitBtn.disabled = true;
    
    const customerName = document.getElementById('customerNameCart').value.trim();
    const customerMobile = document.getElementById('customerMobileCart').value.trim();
    const customerAddress = document.getElementById('customerAddress').value.trim();
    const otp = document.getElementById('customerOtp').value.trim(); // Get OTP value

    // Validate inputs
    if (!customerName || !customerMobile || !customerAddress || !otp) {
        showToast('Please fill in all fields and enter the OTP.', 'error');
        submitBtn.querySelector('span').textContent = originalText;
        submitBtn.disabled = false;
        return;
    }

    if (!/^\d{10}$/.test(customerMobile)) {
        showToast('Please enter a valid 10-digit mobile number.', 'error');
        submitBtn.querySelector('span').textContent = originalText;
        submitBtn.disabled = false;
        return;
    }

    if (cart.length === 0) {
        showToast('Your cart is empty.', 'error');
        submitBtn.querySelector('span').textContent = originalText;
        submitBtn.disabled = false;
        return;
    }

    const orderData = {
        name: customerName,
        mobile: customerMobile,
        address: customerAddress,
        otp: otp, // Include OTP in the payload
        cart_items: cart.map(item => ({ id: item.id, quantity: item.quantity })),
    };

    try {
        const response = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showToast(result.message, 'success');
            clearCart();
            resetCheckoutForm();
            toggleCart();
        } else {
            throw new Error(result.error || 'Failed to place order.');
        }
    } catch (error) {
        console.error('Order placement error:', error);
        showToast(error.message, 'error');
    } finally {
        submitBtn.querySelector('span').textContent = originalText;
        // Keep the button disabled until a new OTP is sent
        submitBtn.disabled = true;
        submitBtn.classList.add('bg-orange-300', 'cursor-not-allowed');
        submitBtn.classList.remove('bg-orange-500', 'hover:bg-orange-600');
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
    document.getElementById('customerDetailsForm').reset();
    document.getElementById('otp-container').classList.add('hidden');
    document.getElementById('otpMessage').textContent = '';
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

// Show toast notification
function showToast(message, type = 'success') {
    const toastEl = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');

    toastMessage.textContent = message;

    // Reset classes
    toastEl.className = 'fixed bottom-5 right-5 text-white px-6 py-3 rounded-lg shadow-lg animate-pop';
    
    if (type === 'success') {
        toastEl.classList.add('bg-green-500');
    } else if (type === 'error') {
        toastEl.classList.add('bg-red-500');
    } else if (type === 'warning') {
        toastEl.classList.add('bg-yellow-500');
    }

    toastEl.classList.remove('hidden');
    setTimeout(() => {
        toastEl.classList.add('hidden');
    }, 3000);
}

// No need for getCookie as Flask doesn't use CSRF tokens by default in this setup
