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
    if(Array.isArray(items)) {
        for (const item of items) {
            itemsHtml += `<li>${item.quantity} x ${item.name}</li>`;
        }
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
        button.addEventListener('click', (e) => {
            e.preventDefault();
            handleStatusUpdate(e.target, 'ready');
        });
    });    
    document.querySelectorAll('.mark-pickedup-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            handleStatusUpdate(e.target, 'pickedup');
        });
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

