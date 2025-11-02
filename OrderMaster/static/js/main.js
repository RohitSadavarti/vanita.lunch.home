/*
This is a merged file containing all necessary JavaScript for:
1. The Admin Order Management (Kanban) Board (using jQuery)
2. The Admin Menu Management Sidebar (using modern JS)
3. The Timer fix for the Kanban board
*/

// Utility function to get CSRF token
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


// ==================================================================
// PART 1: KANBAN ORDER BOARD & TIMER LOGIC (using jQuery)
// ==================================================================
$(document).ready(function() {
    
    // Check if we are on the order management page
    if ($('#preparing-orders-list').length) {
        // Initial load
        fetchAndDisplayOrders();

        // Refresh every 10 seconds
        setInterval(fetchAndDisplayOrders, 10000);
    }

    // Start timers
    updateOrderTimers();
    setInterval(updateOrderTimers, 1000);

    // ==================================================================
    // ORDER BOARD LOGIC (Fetch and Display)
    // ==================================================================
    function fetchAndDisplayOrders() {
        $.ajax({
            url: '/api/get_orders/',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                const preparingList = $('#preparing-orders-list');
                const readyList = $('#ready-orders-list');

                preparingList.empty();
                readyList.empty();

                // Populate Preparing Orders
                if (data.preparing_orders.length === 0) {
                    preparingList.html('<div class="text-center py-4 text-muted">No orders in preparation.</div>');
                } else {
                    data.preparing_orders.forEach(order => {
                        preparingList.append(createOrderCard(order, true));
                    });
                }

                // Populate Ready Orders
                if (data.ready_orders.length === 0) {
                    readyList.html('<div class="text-center py-4 text-muted">No orders are ready.</div>');
                } else {
                    data.ready_orders.forEach(order => {
                        readyList.append(createOrderCard(order, false));
                    });
                }

                // Update counts
                $('#preparing-count').text(data.preparing_orders.length);
                $('#ready-count').text(data.ready_orders.length);

                // Re-initialize timers for any new cards
                updateOrderTimers();
            },
            error: function(xhr, status, error) {
                console.error('Failed to fetch orders:', error);
                $('#preparing-orders-list').html('<div class="text-center py-4 text-danger">Error loading orders.</div>');
            }
        });
    }

    // Function to create an HTML card for an order
    function createOrderCard(order, isPreparing) {
        let itemsHtml = '<ul class="list-unstyled small mt-1 mb-0">';
        // 'items' is expected to be a dict like {"item_name": quantity}
        for (const item_name in order.items) {
            itemsHtml += `<li>• ${order.items[item_name]}x ${item_name}</li>`;
        }
        itemsHtml += '</ul>';

        let timerHtml = isPreparing ? 
            `<small class="text-muted fw-bold">
                <span class="order-timer">00:00:00</span>
             </small>` : 
            `<small class="text-muted">Ready at ${order.ready_time_formatted}</small>`;

        let buttonHtml = isPreparing ?
            `<button class="btn btn-success btn-sm move-to-ready" data-order-pk="${order.id}">Mark as Ready</button>` :
            `<button class="btn btn-primary btn-sm mark-completed" data-order-pk="${order.id}">Complete</button>`;

        // We use the database pk (order.id) for the data-order-id for consistency
        return `
            <div class="card mb-3 order-card" data-order-id="${order.id}" data-order-time="${order.created_at_iso}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-0">Order #${order.order_id}</h6>
                        <span class="badge ${isPreparing ? 'bg-warning text-dark' : 'bg-success'}">${isPreparing ? 'Pending' : 'Ready'}</span>
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
                            <strong class="text-danger fs-6">Total: ₹${order.total_amount}</strong>
                            ${timerHtml}
                        </div>
                        ${buttonHtml}
                    </div>
                </div>
            </div>`;
    }

    // ==================================================================
    // ORDER ACTION LOGIC (Update Status)
    // ==================================================================
    $(document).on('click', '.move-to-ready, .mark-completed', function() {
        const orderPk = $(this).data('order-pk');
        const isReadyButton = $(this).hasClass('move-to-ready');
        const newStatus = isReadyButton ? 'Ready' : 'Completed';
        const card = $(this).closest('.order-card');

        // Optimistic UI update: move card immediately
        card.fadeOut(300, function() {
            if (isReadyButton) {
                // Moving from Preparing to Ready
                $('#ready-orders-list').prepend(card);
                // Update card content
                card.find('.badge').removeClass('bg-warning text-dark').addClass('bg-success').text('Ready');
                card.find('.move-to-ready').removeClass('move-to-ready btn-success').addClass('mark-completed btn-primary').text('Complete');
            } else {
                // Moving from Ready to (implicitly) Completed
                card.remove(); // Just remove it from the board
            }
            card.fadeIn(300);
            // Update counts
            $('#preparing-count').text($('#preparing-orders-list .order-card').length);
            $('#ready-count').text($('#ready-orders-list .order-card').length);
        });


        // Send update to server
        $.ajax({
            url: '/api/update_order_status/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ id: orderPk, status: newStatus }),
            headers: {
                'X-CSRFToken': getCookie('csrftoken') // Get token for security
            },
            success: function(response) {
                if (!response.success) {
                    alert('Error updating order: ' + response.error);
                    fetchAndDisplayOrders(); // Force a full refresh to fix state
                }
                // On success, do nothing - optimistic update already handled
            },
            error: function(xhr) {
                alert('Server error. Please try again.');
                fetchAndDisplayOrders(); // Force a full refresh to fix state
            }
        });
    });

    // ==================================================================
    // ORDER TIMER LOGIC (WITH FIX)
    // ==================================================================
    function updateOrderTimers() {
        $('.order-timer').each(function() {
            const orderCard = $(this).closest('.order-card');
            const orderTimeStr = orderCard.data('order-time');
            if (!orderTimeStr) {
                $(this).text('--:--:--');
                return;
            }

            const orderTime = new Date(orderTimeStr);
            const now = new Date();
            let diff = now - orderTime; // Difference in milliseconds

            // --- THIS IS THE TIMER FIX ---
            // If diff is negative (browser clock is behind server), set to 0
            if (diff < 0) {
                diff = 0;
            }
            // -----------------------------

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

});


// ==================================================================
// PART 2: MENU MANAGEMENT SIDEBAR (from your new file)
// ==================================================================
// This part runs outside of jQuery.ready, but after the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize Lucide Icons if available
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // --- MENU MANAGEMENT PAGE ---
    const editSidebar = document.getElementById('editSidebar');
    const editFormContainer = document.getElementById('editForm');
    
    if (editSidebar && editFormContainer) { // Only run if we are on the menu page
        
        document.querySelectorAll('.edit-btn').forEach(button => {
            button.addEventListener('click', async () => {
                const itemId = button.dataset.itemId;
                let response;
                try {
                    // Use the correct API URL for your app
                    response = await fetch(`/api/menu-items/${itemId}/`); 
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const item = await response.json();

                    // ** FIX: Removed {% csrf_token %} which cannot be in a .js file **
                    editFormContainer.innerHTML = `
                        <div class="mb-3">
                            <label class="form-label">Item Name</label>
                            <input type="text" class="form-control" name="name" value="${item.name || ''}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Price</label>
                            <input type="number" step="0.01" class="form-control" name="price" value="${item.price || ''}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Current Image</label>
                            <div>
                                ${item.image_url ? `<img src="${item.image_url}" alt="${item.name}" style="width: 100px; height: auto; border-radius: 8px;">` : 'No image'}
                            </div>
                            <label class="form-label mt-2">Change Image</label>
                            <input type="file" class="form-control" name="image">
                        </div>
                        
                        <div class="sidebar-footer">
                            <button type="button" class="btn btn-secondary" id="cancelEditBtn">Cancel</button>
                            <button type="submit" class="btn btn-primary">Save Changes</button>
                        </div>
                    `;
                    
                    // Set the form's action URL to the web view, not the API
                    editFormContainer.action = `/menu/edit/${item.id}/`; 
                    editSidebar.classList.add('open');
                    document.getElementById('sidebar-overlay').classList.add('open');
                
                } catch (error) {
                    console.error('Failed to fetch menu item:', error);
                    alert('Error loading item data. Please check the console.');
                }
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

        // This submit listener assumes the form is being submitted via HTML, not JS.
        // The editFormContainer.action is set to the correct Django view URL.
        // The form in menu_management.html should handle the "Add Item" part.
        // This script now only handles *populating* the edit form.
        // The form submission itself is a standard HTML form POST.
    }
    
    // NOTE: The "live-orders" and "newOrderPopup" logic from your file 
    // was removed as it conflicts with the jQuery Kanban board logic.
    // This file now handles the Kanban board and the Menu Editing sidebar.
});
