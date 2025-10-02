document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize Lucide Icons if available
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // --- UTILITY: Get CSRF Token ---
    const getCookie = (name) => {
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
    };
//--------------------------------------------------------------------------------------------------------------------------

function showNewOrderPopup(orderData) {
    const modal = new bootstrap.Modal(document.getElementById('newOrderModal'));
    const detailsContainer = document.getElementById('newOrderDetails');
    
    // Parse the items if they are in a string format
    let items;
    try {
        items = JSON.parse(orderData.items);
    } catch (e) {
        items = orderData.items; // Assume it's already an object/array
    }

    let itemsHtml = '<ul>';
    for (const item of items) {
        itemsHtml += `<li>${item.quantity} x ${item.name}</li>`;
    }
    itemsHtml += '</ul>';

    detailsContainer.innerHTML = `
        <p><strong>Order ID:</strong> #${orderData.order_id}</p>
        <p><strong>Customer:</strong> ${orderData.customer_name}</p>
        <p><strong>Total:</strong> ₹${orderData.total_price}</p>
        <div><strong>Items:</strong>${itemsHtml}</div>
    `;

    // Add event listeners for accept/reject buttons
    const acceptBtn = document.getElementById('acceptOrderBtn');
    const rejectBtn = document.getElementById('rejectOrderBtn');

    acceptBtn.onclick = () => handleOrderAction(orderData.id, 'accept', modal);
    rejectBtn.onclick = () => handleOrderAction(orderData.id, 'reject', modal);

    modal.show();
}

async function handleOrderAction(orderId, action, modalInstance) {
    try {
        const response = await fetch('/api/handle-order-action/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ order_id: orderId, action: action })
        });

        if (response.ok) {
            modalInstance.hide();
            // Optionally, show a success message
            alert(`Order has been ${action}ed.`);
            // Refresh the page to update the order lists
            location.reload(); 
        } else {
            alert(`Failed to ${action} the order.`);
        }
    } catch (error) {
        console.error(`Error ${action}ing order:`, error);
        alert('An error occurred. Please try again.');
    }
}
    
//--------------------------------------------------------------------------------------------------------------------------

    
    
        // --- DASHBOARD: LIVE ORDER REFRESH ---
    const liveOrdersContainer = document.getElementById('live-orders');
    if (liveOrdersContainer) {
        const fetchOrders = async () => {
            try {
                const response = await fetch('/api/get_orders/');
                if (!response.ok) return;
                const data = await response.json();
                const ordersHtml = data.orders.map(order => {
                    const itemsSummary = order.items.length > 0 ? `${order.items.length} item(s): ${order.items[0].name}` : 'No items';
                    return `
                        <div class="live-order-item">
                            <p><b>#${order.order_id}</b> | ${itemsSummary} | <b>₹${order.total_price}</b></p>
                            <div class="status ${order.order_status}">${order.order_status}</div>
                        </div>`;
                }).join('');
                liveOrdersContainer.innerHTML = ordersHtml;
            } catch (error) {
                console.error("Error fetching live orders:", error);
            }
        };
        fetchOrders();
        setInterval(fetchOrders, 10000);
    }


    // --- ORDER MANAGEMENT PAGE ---
    const customDateBtn = document.getElementById('customDateBtn');
    const customDateRangeDiv = document.getElementById('customDateRange');

    if (customDateBtn && customDateRangeDiv) {
        customDateBtn.addEventListener('click', (e) => {
            e.preventDefault();
            customDateRangeDiv.classList.toggle('d-none');
        });
    }

    const handleStatusUpdate = async (button, newStatus) => {
        const orderCard = button.closest('.card[data-order-id]');
        
        if (!orderCard) {
            console.error('Could not find the parent order card element.');
            alert('An error occurred. Could not identify the order.');
            return;
        }
        
        const orderId = orderCard.dataset.orderId;
        if (!orderId) {
            console.error('Order ID is missing from the card element.');
            alert('An error occurred. Order ID is missing.');
            return;
        }

        try {
            const response = await fetch('/api/update-order-status/', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ id: orderId, status: newStatus })
            });

            if (response.ok) {
                orderCard.style.transition = 'opacity 0.5s ease';
                orderCard.style.opacity = '0';
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                alert('Error updating status. Please try again.');
            }
        } catch (error) {
            console.error('Failed to update order status:', error);
            alert('A network error occurred. Please check the console for details.');
        }
    };
    
    document.querySelectorAll('.mark-ready-btn').forEach(button => {
        button.addEventListener('click', (e) => handleStatusUpdate(e.target, 'ready'));
    });
    
    document.querySelectorAll('.mark-pickedup-btn').forEach(button => {
        button.addEventListener('click', (e) => handleStatusUpdate(e.target, 'pickedup'));
    });
});


// --- MENU MANAGEMENT PAGE ---
    const editSidebar = document.getElementById('editSidebar');
    const editFormContainer = document.getElementById('editForm');
    if (editSidebar) {
        document.querySelectorAll('.edit-btn').forEach(button => {
            button.addEventListener('click', async () => {
                const itemId = button.dataset.itemId;
                const response = await fetch(`/api/menu-item/${itemId}/`);
                const item = await response.json();

                editFormContainer.innerHTML = `
                    {% csrf_token %}
                    <div class="mb-3">
                        <label class="form-label">Item Name</label>
                        <input type="text" class="form-control" name="item_name" value="${item.item_name}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" name="description" rows="3">${item.description}</textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Price</label>
                        <input type="number" class="form-control" name="price" value="${item.price}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Category</label>
                        <input type="text" class="form-control" name="category" value="${item.category}">
                    </div>
                     <div class="mb-3">
                        <label class="form-label">Type</label>
                        <input type="text" class="form-control" name="veg_nonveg" value="${item.veg_nonveg}">
                    </div>
                     <div class="mb-3">
                        <label class="form-label">Meal Type</label>
                        <input type="text" class="form-control" name="meal_type" value="${item.meal_type}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Availability</label>
                        <input type="text" class="form-control" name="availability_time" value="${item.availability_time}">
                    </div>
                    <div class="sidebar-footer">
                        <button type="button" class="btn btn-secondary" id="cancelEditBtn">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                    </div>
                `;
                editFormContainer.action = `/api/menu-item/${item.id}/`;
                editSidebar.classList.add('open');
                document.getElementById('sidebar-overlay').classList.add('open');
            });
        });

        document.getElementById('closeEditBtn').addEventListener('click', () => {
            editSidebar.classList.remove('open');
            document.getElementById('sidebar-overlay').classList.remove('open');
        });
        
        document.getElementById('sidebar-overlay').addEventListener('click', () => {
            editSidebar.classList.remove('open');
            document.getElementById('sidebar-overlay').classList.remove('open');
        });

        editFormContainer.addEventListener('click', function(e) {
            if (e.target && e.target.id === 'cancelEditBtn') {
                editSidebar.classList.remove('open');
                document.getElementById('sidebar-overlay').classList.remove('open');
            }
        });

        editFormContainer.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(editFormContainer);
            const response = await fetch(editFormContainer.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Error saving item.');
            }
        });
    }
});





// Add this to your main.js or create a new file and include it in base.html

(function() {
    'use strict';

    // --- UTILITY: Get CSRF Token ---
    const getCookie = (name) => {
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
    };

    // --- PENDING ORDERS MANAGEMENT ---
    let pendingOrdersQueue = [];
    let currentPopupOrder = null;
    let isProcessing = false;

    // Load pending orders from localStorage on page load
    function loadPendingOrdersFromStorage() {
        try {
            const stored = localStorage.getItem('vlh_pending_orders');
            if (stored) {
                pendingOrdersQueue = JSON.parse(stored);
                console.log('Loaded pending orders from storage:', pendingOrdersQueue);
            }
        } catch (e) {
            console.error('Error loading pending orders:', e);
            pendingOrdersQueue = [];
        }
    }

    // Save pending orders to localStorage
    function savePendingOrdersToStorage() {
        try {
            localStorage.setItem('vlh_pending_orders', JSON.stringify(pendingOrdersQueue));
        } catch (e) {
            console.error('Error saving pending orders:', e);
        }
    }

    // Fetch pending orders from server
    async function fetchPendingOrders() {
        try {
            const response = await fetch('/api/pending-orders/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch pending orders');
            }

            const data = await response.json();
            
            if (data.success && data.orders && data.orders.length > 0) {
                // Get IDs of orders already in queue
                const existingIds = pendingOrdersQueue.map(o => o.id);
                
                // Add only new orders
                data.orders.forEach(order => {
                    if (!existingIds.includes(order.id)) {
                        pendingOrdersQueue.push(order);
                        console.log('New order added to queue:', order.order_id);
                    }
                });

                savePendingOrdersToStorage();
                showNextPopup();
            }
        } catch (error) {
            console.error('Error fetching pending orders:', error);
        }
    }

    // Show the next popup from queue
    function showNextPopup() {
        // Don't show if already processing or no orders in queue
        if (isProcessing || pendingOrdersQueue.length === 0 || currentPopupOrder !== null) {
            return;
        }

        // Get the first order from queue
        currentPopupOrder = pendingOrdersQueue[0];
        showOrderPopup(currentPopupOrder);
    }

    // Show order popup
    function showOrderPopup(orderData) {
        const modal = document.getElementById('newOrderModal');
        if (!modal) {
            console.error('Modal element not found');
            return;
        }

        const detailsContainer = document.getElementById('newOrderDetails');
        
        // Build items HTML
        let itemsHtml = '<ul class="list-unstyled mb-0">';
        orderData.items.forEach(item => {
            itemsHtml += `<li class="mb-1"><strong>${item.quantity}x</strong> ${item.name} - ₹${(item.price * item.quantity).toFixed(2)}</li>`;
        });
        itemsHtml += '</ul>';

        detailsContainer.innerHTML = `
            <div class="alert alert-info mb-3">
                <i class="fas fa-bell"></i> New order received!
            </div>
            <div class="row mb-3">
                <div class="col-md-6">
                    <p class="mb-1"><strong>Order ID:</strong></p>
                    <p class="text-primary">#${orderData.order_id}</p>
                </div>
                <div class="col-md-6">
                    <p class="mb-1"><strong>Time:</strong></p>
                    <p>${orderData.created_at}</p>
                </div>
            </div>
            <div class="mb-3">
                <p class="mb-1"><strong>Customer Name:</strong></p>
                <p>${orderData.customer_name}</p>
            </div>
            <div class="mb-3">
                <p class="mb-1"><strong>Mobile:</strong></p>
                <p>${orderData.customer_mobile}</p>
            </div>
            <div class="mb-3">
                <p class="mb-1"><strong>Items:</strong></p>
                ${itemsHtml}
            </div>
            <div class="alert alert-success mb-0">
                <strong>Total Amount: ₹${orderData.total_price.toFixed(2)}</strong>
            </div>
        `;

        // Show modal using Bootstrap
        const bsModal = new bootstrap.Modal(modal, {
            backdrop: 'static',  // Prevent closing by clicking outside
            keyboard: false      // Prevent closing with ESC key
        });
        bsModal.show();

        // Set up button handlers
        setupPopupButtons(orderData.id, bsModal);
    }

    // Setup popup button handlers
    function setupPopupButtons(orderId, bsModal) {
        const acceptBtn = document.getElementById('acceptOrderBtn');
        const rejectBtn = document.getElementById('rejectOrderBtn');

        // Remove old event listeners by cloning
        const newAcceptBtn = acceptBtn.cloneNode(true);
        const newRejectBtn = rejectBtn.cloneNode(true);
        acceptBtn.parentNode.replaceChild(newAcceptBtn, acceptBtn);
        rejectBtn.parentNode.replaceChild(newRejectBtn, rejectBtn);

        // Add new event listeners
        newAcceptBtn.addEventListener('click', () => handleOrderAction(orderId, 'accept', bsModal));
        newRejectBtn.addEventListener('click', () => handleOrderAction(orderId, 'reject', bsModal));
    }

    // Handle order action (accept/reject)
    async function handleOrderAction(orderId, action, bsModal) {
        if (isProcessing) return;
        isProcessing = true;

        // Disable buttons
        const acceptBtn = document.getElementById('acceptOrderBtn');
        const rejectBtn = document.getElementById('rejectOrderBtn');
        acceptBtn.disabled = true;
        rejectBtn.disabled = true;
        acceptBtn.textContent = 'Processing...';
        rejectBtn.textContent = 'Processing...';

        try {
            const response = await fetch('/api/handle-order-action/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ 
                    order_id: orderId, 
                    action: action 
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Remove order from queue
                pendingOrdersQueue = pendingOrdersQueue.filter(o => o.id !== orderId);
                savePendingOrdersToStorage();
                currentPopupOrder = null;

                // Hide modal
                bsModal.hide();

                // Show success message
                showToast(result.message || `Order ${action}ed successfully!`, 'success');

                // Show next popup after a short delay
                setTimeout(() => {
                    isProcessing = false;
                    showNextPopup();
                }, 500);

                // Refresh the page to update order lists
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                throw new Error(result.error || 'Failed to process order');
            }
        } catch (error) {
            console.error(`Error ${action}ing order:`, error);
            showToast(error.message || 'An error occurred. Please try again.', 'error');
            
            // Re-enable buttons
            acceptBtn.disabled = false;
            rejectBtn.disabled = false;
            acceptBtn.textContent = 'Accept';
            rejectBtn.textContent = 'Reject';
            isProcessing = false;
        }
    }

    // Show toast notification
    function showToast(message, type = 'success') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0 position-fixed bottom-0 end-0 m-3" role="alert" aria-live="assertive" aria-atomic="true" style="z-index: 9999;">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.body.lastElementChild;
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // Initialize on page load
    function init() {
        console.log('Initializing pending orders system...');
        
        // Load pending orders from storage
        loadPendingOrdersFromStorage();
        
        // Show popup if there are pending orders
        showNextPopup();
        
        // Fetch new pending orders from server
        fetchPendingOrders();
        
        // Poll for new orders every 10 seconds
        setInterval(fetchPendingOrders, 10000);
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Handle Firebase notifications
    window.handleNewOrderNotification = function(orderData) {
        console.log('Received new order notification:', orderData);
        
        // Add to queue if not already there
        const exists = pendingOrdersQueue.some(o => o.id === orderData.id);
        if (!exists) {
            pendingOrdersQueue.push(orderData);
            savePendingOrdersToStorage();
            showNextPopup();
        }
    };

})();

