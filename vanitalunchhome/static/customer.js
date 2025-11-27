// vanitalunchhome/static/customer.js

// Global State
let menuItems = [];
let cart = [];
let currentUser = null; // Stores user object if logged in

document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
    checkAuthStatus(); // Check if user is already logged in or allow guest access
    setupEventListeners();
});

// --- AUTHENTICATION LOGIC ---

function checkAuthStatus() {
    // 1. Always load the menu items, regardless of login status
    loadMenuItems(); 
    loadCartFromStorage();

    const storedUser = localStorage.getItem('vlh_user');
    
    if (storedUser) {
        try {
            currentUser = JSON.parse(storedUser);
        } catch (e) {
            console.error("Error parsing user data", e);
            currentUser = null;
        }
    } else {
        currentUser = null;
    }

    // 2. Decide whether to show Landing Page or Main App
    // Change this logic if you want to force the Landing Page first.
    // Currently set to: Show App immediately (Guest Mode) so menu is visible.
    if (currentUser) {
        showApp();
    } else {
        // Option A: Show Landing Page first (User must click "Order Now" to see menu)
        // showLanding(); 
        
        // Option B: Show App immediately as Guest (Menu is visible) - CHOSEN FIX
        showApp(); 
    }
}

function showApp() {
    document.getElementById('landing-page').classList.add('hidden');
    document.getElementById('main-app').classList.remove('hidden');
    
    // Update UI with user details OR Guest details
    if (currentUser) {
        document.getElementById('user-name-display').textContent = currentUser.name;
        document.getElementById('user-avatar').textContent = currentUser.name.charAt(0).toUpperCase();
        document.getElementById('user-location-display').textContent = currentUser.address || 'Add Address';
        // Show Profile/Logout options
        document.getElementById('user-name-display').parentElement.classList.remove('hidden'); 
    } else {
        // Guest View
        document.getElementById('user-name-display').textContent = "Guest";
        document.getElementById('user-avatar').textContent = "G";
        document.getElementById('user-location-display').textContent = "Select Location";
        
        // You might want to change the "Log Out" button to "Log In" for guests
        const dropdown = document.querySelector('.group .absolute');
        if(dropdown) {
            dropdown.innerHTML = `<a href="#" onclick="showAuthModal('login')" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Log In</a>`;
        }
    }
}

function showLanding() {
    document.getElementById('landing-page').classList.remove('hidden');
    document.getElementById('main-app').classList.add('hidden');
    currentUser = null;
}

function logoutUser() {
    localStorage.removeItem('vlh_user');
    // localStorage.removeItem('vanita_cart'); // Optional: keep cart on logout?
    currentUser = null;
    
    // Refresh to reset state or just show landing
    window.location.reload(); 
}

// --- MODAL HANDLING ---

window.showAuthModal = function(tab) {
    document.getElementById('auth-modal').classList.remove('hidden');
    switchAuthTab(tab);
};

window.closeAuthModal = function() {
    document.getElementById('auth-modal').classList.add('hidden');
};

window.switchAuthTab = function(tab) {
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.add('hidden');
    document.getElementById('otp-form').classList.add('hidden');
    
    if (tab === 'login') document.getElementById('login-form').classList.remove('hidden');
    if (tab === 'register') document.getElementById('register-form').classList.remove('hidden');
    if (tab === 'otp') document.getElementById('otp-form').classList.remove('hidden');
};

// --- API CALLS FOR AUTH ---

window.handleRegister = async function(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = 'Sending...';
    btn.disabled = true;

    const data = {
        full_name: document.getElementById('reg-name').value,
        mobile: document.getElementById('reg-mobile').value,
        email: document.getElementById('reg-email').value,
        password: document.getElementById('reg-password').value,
        address: document.getElementById('reg-address').value
    };

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.success) {
            // Store temp email for OTP verification
            localStorage.setItem('temp_verify_email', data.email);
            document.getElementById('otp-email-display').innerText = data.email;
            switchAuthTab('otp');
            showToast('OTP sent to your email!', 'success');
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Registration failed. Try again.', 'error');
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
};

window.handleVerifyOTP = async function(e) {
    e.preventDefault();
    const otp = document.getElementById('otp-input').value;
    const email = localStorage.getItem('temp_verify_email');

    try {
        const response = await fetch('/api/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, otp })
        });
        const result = await response.json();

        if (result.success) {
            // Save user and login
            localStorage.setItem('vlh_user', JSON.stringify(result.user));
            localStorage.removeItem('temp_verify_email');
            closeAuthModal();
            // Reload to apply logged-in state
            window.location.reload(); 
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Verification failed.', 'error');
    }
};

window.handleLogin = async function(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.innerText = 'Logging in...';
    btn.disabled = true;

    const data = {
        username: document.getElementById('login-username').value,
        password: document.getElementById('login-password').value
    };

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.success) {
            localStorage.setItem('vlh_user', JSON.stringify(result.user));
            closeAuthModal();
            window.location.reload(); // Reload to update UI completely
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Login error.', 'error');
    } finally {
        btn.innerText = 'Log In';
        btn.disabled = false;
    }
};

// --- MENU & CART LOGIC ---

async function loadMenuItems() {
    const container = document.getElementById('menu-container');
    if (!container) return; // Guard clause

    container.innerHTML = '<div class="col-span-full text-center py-10"><div class="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500 mx-auto"></div></div>';
    
    try {
        const response = await fetch('/api/menu-items');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Handle inconsistent API response structure (array vs object)
        menuItems = Array.isArray(data) ? data : (data.menu_items || []);
        
        renderMenu(menuItems);
    } catch (error) {
        console.error("Failed to load menu:", error);
        container.innerHTML = `
            <div class="col-span-full text-center text-red-500">
                <p>Failed to load menu items.</p>
                <p class="text-xs text-gray-400 mt-2">${error.message}</p>
                <button onclick="loadMenuItems()" class="mt-4 px-4 py-2 bg-orange-100 text-orange-600 rounded">Retry</button>
            </div>`;
    }
}

function renderMenu(items) {
    const container = document.getElementById('menu-container');
    if (!container) return;
    container.innerHTML = '';
    
    if (!items || items.length === 0) {
        container.innerHTML = '<p class="col-span-full text-center text-gray-500">No items available.</p>';
        return;
    }

    items.forEach(item => {
        // Fallback image if URL is missing or null
        const img = item.image_url ? item.image_url : `https://placehold.co/600x400/f3f4f6/9ca3af?text=${encodeURIComponent(item.item_name)}`;
        
        const card = document.createElement('div');
        card.className = 'bg-white rounded-xl shadow-sm hover:shadow-md transition overflow-hidden border border-gray-100 flex flex-col h-full group';
        card.innerHTML = `
            <div class="relative h-48 overflow-hidden">
                <img src="${img}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" alt="${item.item_name}">
                <div class="absolute top-2 right-2 bg-white/90 backdrop-blur px-2 py-1 rounded text-xs font-bold text-gray-700 shadow-sm">
                    ${item.category || 'General'}
                </div>
            </div>
            <div class="p-4 flex flex-col flex-grow">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="font-bold text-gray-800 text-lg leading-tight">${item.item_name}</h3>
                    <div class="flex items-center justify-center h-5 w-5 border ${item.veg_nonveg === 'Veg' ? 'border-green-600' : 'border-red-600'} rounded-[2px] p-[2px]">
                        <div class="h-2.5 w-2.5 rounded-full ${item.veg_nonveg === 'Veg' ? 'bg-green-600' : 'bg-red-600'}"></div>
                    </div>
                </div>
                <p class="text-gray-500 text-sm line-clamp-2 mb-4 flex-grow">${item.description || ''}</p>
                <div class="flex justify-between items-center mt-auto pt-3 border-t border-gray-50">
                    <span class="text-lg font-bold text-gray-900">₹${parseFloat(item.price).toFixed(2)}</span>
                    <button onclick="addToCart(${item.id})" class="bg-orange-50 text-orange-600 hover:bg-orange-600 hover:text-white px-4 py-2 rounded-lg font-semibold text-sm transition-colors duration-300">ADD</button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

// --- CART FUNCTIONS ---

window.addToCart = function(itemId) {
    const item = menuItems.find(i => i.id === itemId);
    if (!item) return;
    
    // Optional: Force login before adding to cart? 
    // Currently allowing guest cart but checkout will require details.
    
    const existing = cart.find(i => i.id === itemId);
    if (existing) {
        existing.quantity++;
    } else {
        cart.push({ ...item, quantity: 1 });
    }
    updateCartUI();
    saveCart();
    showToast(`${item.item_name} added to cart`);
};

window.updateQuantity = function(itemId, change) {
    const item = cart.find(i => i.id === itemId);
    if (!item) return;
    
    item.quantity += change;
    if (item.quantity <= 0) {
        cart = cart.filter(i => i.id !== itemId);
    }
    updateCartUI();
    saveCart();
};

function updateCartUI() {
    const countBadge = document.getElementById('cartCount');
    const totalQty = cart.reduce((sum, i) => sum + i.quantity, 0);
    
    // Update Badge
    if (countBadge) {
        countBadge.innerText = totalQty;
        countBadge.classList.toggle('hidden', totalQty === 0);
    }
    
    // Render Sidebar Items
    const container = document.getElementById('cart-page-items-container');
    if (!container) return;

    container.innerHTML = '';
    
    if (cart.length === 0) {
        container.innerHTML = `
            <div class="text-center py-10 opacity-60">
                <i data-lucide="shopping-bag" class="h-12 w-12 mx-auto mb-3 text-gray-300"></i>
                <p>Your cart is empty</p>
                <button onclick="toggleCart()" class="mt-4 text-orange-600 font-semibold text-sm">Browse Menu</button>
            </div>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    } else {
        cart.forEach(item => {
            const el = document.createElement('div');
            el.className = 'flex justify-between items-center bg-white p-3 rounded-lg border border-gray-100 shadow-sm';
            el.innerHTML = `
                <div>
                    <h4 class="font-medium text-gray-800 text-sm">${item.item_name}</h4>
                    <p class="text-xs text-gray-500">₹${item.price} x ${item.quantity}</p>
                </div>
                <div class="flex items-center gap-3 bg-gray-50 rounded-md px-2 py-1">
                    <button onclick="updateQuantity(${item.id}, -1)" class="text-gray-500 hover:text-orange-600">-</button>
                    <span class="text-sm font-semibold w-4 text-center">${item.quantity}</span>
                    <button onclick="updateQuantity(${item.id}, 1)" class="text-gray-500 hover:text-orange-600">+</button>
                </div>
            `;
            container.appendChild(el);
        });
    }
    
    // Update Summary
    const subtotal = cart.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    const summaryContainer = document.getElementById('cart-page-summary');
    if (summaryContainer) {
        summaryContainer.innerHTML = `
            <div class="flex justify-between"><span>Subtotal</span><span>₹${subtotal.toFixed(2)}</span></div>
            <div class="flex justify-between text-lg font-bold text-gray-900 mt-2 pt-2 border-t"><span>Total</span><span>₹${subtotal.toFixed(2)}</span></div>
        `;
    }
    
    // Pre-fill Checkout Form if user exists
    if (currentUser) {
        const nameInput = document.getElementById('checkout-name');
        const mobileInput = document.getElementById('checkout-mobile');
        const addrInput = document.getElementById('checkout-address');
        
        if (nameInput) nameInput.value = currentUser.name;
        if (mobileInput) mobileInput.value = currentUser.mobile;
        if (addrInput && !addrInput.value) addrInput.value = currentUser.address;
    }
}

// --- ORDER SUBMISSION ---

const checkoutForm = document.getElementById('checkoutForm');
if (checkoutForm) {
    checkoutForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!currentUser) {
            showToast('Please login to place an order', 'error');
            showAuthModal('login');
            return;
        }

        if (cart.length === 0) return showToast('Cart is empty', 'error');
        
        const btn = document.getElementById('payNowBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = 'Processing...';
        btn.disabled = true;
        
        const orderData = {
            name: currentUser.name,
            mobile: currentUser.mobile,
            email: currentUser.email, 
            address: document.getElementById('checkout-address').value,
            cart_items: cart.map(i => ({ id: i.id, quantity: i.quantity }))
        };
        
        try {
            const response = await fetch('/api/order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(orderData)
            });
            const result = await response.json();
            
            if (result.success) {
                cart = [];
                saveCart();
                updateCartUI();
                toggleCart();
                showToast('Order placed successfully! Check your email.', 'success');
            } else {
                showToast(result.error || 'Failed to place order', 'error');
            }
        } catch (error) {
            console.error(error);
            showToast('Network error', 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}

// --- UTILS ---

function setupEventListeners() {
    const cartBtn = document.getElementById('cartBtn');
    const closeCartBtn = document.getElementById('closeCartBtn');
    const cartOverlay = document.getElementById('cartOverlay');

    if (cartBtn) cartBtn.addEventListener('click', toggleCart);
    if (closeCartBtn) closeCartBtn.addEventListener('click', toggleCart);
    if (cartOverlay) cartOverlay.addEventListener('click', toggleCart);
    
    // Category filtering
    document.querySelectorAll('.category-filter').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.category-filter').forEach(b => {
                b.classList.remove('bg-orange-600', 'text-white', 'shadow-sm');
                b.classList.add('bg-white', 'text-gray-600', 'hover:border-orange-500');
            });
            e.target.classList.remove('bg-white', 'text-gray-600', 'hover:border-orange-500');
            e.target.classList.add('bg-orange-600', 'text-white', 'shadow-sm');
            
            const cat = e.target.dataset.category;
            if (cat === 'all') {
                renderMenu(menuItems);
            } else {
                const filtered = menuItems.filter(i => i.category === cat);
                renderMenu(filtered);
            }
        });
    });
}

function toggleCart() {
    const sidebar = document.getElementById('cartSidebar');
    const overlay = document.getElementById('cartOverlay');
    if (!sidebar || !overlay) return;

    const isOpen = !sidebar.classList.contains('translate-x-full');
    
    if (isOpen) {
        sidebar.classList.add('translate-x-full');
        overlay.classList.add('hidden');
        document.body.style.overflow = '';
    } else {
        sidebar.classList.remove('translate-x-full');
        overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        updateCartUI(); // Refresh UI when opening
    }
}

function saveCart() {
    localStorage.setItem('vanita_cart', JSON.stringify(cart));
}

function loadCartFromStorage() {
    const saved = localStorage.getItem('vanita_cart');
    if (saved) {
        try { cart = JSON.parse(saved); updateCartUI(); } catch(e) { cart = []; }
    }
}

function showToast(msg, type='success') {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-message');
    if (!toast || !toastMsg) return;

    toastMsg.innerText = msg;
    
    // Color logic
    const icon = toast.querySelector('i');
    if (icon) {
        if (type === 'error') {
            icon.classList.add('text-red-400');
            icon.classList.remove('text-orange-400', 'text-green-400');
        } else {
            icon.classList.add('text-green-400');
            icon.classList.remove('text-red-400', 'text-orange-400');
        }
    }
    
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

// Smooth scroll for landing page
window.scrollToSection = function(id) {
    showToast('Scroll to ' + id + ' (Placeholder)');
};
