// OrderMaster/static/js/persistent-popup.js

(function() {
    'use strict';

    let pendingOrdersQueue = [];
    let isPopupVisible = false;

    // Make this function globally available so firebase-init.js can call it
    window.handleNewOrderNotification = function(orderData) {
        console.log('🔔 New order notification handler called:', orderData);
        
        // Add the order to the queue
        pendingOrdersQueue.push(orderData);
        console.log('📋 Orders in queue:', pendingOrdersQueue.length);
        
        // If no popup is currently showing, show the next one
        if (!isPopupVisible) {
            showNextOrderPopup();
        }
    };

    function showNextOrderPopup() {
        if (pendingOrdersQueue.length === 0) {
            isPopupVisible = false;
            console.log('✅ All orders processed');
            return;
        }

        isPopupVisible = true;
        const orderData = pendingOrdersQueue[0]; // Get the first order in the queue
        console.log('📤 Displaying order popup:', orderData.order_id);
        displayPopup(orderData);
    }

    function displayPopup(orderData) {
        const modalElement = document.getElementById('newOrderModal');
        if (!modalElement) {
            console.error('❌ Modal element not found');
            return;
        }

        const modal = new bootstrap.Modal(modalElement, {
            backdrop: 'static',
            keyboard: false
        });

        const detailsContainer = document.getElementById('newOrderDetails');
        
        // Parse items if they're a string
        let items;
        try {
            items = typeof orderData.items === 'string' ? 
                    JSON.parse(orderData.items) : orderData.items;
        } catch (e) {
            console.error('❌ Error parsing items:', e);
            items = [];
        }

        let itemsHtml = '<ul class="list-unstyled">';
        items.forEach(item => {
            itemsHtml += `<li>✓ ${item.quantity} x ${item.name}</li>`;
        });
        itemsHtml += '</ul>';

        detailsContainer.innerHTML = `
            <p><strong>Order ID:</strong> #${orderData.order_id}</p>
            <p><strong>Customer:</strong> ${orderData.customer_name}</p>
            <p><strong>Total:</strong> ₹${orderData.total_price}</p>
            <div><strong>Items:</strong>${itemsHtml}</div>
        `;

        // Setup button listeners
        const acceptBtn = document.getElementById('acceptOrderBtn');
        const rejectBtn = document.getElementById('rejectOrderBtn');

        if (acceptBtn && rejectBtn) {
            // Use .onclick to easily replace the listener for each new order
            acceptBtn.onclick = () => handleOrderAction(orderData.id, 'accept', modal);
            rejectBtn.onclick = () => handleOrderAction(orderData.id, 'reject', modal);
        } else {
            console.error('❌ Accept/Reject buttons not found');
        }

        modal.show();
    }

    async function handleOrderAction(orderId, action, modal) {
        console.log(`⚡ Handling order action: ${action} for order ${orderId}`);
        
        // Disable buttons to prevent double-clicking
        const acceptBtn = document.getElementById('acceptOrderBtn');
        const rejectBtn = document.getElementById('rejectOrderBtn');
        acceptBtn.disabled = true;
        rejectBtn.disabled = true;

        try {
            const response = await fetch('/api/handle-order-action/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ order_id: orderId, action: action })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                console.log(`✅ Order ${action}ed successfully`);
                modal.hide();
                pendingOrdersQueue.shift(); // Remove the processed order from the queue
                
                // Show success notification
                if (window.Notification && Notification.permission === 'granted') {
                    new Notification(`Order ${action}ed`, {
                        body: `Order #${data.order_id} has been ${action}ed`,
                        icon: '/static/favicon.ico'
                    });
                }
                
                // Wait a moment before showing next order
                setTimeout(() => {
                    showNextOrderPopup(); // Show the next order, if any
                }, 500);
                
                // Reload after a delay to update order lists
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                console.error(`❌ Failed to ${action} order:`, data.error);
                alert(`Failed to ${action} the order: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('❌ Error handling order action:', error);
            alert('An error occurred. Please try again.');
        } finally {
            // Re-enable buttons in case of an error
            acceptBtn.disabled = false;
            rejectBtn.disabled = false;
        }
    }

    // Helper function to get CSRF token
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

    console.log('✅ Persistent popup script loaded');

})();
