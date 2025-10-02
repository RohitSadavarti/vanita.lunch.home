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
