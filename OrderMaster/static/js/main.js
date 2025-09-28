document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons if the library is present
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // --- UTILITY FUNCTION to get CSRF token ---
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

    // --- LIVE ORDER REFRESH LOGIC (DASHBOARD) ---
    const liveOrdersContainer = document.getElementById('live-orders');
    if (liveOrdersContainer) {
        const fetchOrders = async () => {
            try {
                const response = await fetch('/api/get_orders/');
                if (!response.ok) return;
                const data = await response.json();

                const ordersHtml = data.orders.map(order => {
                    const itemsSummary = order.items.length > 0 ? `${order.items.length}: ${order.items[0].name}` : 'No items';
                    return `
                        <div class="live-order-item">
                            <p>ID(${order.order_id}), Items(${itemsSummary}), Amount(₹${order.total_price})</p>
                            <div class="status ${order.order_status}">${order.order_status}</div>
                        </div>
                    `;
                }).join('');

                liveOrdersContainer.innerHTML = ordersHtml;
            } catch (error) {
                console.error("Error fetching live orders:", error);
            }
        };

        // Fetch orders immediately and then every 10 seconds
        fetchOrders();
        setInterval(fetchOrders, 10000);
    }
    
    // --- ORDER MANAGEMENT PAGE LOGIC ---
    
    // 1. Collapse/Expand Section Logic
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(button => {
        button.addEventListener('click', function() {
            const icon = this.querySelector('i');
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            // Note: Bootstrap handles the toggling, we just handle the icon state change.
            // The state is checked *before* the toggle happens.
            if (isExpanded) {
                icon.setAttribute('data-lucide', 'chevron-down');
            } else {
                icon.setAttribute('data-lucide', 'chevron-up');
            }
            lucide.createIcons();
        });
    });

    // 2. Date Filter Logic
    const customDateBtn = document.getElementById('customDateBtn');
    const customDateRangeDiv = document.getElementById('customDateRange');

    if (customDateBtn && customDateRangeDiv) {
        // Initialize date pickers
        flatpickr("#startDate", { altInput: true, altFormat: "F j, Y", dateFormat: "Y-m-d" });
        flatpickr("#endDate", { altInput: true, altFormat: "F j, Y", dateFormat: "Y-m-d" });

        customDateBtn.addEventListener('click', (e) => {
            e.preventDefault();
            customDateRangeDiv.classList.toggle('d-none');
            customDateRangeDiv.classList.toggle('d-flex');
        });

        // If custom filter was selected on page load, show the inputs
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('date_filter') === 'custom') {
            customDateRangeDiv.classList.remove('d-none');
            customDateRangeDiv.classList.add('d-flex');
        }
    }

    // 3. Order Status Update Logic
    const handleStatusUpdate = async (orderCard, newStatus) => {
        const orderId = orderCard.dataset.orderId;
        const csrfToken = getCookie('csrftoken');

        try {
            const response = await fetch('/api/update_order_status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ id: orderId, status: newStatus })
            });

            if (response.ok) {
                orderCard.style.transition = 'opacity 0.5s ease';
                orderCard.style.opacity = '0';
                setTimeout(() => {
                    orderCard.remove();
                    // Reload the page to see updated counts and move the order if necessary
                    window.location.reload(); 
                }, 500);
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.error || 'Could not update order status.'}`);
            }
        } catch (error) {
            console.error('Failed to update order status:', error);
            alert('An error occurred. Please check the console and try again.');
        }
    };

    document.querySelectorAll('.mark-ready-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const orderCard = e.target.closest('.order-card');
            handleStatusUpdate(orderCard, 'ready');
        });
    });

    document.querySelectorAll('.mark-pickedup-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const orderCard = e.target.closest('.order-card');
            handleStatusUpdate(orderCard, 'pickedup');
        });
    });

});
