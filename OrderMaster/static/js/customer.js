// static/js/customer.js

document.addEventListener('DOMContentLoaded', function () {
    const API_URL = '/api/menu-items/';
    const PLACE_ORDER_URL = '/api/place-order/';

    const menuContainer = document.getElementById('menu-container');
    const cartButton = document.getElementById('cart-button');
    const cartCountBadge = document.getElementById('cart-count-badge');
    const cartSidebar = document.getElementById('cart-sidebar');
    const cartOverlay = document.getElementById('cart-overlay');
    const closeCartBtn = document.getElementById('close-cart-btn');
    const cartItemsContainer = document.getElementById('cart-items-container');
    const cartSummaryContainer = document.getElementById('cart-summary-container');
    const checkoutBtn = document.getElementById('checkout-btn');
    const checkoutFormContainer = document.getElementById('checkout-form-container');
    const customerDetailsForm = document.getElementById('customer-details-form');

    let menuItems = [];
    let cart = [];

    // --- UTILITY FUNCTIONS ---
    const formatCurrency = (amount) => `₹${Number(amount).toFixed(2)}`;
    const updateCartCount = () => {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        cartCountBadge.textContent = totalItems;
        cartCountBadge.style.display = totalItems > 0 ? 'block' : 'none';
    };

    // --- CART VISIBILITY ---
    const showCart = () => cartSidebar.classList.add('is-open');
    const hideCart = () => cartSidebar.classList.remove('is-open');

    // --- CART LOGIC ---
    const addToCart = (itemId) => {
        const item = menuItems.find(i => i.id === itemId);
        if (!item) return;

        const cartItem = cart.find(i => i.id === itemId);
        if (cartItem) {
            cartItem.quantity++;
        } else {
            cart.push({ ...item, quantity: 1 });
        }
        updateCart();
    };

    const removeFromCart = (itemId) => {
        const itemIndex = cart.findIndex(i => i.id === itemId);
        if (itemIndex > -1) {
            cart.splice(itemIndex, 1);
            updateCart();
        }
    };

    const updateQuantity = (itemId, newQuantity) => {
        const cartItem = cart.find(i => i.id === itemId);
        if (cartItem) {
            cartItem.quantity = newQuantity;
            if (cartItem.quantity <= 0) {
                removeFromCart(itemId);
            } else {
                updateCart();
            }
        }
    };

    // --- RENDERING ---
    const renderMenu = (items) => {
        const groupedItems = items.reduce((acc, item) => {
            (acc[item.category] = acc[item.category] || []).push(item);
            return acc;
        }, {});

        menuContainer.innerHTML = Object.entries(groupedItems).map(([category, items]) => `
            <section class="menu-category">
                <h2 class="category-title">${category}</h2>
                <div class="menu-items-grid">
                    ${items.map(item => `
                        <div class="menu-item-card">
                            <div class="item-details">
                                <h3 class="item-name">${item.item_name}</h3>
                                <p class="item-description">${item.description || ''}</p>
                                <p class="item-price">${formatCurrency(item.price)}</p>
                            </div>
                            <div class="item-action">
                                <button class="btn-add-to-cart" data-item-id="${item.id}">Add</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </section>
        `).join('');
    };

    const renderCart = () => {
        if (cart.length === 0) {
            cartItemsContainer.innerHTML = '<p class="text-center text-muted">Your cart is empty.</p>';
            cartSummaryContainer.innerHTML = '';
            checkoutBtn.style.display = 'none';
            checkoutFormContainer.style.display = 'none';
            return;
        }

        checkoutBtn.style.display = 'block';
        cartItemsContainer.innerHTML = cart.map(item => `
            <div class="cart-item">
                <div class="item-info">
                    <p class="item-name m-0">${item.item_name}</p>
                    <p class="item-price text-muted m-0">${formatCurrency(item.price)}</p>
                </div>
                <div class="item-controls">
                    <input type="number" class="form-control item-quantity" value="${item.quantity}" min="1" data-item-id="${item.id}">
                    <button class="btn btn-sm btn-outline-danger btn-remove-item" data-item-id="${item.id}">&times;</button>
                </div>
            </div>
        `).join('');

        const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        cartSummaryContainer.innerHTML = `
            <div class="d-flex justify-content-between">
                <span>Subtotal</span>
                <strong>${formatCurrency(subtotal)}</strong>
            </div>
        `;
    };

    const updateCart = () => {
        renderCart();
        updateCartCount();
    };

    // --- API CALLS ---
    const fetchMenu = async () => {
        try {
            const response = await fetch(API_URL);
            if (!response.ok) throw new Error('Network response was not ok');
            menuItems = await response.json();
            renderMenu(menuItems);
        } catch (error) {
            console.error('Failed to fetch menu:', error);
            menuContainer.innerHTML = '<p class="text-center text-danger">Could not load menu. Please try again later.</p>';
        }
    };

    const placeOrder = async (orderDetails) => {
    try {
        // Calculate totals
        const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const deliveryFee = subtotal >= 300 ? 0 : 40;
        const totalPrice = subtotal + deliveryFee;

        // Prepare order data with correct field names
        const orderData = {
            customer_name: orderDetails.customerName,
            customer_mobile: orderDetails.customerMobile,
            customer_address: orderDetails.customerAddress || 'N/A',
            items: cart.map(item => ({
                id: item.id,
                name: item.item_name,
                price: item.price,
                quantity: item.quantity
            })),
            total_price: totalPrice.toFixed(2),
            payment_id: 'COD'
        };

        const response = await fetch(PLACE_ORDER_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });

        const result = await response.json();

        if (result.success) {
            alert(`Order placed successfully! Your Order ID is: ${result.order_id}`);
            cart = [];
            updateCart();
            hideCart();
            customerDetailsForm.reset();
            checkoutFormContainer.style.display = 'none';
        } else {
            throw new Error(result.error || 'Failed to place order.');
        }
    } catch (error) {
        console.error('Order placement failed:', error);
        alert(`Error: ${error.message}`);
    }
};
    // --- EVENT LISTENERS ---
    cartButton.addEventListener('click', showCart);
    closeCartBtn.addEventListener('click', hideCart);
    cartOverlay.addEventListener('click', hideCart);

    menuContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-add-to-cart')) {
            const itemId = parseInt(e.target.dataset.itemId, 10);
            addToCart(itemId);
        }
    });

    cartItemsContainer.addEventListener('change', (e) => {
        if (e.target.classList.contains('item-quantity')) {
            const itemId = parseInt(e.target.dataset.itemId, 10);
            const newQuantity = parseInt(e.target.value, 10);
            updateQuantity(itemId, newQuantity);
        }
    });
    
    cartItemsContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-remove-item')) {
            const itemId = parseInt(e.target.dataset.itemId, 10);
            removeFromCart(itemId);
        }
    });

    checkoutBtn.addEventListener('click', () => {
        checkoutFormContainer.style.display = 'block';
        checkoutBtn.style.display = 'none';
    });

    customerDetailsForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const orderDetails = {
        customerName: document.getElementById('customer-name').value,
        customerMobile: document.getElementById('customer-mobile').value,
        customerAddress: document.getElementById('customer-address').value
    };
    placeOrder(orderDetails);
});
    // --- INITIALIZATION ---
    fetchMenu();
});

