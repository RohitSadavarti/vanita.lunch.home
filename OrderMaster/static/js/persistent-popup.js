// OrderMaster/static/js/persistent-popup.js

(function() {
    'use strict';

    let pendingOrdersQueue = [];
    let isPopupVisible = false;

    // --- Listen for foreground messages ---
messaging.onMessage((payload) => {
    console.log('Foreground message received: ', payload);
    if (window.handleNewOrderNotification) {
        // The message data is inside payload.data
        window.handleNewOrderNotification(payload.data);
    }
});

    function showNextOrderPopup() {
        if (pendingOrdersQueue.length === 0) {
            isPopupVisible = false;
            return;
        }

        isPopupVisible = true;
        const orderData = pendingOrdersQueue[0]; // Get the first order in the queue
        displayPopup(orderData);
    }

    function displayPopup(orderData) {
        const modalElement = document.getElementById('newOrderModal');
        const modal = new bootstrap.Modal(modalElement);

        const detailsContainer = document.getElementById('newOrderDetails');
        const items = JSON.parse(orderData.items);
        let itemsHtml = '<ul>';
        items.forEach(item => {
            itemsHtml += `<li>${item.quantity} x ${item.name}</li>`;
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

        // Use .onclick to easily replace the listener for each new order
        acceptBtn.onclick = () => handleOrderAction(orderData.id, 'accept', modal);
        rejectBtn.onclick = () => handleOrderAction(orderData.id, 'reject', modal);

        modal.show();
    }

    async function handleOrderAction(orderId, action, modal) {
        // Disable buttons to prevent double-clicking
        document.getElementById('acceptOrderBtn').disabled = true;
        document.getElementById('rejectOrderBtn').disabled = true;

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
                // Order action was successful
                modal.hide();
                pendingOrdersQueue.shift(); // Remove the processed order from the queue
                showNextOrderPopup(); // Show the next order, if any
                location.reload(); // Reload to update order lists on the page
            } else {
                alert(`Failed to ${action} the order.`);
            }
        } catch (error) {
            console.error('Error handling order action:', error);
            alert('An error occurred. Please try again.');
        } finally {
            // Re-enable buttons in case of an error
            document.getElementById('acceptOrderBtn').disabled = false;
            document.getElementById('rejectOrderBtn').disabled = false;
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

})();
