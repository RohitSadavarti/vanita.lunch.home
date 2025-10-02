// OrderMaster/static/js/persistent-popup.js

(function() {
    'use strict';

    const STORAGE_KEY = 'pendingOrdersQueue';
    let isPopupVisible = false;

    // --- Function to load pending orders from localStorage ---
    function loadPendingOrders() {
        try {
            const storedOrders = localStorage.getItem(STORAGE_KEY);
            return storedOrders ? JSON.parse(storedOrders) : [];
        } catch (e) {
            console.error("Failed to parse pending orders:", e);
            return [];
        }
    }

    // --- Function to save pending orders to localStorage ---
    function savePendingOrders(orders) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(orders));
    }

    // This function is called by firebase-init.js when a message is received
    window.handleNewOrderNotification = function(orderData) {
        console.log("handleNewOrderNotification called with:", orderData);
        let pendingOrders = loadPendingOrders();
        
        // Avoid adding duplicate orders
        const isDuplicate = pendingOrders.some(order => order.id === orderData.id);
        if (!isDuplicate) {
            pendingOrders.push(orderData);
            savePendingOrders(pendingOrders);
        }
        
        if (!isPopupVisible) {
            showNextOrderPopup();
        }
    };

    function showNextOrderPopup() {
        const pendingOrders = loadPendingOrders();
        if (pendingOrders.length === 0) {
            isPopupVisible = false;
            const modalElement = document.getElementById('newOrderModal');
            if (modalElement) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
            }
            return;
        }

        isPopupVisible = true;
        const orderData = pendingOrders[0]; // Get the first order
        displayPopup(orderData);
    }

    function displayPopup(orderData) {
        const modalElement = document.getElementById('newOrderModal');
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: 'static', // Prevents closing on backdrop click
            keyboard: false     // Prevents closing with the escape key
        });

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

        const acceptBtn = document.getElementById('acceptOrderBtn');
        const rejectBtn = document.getElementById('rejectOrderBtn');

        // Use .onclick to easily replace the listener for each new order
        acceptBtn.onclick = () => handleOrderAction(orderData.id, 'accept');
        rejectBtn.onclick = () => handleOrderAction(orderData.id, 'reject');

        modal.show();
    }

    async function handleOrderAction(orderId, action) {
        document.getElementById('acceptOrderBtn').disabled = true;
        document.getElementById('rejectOrderBtn').disabled = true;

        try {
            const response = await fetch('/api/handle-order-action/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ order_id: orderId, action: action })
            });

            if (response.ok) {
                let pendingOrders = loadPendingOrders();
                // Remove the processed order from the queue
                const updatedOrders = pendingOrders.filter(order => order.id !== orderId);
                savePendingOrders(updatedOrders);
                
                isPopupVisible = false;
                showNextOrderPopup(); // Show the next order, if any
                
                // Optionally reload the main page content
                if (window.location.pathname.includes('/orders/')) {
                    location.reload();
                }
                
            } else {
                alert(`Failed to ${action} the order.`);
            }
        } catch (error) {
            console.error('Error handling order action:', error);
            alert('An error occurred. Please try again.');
        } finally {
            document.getElementById('acceptOrderBtn').disabled = false;
            document.getElementById('rejectOrderBtn').disabled = false;
        }
    }

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

    // --- On page load, always check if there are pending orders ---
    document.addEventListener('DOMContentLoaded', () => {
        showNextOrderPopup();
    });

})();
