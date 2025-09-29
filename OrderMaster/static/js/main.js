document.addEventListener('DOMContentLoaded', function() {
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
    // 1. Collapse/Expand Section Logic
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(button => {
        const icon = button.querySelector('i');
        const collapseEl = document.getElementById(button.getAttribute('data-bs-target').substring(1));
        
        collapseEl.addEventListener('show.bs.collapse', () => {
            icon.setAttribute('data-lucide', 'chevron-up');
            lucide.createIcons();
        });
        collapseEl.addEventListener('hide.bs.collapse', () => {
            icon.setAttribute('data-lucide', 'chevron-down');
            lucide.createIcons();
        });
    });

    // 2. Date Filter Logic
    const customDateBtn = document.getElementById('customDateBtn');
    const customDateRangeDiv = document.getElementById('customDateRange');
    if (customDateBtn && customDateRangeDiv) {
        flatpickr("#startDate", { dateFormat: "Y-m-d" });
        flatpickr("#endDate", { dateFormat: "Y-m-d" });

        customDateBtn.addEventListener('click', (e) => {
            e.preventDefault();
            customDateRangeDiv.classList.toggle('d-none');
        });
    }

    // 3. Order Status Update Logic
    const handleStatusUpdate = async (orderCard, newStatus) => {
        if (!orderCard) {
            console.error('Could not find the parent order card element.');
            return;
        }
        const orderId = orderCard.dataset.orderId;
        try {
            const response = await fetch('/api/update-order-status/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ id: orderId, status: newStatus })
            });
            if (response.ok) {
                orderCard.style.transition = 'opacity 0.5s ease';
                orderCard.style.opacity = '0';
                setTimeout(() => window.location.reload(), 500);
            } else {
                alert('Error updating status.');
            }
        } catch (error) {
            console.error('Failed to update order status:', error);
            alert('An error occurred. Please check the console for details.');
        }
    };

    // --- FIX: Corrected the selector from '.order-card' to '.card' ---
    document.querySelectorAll('.mark-ready-btn').forEach(button => {
        button.addEventListener('click', (e) => handleStatusUpdate(e.target.closest('.card[data-order-id]'), 'ready'));
    });
    document.querySelectorAll('.mark-pickedup-btn').forEach(button => {
        button.addEventListener('click', (e) => handleStatusUpdate(e.target.closest('.card[data-order-id]'), 'pickedup'));
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

