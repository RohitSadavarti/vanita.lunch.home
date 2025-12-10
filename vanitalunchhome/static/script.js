$(document).ready(function() {
    let currentOrders = { preparing: [], ready: [] };
    let newOrderSound = new Audio('/static/notification.mp3'); // Path to your sound file
    let newOrdersQueue = [];
    let isModalOpen = false;

    // --- UTILITY: Get CSRF Token ---
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

    // --- NOTIFICATION MODAL ---
    function showNewOrderPopup() {
        if (isModalOpen || newOrdersQueue.length === 0) {
            return; // Don't show if modal is already open or queue is empty
        }
        
        isModalOpen = true;
        const orderData = newOrdersQueue.shift(); // Get the first order from the queue
        
        const modal = new bootstrap.Modal(document.getElementById('newOrderModal'));
        const detailsContainer = document.getElementById('newOrderDetails');
        
        let items;
        try {
            // Check if items is a JSON string, otherwise assume it's an object
            items = typeof orderData.items === 'string' ? JSON.parse(orderData.items) : orderData.items;
        } catch (e) {
            items = []; // Fallback
        }

        let itemsHtml = '<ul class="list-group list-group-flush">';
        if (Array.isArray(items)) {
             items.forEach(item => {
                itemsHtml += `<li class="list-group-item d-flex justify-content-between">
                                <span>${item.quantity} x ${item.name}</span>
                                <strong>₹${item.price}</strong>
                              </li>`;
            });
        } else if (typeof items === 'object' && items !== null) {
             // Handle object format {item_name: quantity}
            for (const [name, qty] of Object.entries(items)) {
                itemsHtml += `<li class="list-group-item">${qty} x ${name}</li>`;
            }
        }
        itemsHtml += '</ul>';

        detailsContainer.innerHTML = `
            <h4 class="mb-3">Order #${orderData.order_id}</h4>
            <p><strong>Customer:</strong> ${orderData.customer_name}</p>
            <p><strong>Total:</strong> <strong class="text-danger fs-5">₹${orderData.total_price}</strong></p>
            <div><strong>Items:</strong>${itemsHtml}</div>
        `;

        // Add event listeners for accept/reject buttons
        $('#acceptOrderBtn').off('click').on('click', () => handleOrderAction(orderData.id, 'accept', modal));
        $('#rejectOrderBtn').off('click').on('click', () => handleOrderAction(orderData.id, 'reject', modal));
        
        // When modal is hidden, check queue for next order
        $('#newOrderModal').off('hidden.bs.modal').on('hidden.bs.modal', function () {
            isModalOpen = false;
            setTimeout(showNewOrderPopup, 500); // Check for next order
        });

        modal.show();
        newOrderSound.play().catch(e => console.warn("Audio play failed:", e));
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
                fetchOrders(); // Manually refresh the board
            } else {
                alert(`Failed to ${action} the order.`);
            }
        } catch (error) {
            console.error(`Error ${action}ing order:`, error);
            alert('An error occurred. Please try again.');
        }
    }


    // --- KANBAN BOARD LOGIC ---
    function fetchOrders() {
        $.ajax({
            url: '/api/get-orders',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                const preparingList = $('#preparing-orders-list');
                const readyList = $('#ready-orders-list');

                // Check for new orders to show popup
                const newPreparingOrders = data.preparing_orders.filter(order => 
                    !currentOrders.preparing.some(o => o.id === order.id)
                );
                
                if (newPreparingOrders.length > 0) {
                    newOrdersQueue.push(...newPreparingOrders);
                    showNewOrderPopup(); // Try to show popup
                }
                
                // Update current orders
                currentOrders.preparing = data.preparing_orders;
                currentOrders.ready = data.ready_orders;

                // --- Render Preparing Orders ---
                preparingList.empty();
                if (currentOrders.preparing.length === 0) {
                    preparingList.html('<div class="text-center py-5 text-muted">No orders in preparation.</div>');
                } else {
                    currentOrders.preparing.forEach(order => {
                        preparingList.append(createOrderCard(order, 'preparing'));
                    });
                }
                
                // --- Render Ready Orders ---
                readyList.empty();
                if (currentOrders.ready.length === 0) {
                    readyList.html('<div class="text-center py-5 text-muted">No orders are ready for pickup.</div>');
                } else {
                    currentOrders.ready.forEach(order => {
                        readyList.append(createOrderCard(order, 'ready'));
                    });
                }
                
                // Update counts
                $('#preparing-count').text(currentOrders.preparing.length);
                $('#ready-count').text(currentOrders.ready.length);
                updateTimers(); // Refresh all timers
            },
            error: function(xhr, status, error) {
                console.error("Failed to fetch orders: ", error);
            }
        });
    }

    function createOrderCard(order, status) {
        let itemsHtml = '<ul class="list-unstyled small mt-1 mb-0">';
        let items;
        try {
            items = typeof order.items === 'string' ? JSON.parse(order.items) : order.items;
        } catch (e) { items = []; }

        if (Array.isArray(items)) {
             items.forEach(item => {
                itemsHtml += `<li>• ${item.quantity} x ${item.name}</li>`;
            });
        } else if (typeof items === 'object' && items !== null) {
            for (const [name, qty] of Object.entries(items)) {
                itemsHtml += `<li>• ${qty} x ${name}</li>`;
            }
        }
        itemsHtml += '</ul>';

        let cardHtml = `
            <div class="card mb-3 order-card" data-order-id="${order.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-0">Order #${order.order_id}</h6>
                        <span class="badge ${status === 'preparing' ? 'bg-warning text-dark' : 'bg-success'}">${status === 'preparing' ? 'Preparing' : 'Ready'}</span>
                    </div>
                    <p class="card-text mb-1">
                        <strong>Customer:</strong> ${order.customer_name}
                    </p>
                    <div class="mt-2">
                        <strong>Items:</strong>
                        ${itemsHtml}
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <div class="d-flex flex-column">
                            <strong class="text-danger fs-6">Total: ₹${order.total_price}</strong>`;
        
        if (status === 'preparing') {
            cardHtml += `<small class="text-muted fw-bold">
                            <span class="order-timer" data-time="${order.created_at}">00:00:00</span>
                         </small>`;
        } else { // 'ready' status
            // Use the data-time attribute for the 'Ready' timer
            cardHtml += `<small class="text-primary fw-bold">
                            <span class="order-timer" data-time="${order.ready_time}">00:00:00</span>
                         </small>`;
        }

        cardHtml += `</div>`; // Close timer column
        
        if (status === 'preparing') {
            cardHtml += `<button class="btn btn-success btn-sm mark-ready" data-order-pk="${order.id}">Mark as Ready</button>`;
        } else {
            cardHtml += `<button class="btn btn-primary btn-sm mark-pickedup" data-order-pk="${order.id}">Mark Picked Up</button>`;
        }

        cardHtml += `</div></div></div>`;
        return cardHtml;
    }

    function updateTimers() {
        $('.order-timer').each(function() {
            const timeStr = $(this).data('time');

            // --- THIS IS THE FIX ---
            // If timeStr is null, undefined, or the string "null", stop.
            if (!timeStr || timeStr === "null") {
                $(this).text('00:00:00'); // Show a default time
                return; // Skip this timer
            }
            // --- END FIX ---

            const orderTime = new Date(timeStr);
            if (isNaN(orderTime)) {
                // Handle Invalid Date
                $(this).text('--:--:--');
                return;
            }

            const now = new Date();
            let diff = now - orderTime;

            // Handle clock skew (browser time behind server time)
            if (diff < 0) { diff = 0; }

            let totalSeconds = Math.floor(diff / 1000);
            let hours = Math.floor(totalSeconds / 3600);
            totalSeconds %= 3600;
            let minutes = Math.floor(totalSeconds / 60);
            let seconds = totalSeconds % 60;

            $(this).text(
                `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
            );
        });
    }

    // --- BUTTON CLICK HANDLERS ---
    $(document).on('click', '.mark-ready, .mark-pickedup', function() {
        const orderPk = $(this).data('order-pk');
        const isReadyButton = $(this).hasClass('mark-ready');
        const newStatus = isReadyButton ? 'ready' : 'pickedup';
        const card = $(this).closest('.order-card');

        // Optimistic UI update
        card.fadeOut(300, function() {
            if (isReadyButton) {
                // Move from Preparing to Ready
                $('#ready-orders-list').prepend(card);
                // Update card content
                card.find('.badge').removeClass('bg-warning text-dark').addClass('bg-success').text('Ready');
                card.find('.mark-ready').removeClass('mark-ready btn-success').addClass('mark-pickedup btn-primary').text('Mark Picked Up');
                // The timer will be updated on the next fetch
            } else {
                // Move from Ready to Picked Up (remove from board)
                card.remove();
            }
            card.fadeIn(300);
            // Update counts
            $('#preparing-count').text($('#preparing-orders-list .order-card').length);
            $('#ready-count').text($('#ready-orders-list .order-card').length);
        });

        // Send update to server
        $.ajax({
            url: '/api/update-order-status',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ order_id: orderPk, status: newStatus }),
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                if (!response.success) {
                    alert('Error updating order: ' + response.error);
                    fetchOrders(); // Force refresh on error
                }
                // On success, do nothing (optimistic update handled)
            },
            error: function(xhr) {
                alert('Server error. Please try again.');
                fetchOrders(); // Force refresh on error
            }
        });
    });

    // --- INITIALIZE ---
    fetchOrders(); // Initial load
    setInterval(fetchOrders, 10000); // Refresh every 10 seconds
    setInterval(updateTimers, 1000); // Update timers every second
});
