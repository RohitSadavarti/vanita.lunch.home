// =================================================================================
// APPLICATION STATE & INITIALIZATION
// =================================================================================

// Global state variables
let cart = [];
let menuItems = [];
let filteredMenuItems = [];
let currentCategory = 'all';
let currentVegFilter = 'all';
let currentSearchTerm = '';

// Initialize the application once the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons(); // Initialize icons
    loadMenu();
    setupEventListeners();
});

// =================================================================================
// EVENT LISTENERS
// =================================================================================

// Centralized function to set up all event listeners
function setupEventListeners() {
    // Page navigation
    document.getElementById('cartBtn').addEventListener('click', showCartPage);
    document.getElementById('backToMenuBtn').addEventListener('click', showHomePage);

    // Cart actions
    document.getElementById('payNowBtn').addEventListener('click', processOrder);

    // Menu filtering and searching
    document.getElementById('searchInput').addEventListener('input', handleSearch);
    document.querySelectorAll('.category-filter').forEach(button => {
        button.addEventListener('click', handleCategoryFilter);
    });
    document.querySelectorAll('.veg-filter').forEach(button => {
        button.addEventListener('click', handleVegFilter);
    });
}

// =================================================================================
// API & DATA HANDLING
// =================================================================================

// Load menu items from the backend API
async function loadMenu() {
    try {
        const response = await fetch('/api/menu');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        menuItems = await response.json();
        filteredMenuItems = [...menuItems];
        renderMenu();
    } catch (error) {
        console.error('Error loading menu:', error);
        showToast('Failed to load menu. Please refresh the page.', 'error');
    }
}

// =================================================================================
// UI RENDERING & PAGE NAVIGATION
// =================================================================================

// Show the main menu page
function showHomePage() {
    document.getElementById('cartView').classList.add('hidden');
    document.getElementById('homeView').classList.remove('hidden');
}

// Show the cart page
function showCartPage() {
    if (cart.length === 0) {
        showToast('Your cart is empty!', 'info');
        return;
    }
    document.getElementById('homeView').classList.add('hidden');
    document.getElementById('cartView').classList.remove('hidden');
    renderCartPage();
}

// Render the filtered menu items on the page
function renderMenu() {
    const menuContainer = document.getElementById('menu-container');
    menuContainer.innerHTML = ''; // Clear previous items

    if (filteredMenuItems.length === 0) {
        menuContainer.innerHTML = `
            <div class="col-span-full text-center py-12">
                <i data-lucide="search-x" class="mx-auto h-12 w-12 text-gray-400 mb-4"></i>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No items found</h3>
                <p class="text-gray-500">Try adjusting your search or filters.</p>
            </div>`;
    } else {
        filteredMenuItems.forEach(item => {
            const menuCard = createMenuCard(item);
            menuContainer.appendChild(menuCard);
        });
    }

    lucide.createIcons(); // Re-render icons for new elements
}

// vanitalunchhome/static/script.js

// ... (keep all the existing code before this function)

// Create a single menu card element
function createMenuCard(item) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 flex flex-col';

    const vegType = (item.veg_nonveg || '').toLowerCase() === 'veg' ? 'veg' : 'non-veg';
    const vegIndicatorClass = vegType === 'veg' ? 'bg-green-500' : 'bg-red-500';
    const imageUrl = item.image || `https://placehold.co/300x200/f3f4f6/6b7280?text=${encodeURIComponent(item.item_name || 'Food')}`;

    card.innerHTML = `
        <div class="relative">
            <img src="${imageUrl}"
                 alt="${escapeHtml(item.item_name)}"
                 class="w-full h-48 object-cover">
            <div class="absolute top-2 left-2 flex items-center space-x-1 bg-white px-2 py-1 rounded-full text-xs font-medium">
                <span class="w-3 h-3 ${vegIndicatorClass} rounded-sm"></span>
                <span>${vegType.toUpperCase()}</span>
            </div>
        </div>
        <div class="p-4 flex flex-col flex-grow">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">${escapeHtml(item.item_name)}</h3>
            <p class="text-gray-600 text-sm mb-3 line-clamp-2 flex-grow">${escapeHtml(item.description || 'Delicious food item')}</p>
            
            <div class="flex items-center justify-between mt-auto pt-4">
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

// ... (keep all the existing code after this function)
// Render the contents of the cart page
function renderCartPage() {
    const cartItemsContainer = document.getElementById('cart-page-items');
    const cartSummaryContainer = document.getElementById('cart-page-summary');
    cartItemsContainer.innerHTML = '';

    if (cart.length === 0) {
        showHomePage(); // If cart becomes empty, go back to menu
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
            </div>`;
        cartItemsContainer.appendChild(cartItem);
    });

    // Render cart summary using the centralized calculation function
    const { subtotal, deliveryFee, total } = calculateTotals();
    cartSummaryContainer.innerHTML = `
        <div class="flex justify-between">
            <span>Subtotal</span>
            <span>₹${subtotal.toFixed(2)}</span>
        </div>
        <div class="flex justify-between">
            <span>Delivery Fee</span>
            <span>${deliveryFee === 0 ? 'FREE' : '₹' + deliveryFee.toFixed(2)}</span>
        </div>
        <div class="flex justify-between font-semibold text-lg border-t pt-3 mt-3">
            <span>Total</span>
            <span>₹${total.toFixed(2)}</span>
        </div>
        ${subtotal < 300 ? `<p class="text-sm text-gray-500 mt-2">Add ₹${(300 - subtotal).toFixed(2)} more for free delivery!</p>` : ''}`;

    lucide.createIcons(); // Re-render icons
}


// =================================================================================
// MENU FILTERING & SEARCH
// =================================================================================

// Apply all active filters and re-render the menu
function applyFilters() {
    filteredMenuItems = menuItems.filter(item => {
        const categoryMatch = currentCategory === 'all' || item.category === currentCategory;
        const vegMatch = currentVegFilter === 'all' || item.veg_nonveg === currentVegFilter;
        const searchMatch = !currentSearchTerm ||
            item.item_name.toLowerCase().includes(currentSearchTerm) ||
            item.description.toLowerCase().includes(currentSearchTerm);
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
        btn.classList.remove('bg-orange-500', 'text-white');
        btn.classList.add('bg-gray-200', 'text-gray-700');
    });
    e.currentTarget.classList.add('bg-orange-500', 'text-white');
    e.currentTarget.classList.remove('bg-gray-200', 'text-gray-700');
    currentCategory = e.currentTarget.getAttribute('data-category');
    applyFilters();
}

function handleVegFilter(e) {
    document.querySelectorAll('.veg-filter').forEach(btn => btn.classList.remove('active'));
    e.currentTarget.classList.add('active');
    currentVegFilter = e.currentTarget.getAttribute('data-type');
    applyFilters();
}

// =================================================================================
// CART LOGIC
// =================================================================================

// Add an item to the cart
function addToCart(itemId) {
    const item = menuItems.find(i => i.id === itemId);
    if (!item) return;

    const existingItem = cart.find(i => i.id === itemId);
    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({ id: item.id, name: item.item_name, price: item.price, quantity: 1 });
    }

    updateCartCount();
    showToast(`${item.item_name} added to cart!`);
}

// Remove an item completely from the cart
function removeFromCart(itemId) {
    const item = cart.find(i => i.id === itemId);
    cart = cart.filter(i => i.id !== itemId);
    updateCartCount();
    if (document.getElementById('cartView').classList.contains('hidden') === false) {
        renderCartPage();
    }
    showToast(`${item.name} removed from cart.`, 'info');
}

// Update the quantity of a cart item
function updateQuantity(itemId, change) {
    const item = cart.find(i => i.id === itemId);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            removeFromCart(itemId); // Automatically remove if quantity is 0 or less
        } else {
            updateCartCount();
            if (document.getElementById('cartView').classList.contains('hidden') === false) {
                renderCartPage();
            }
        }
    }
}

// Update the cart item count bubble in the header
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

// Centralized function to calculate cart totals
function calculateTotals() {
    const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
    const deliveryFee = subtotal >= 300 ? 0 : 40; // Free delivery for orders >= 300
    const total = subtotal + deliveryFee;
    return { subtotal, deliveryFee, total };
}

// =================================================================================
// ORDER PROCESSING (CASH ON DELIVERY)
// =================================================================================

// 1. Validate form and start the order process
async function processOrder() {
    const name = document.getElementById('customerNameCart').value.trim();
    const mobile = document.getElementById('customerMobileCart').value.trim();
    const address = document.getElementById('customerAddress').value.trim();

    // --- Validation ---
    if (!name || !mobile || !address) {
        showToast('Please fill in all delivery details.', 'error');
        return;
    }
    if (!/^[0-9]{10}$/.test(mobile)) {
        showToast('Please enter a valid 10-digit mobile number.', 'error');
        return;
    }

    // --- Create a dummy payment response for Cash on Delivery ---
    const dummyPaymentResponse = {
        razorpay_payment_id: `cod_${new Date().getTime()}` // Unique ID for COD orders
    };

    const { total } = calculateTotals();

    const customerDetails = {
        name: name,
        mobile: mobile,
        address: address,
        amount: total
    };

    // 2. Proceed to place the order on the backend
    await placeOrderOnBackend(dummyPaymentResponse, customerDetails);
}

// vanitalunchhome/static/script.js

// ... (keep all the existing code before this function)


// 2. Send the final order data to the backend API
async function placeOrderOnBackend(paymentResponse, customerDetails) {
    // This object structure MUST match what the Flask backend (app.py) expects
    const orderData = {
        name: customerDetails.name,                 // Correct key: 'name'
        mobile: customerDetails.mobile,               // Correct key: 'mobile'
        address: customerDetails.address,             // Correct key: 'address'
        cart_items: cart,                           // Correct key: 'cart_items'
        payment_id: paymentResponse.razorpay_payment_id,
        amount: customerDetails.amount              // The original code sent this
    };

    try {
        // The API endpoint is /api/order as defined in your app.py
        const apiResponse = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });

        if (!apiResponse.ok) {
            const errorData = await apiResponse.json();
            throw new Error(errorData.error || 'Failed to place order on the server.');
        }

        const result = await apiResponse.json();

        if (result.success) {
            showToast('Order placed successfully! You will receive a confirmation call shortly.');
            // Reset state and UI after successful order
            cart = [];
            updateCartCount();
            showHomePage();
            document.getElementById('customerDetailsForm').reset();
        } else {
            throw new Error(result.message || 'An unknown error occurred.');
        }
    } catch (error) {
        console.error('Error placing order:', error);
        showToast(`Error: ${error.message}`, 'error');
    }
}


// ... (keep all the existing code after this function)

// =================================================================================
// UTILITY FUNCTIONS
// =================================================================================

// Display a toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    if (!toast || !toastMessage) return;

    toastMessage.textContent = message;

    // Reset classes
    toast.className = 'fixed bottom-5 right-5 px-6 py-3 rounded-lg shadow-lg animate-pop';

    if (type === 'error') {
        toast.classList.add('bg-red-500', 'text-white');
    } else if (type === 'info') {
        toast.classList.add('bg-blue-500', 'text-white');
    } else {
        toast.classList.add('bg-green-500', 'text-white');
    }

    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4000);
}

// Sanitize text to prevent XSS attacks
function escapeHtml(text) {
    if (text === null || typeof text === 'undefined') {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
