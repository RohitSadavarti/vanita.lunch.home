/*
This file contains all logic for:
1. Admin Menu Management (Add/Edit Sidebar)
2. Admin Order Management (Kanban Board & Timers)
3. New Order Popup
4. Timer Fix (NaN fix)
*/

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

// --- GLOBAL TIMER INTERVAL ---
// We define one interval that updates all timers on the page.
let timerInterval = null;

function startGlobalTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
    }
    timerInterval = setInterval(updateOrderTimers, 1000);
}

function updateOrderTimers() {
    document.querySelectorAll('.order-timer').forEach(timerSpan => {
        const startTimeStr = timerSpan.dataset.time;
        
        // If data-time is missing or invalid, stop.
        if (!startTimeStr || startTimeStr === "null") {
            timerSpan.textContent = "00:00:00";
            return;
        }

        const startTime = new Date(startTimeStr);
        if (isNaN(startTime.getTime())) {
            timerSpan.textContent = "00:00:00"; // Show 0 if date is invalid
            return;
        }

        const now = new Date();
        let diff = now - startTime; // Difference in milliseconds

        // Handle clock skew (browser time behind server)
        if (diff < 0) {
            diff = 0;
        }

        let totalSeconds = Math.floor(diff / 1000);
        let hours = Math.floor(totalSeconds / 3600);
        totalSeconds %= 3600;
        let minutes = Math.floor(totalSeconds / 60);
        let seconds = totalSeconds % 60;

        timerSpan.textContent = 
            `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    });
}

// ==================================================================
//  NEW ORDER POPUP LOGIC
// ==================================================================
let newOrdersQueue = [];
let isModalOpen = false;
let lastCheckedOrderId = 0; // Track the last order ID we've seen
let newOrderSound = new Audio('/static/audio/notification.mp3'); // Path to your sound file

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
        items = (typeof orderData.items === 'string') ? JSON.parse(orderData.items) : orderData.items;
    } catch (e) {
        items = orderData.items || {}; // Fallback to object or empty object
    }

    let itemsHtml = '<ul class="list-group list-group-flush">';
    if (Array.isArray(items)) {
         // Assuming format [{name: '...', quantity: 1, price: '...'}, ...]
         items.forEach(item => {
            itemsHtml += `<li class="list-group-item d-flex justify-content-between">
                            <span>${item.quantity} x ${item.name}</span>
                            <strong>₹${item.price}</strong>
                          </li>`;
        });
    } else if (typeof items === 'object' && items !== null) {
         // Assuming format {item_name: quantity, ...}
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
    
    const acceptBtn = document.getElementById('acceptOrderBtn');
    const rejectBtn = document.getElementById('rejectOrderBtn');

    // Use .cloneNode(true) to remove old event listeners
    const newAcceptBtn = acceptBtn.cloneNode(true);
    acceptBtn.parentNode.replaceChild(newAcceptBtn, acceptBtn);
    newAcceptBtn.addEventListener('click', () => handleOrderAction(orderData.id, 'accept', modal));

    const newRejectBtn = rejectBtn.cloneNode(true);
    rejectBtn.parentNode.replaceChild(newRejectBtn, rejectBtn);
    newRejectBtn.addEventListener('click', () => handleOrderAction(orderData.id, 'reject', modal));
    
    const modalElement = document.getElementById('newOrderModal');
    modalElement.addEventListener('hidden.bs.modal', function onModalHide() {
        isModalOpen = false;
        setTimeout(showNewOrderPopup, 500); // Check for next order
        modalElement.removeEventListener('hidden.bs.modal', onModalHide); // Clean up listener
    });

    modal.show();
    try {
        newOrderSound.play();
    } catch (e) {
        console.warn("Audio play blocked by browser.");
    }
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
            fetchAndDisplayOrders(); // Manually refresh the board
        } else {
            alert(`Failed to ${action} the order.`);
        }
    } catch (error) {
        console.error(`Error ${action}ing order:`, error);
        alert('An error occurred. Please try again.');
    }
}

// ==================================================================
//  KANBAN BOARD (Order Management)
// ==================================================================
async function fetchAndDisplayOrders() {
    const preparingList = document.getElementById('preparing-orders-list');
    const readyList = document.getElementById('ready-orders-list');
    
    if (!preparingList || !readyList) return; // Not on order management page

    try {
        const response = await fetch('/api/get-orders/');
        if (!response.ok) return;
        const data = await response.json();

        // Check for new orders
        if (data.preparing_orders.length > 0) {
            const maxId = Math.max(...data.preparing_orders.map(o => o.id));
            if (maxId > lastCheckedOrderId && lastCheckedOrderId !== 0) {
                const newOrders = data.preparing_orders.filter(o => o.id > lastCheckedOrderId);
                newOrdersQueue.push(...newOrders);
                showNewOrderPopup();
            }
            if (lastCheckedOrderId === 0 || maxId > lastCheckedOrderId) {
                lastCheckedOrderId = maxId;
            }
        }

        // --- Render Preparing Orders ---
        preparingList.innerHTML = ''; // Clear list
        if (data.preparing_orders.length === 0) {
            preparingList.innerHTML = '<div class="text-center py-5 text-muted">No orders in preparation.</div>';
        } else {
            data.preparing_orders.forEach(order => {
                preparingList.appendChild(createOrderCard(order, 'preparing'));
            });
        }
        
        // --- Render Ready Orders ---
        readyList.innerHTML = ''; // Clear list
        if (data.ready_orders.length === 0) {
            readyList.innerHTML = '<div class="text-center py-5 text-muted">No orders are ready for pickup.</div>';
        } else {
            data.ready_orders.forEach(order => {
                readyList.appendChild(createOrderCard(order, 'ready'));
            });
        }
        
        // Update counts
        document.getElementById('preparing-count').textContent = data.preparing_orders.length;
        document.getElementById('ready-count').textContent = data.ready_orders.length;
        
        startGlobalTimer(); // Ensure timers are running

    } catch (error) {
        console.error("Failed to fetch orders: ", error);
        preparingList.innerHTML = '<div class="text-center py-4 text-danger">Error loading orders.</div>';
    }
}

function createOrderCard(order, status) {
    let itemsHtml = '<ul class="list-unstyled small mt-1 mb-0">';
    let items;
    try {
        items = (typeof order.items === 'string') ? JSON.parse(order.items) : order.items;
    } catch (e) {
        items = order.items || {};
    }

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

    let timerHtml = '';
    let buttonHtml = '';
    
    if (status === 'preparing') {
        timerHtml = `<small class="text-muted fw-bold">Preparing for: 
                        <span class="order-timer" data-time="${order.created_at_iso}">00:00:00</span>
                     </small>`;
        buttonHtml = `<button class="btn btn-success btn-sm mark-ready" data-order-pk="${order.id}">Mark as Ready</button>`;
    } else { // 'ready' status
        timerHtml = `<small class="text-primary fw-bold">Ready for: 
                        <span class="order-timer" data-time="${order.ready_time_iso}">00:00:00</span>
                     </small>`;
        buttonHtml = `<button class="btn btn-primary btn-sm mark-completed" data-order-pk="${order.id}">Mark Picked Up</button>`;
    }

    const card = document.createElement('div');
    card.className = 'card mb-3 order-card';
    card.dataset.orderId = order.id; // Use DB ID for updates
    
    card.innerHTML = `
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="card-title mb-0">Order #${order.order_id}</h6>
                <span class="badge ${status === 'preparing' ? 'bg-warning text-dark' : 'bg-success'}">${status === 'preparing' ? 'Pending' : 'Ready'}</span>
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
    `;
    return card;
}

// ==================================================================
//  EVENT LISTENERS (Main DOM Content)
// ==================================================================
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize Lucide Icons if available
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // --- ORDER MANAGEMENT PAGE: KANBAN LOGIC ---
    const orderManagementPage = document.getElementById('preparing-orders-list');
    if (orderManagementPage) {
        // Initial load
        fetchAndDisplayOrders();
        // Set polling interval
        setInterval(fetchAndDisplayOrders, 10000); // Refresh every 10 seconds
        // Start timers
        startGlobalTimer();

        // Add single event listener for button clicks
        document.body.addEventListener('click', async function(event) {
            const button = event.target;
            let newStatus = null;
            
            if (button.classList.contains('mark-ready')) {
                newStatus = 'Ready';
            } else if (button.classList.contains('mark-completed')) {
                newStatus = 'Completed';
            }

            if (newStatus) {
                const card = button.closest('.order-card');
                const orderPk = card.dataset.orderId;
                
                // --- THIS IS THE NAN FIX: OPTIMISTIC UI ---
                if (newStatus === 'Ready') {
                    // 1. Move card visually
                    document.getElementById('ready-orders-list').prepend(card);
                    // 2. Update badge and button
                    card.querySelector('.badge').className = 'badge bg-success';
                    card.querySelector('.badge').textContent = 'Ready';
                    button.textContent = 'Mark Picked Up';
                    button.className = 'btn btn-primary btn-sm mark-completed';
                    // 3. Update timer
                    const timerSpan = card.querySelector('.order-timer');
                    const timerLabel = timerSpan.parentElement; // The <small> tag
                    timerLabel.className = 'text-primary fw-bold';
                    timerLabel.innerHTML = `Ready for: <span class="order-timer" data-time="${new Date().toISOString()}">00:00:00</span>`;
                    // The global timer will automatically pick this up
                } else {
                    // Just remove the card for "Completed"
                    card.style.opacity = '0';
                    setTimeout(() => card.remove(), 300);
                }
                
                // Update counts
                document.getElementById('preparing-count').textContent = document.querySelectorAll('#preparing-orders-list .order-card').length;
                document.getElementById('ready-count').textContent = document.querySelectorAll('#ready-orders-list .order-card').length;

                // 4. Send update to server in the background
                try {
                    const response = await fetch('/api/update_order_status/', {
                        method: 'POST',
                        contentType: 'application/json',
                        body: JSON.stringify({ id: orderPk, status: newStatus }),
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    });
                    const result = await response.json();
                    if (!result.success) {
                        // If server fails, force a full refresh to fix state
                        alert('Error updating order: ' + result.error);
                        fetchAndDisplayOrders(); 
                    }
                    // On success, do nothing - UI is already updated.
                } catch (error) {
                    alert('Server error. Please try again.');
                    fetchAndDisplayOrders(); // Force refresh
                }
            }
        });
    }

    // --- MENU MANAGEMENT PAGE: SIDEBAR LOGIC ---
    const editSidebar = document.getElementById('editSidebar');
    const editFormContainer = document.getElementById('editForm');
    
    if (editSidebar && editFormContainer) {
        
        document.querySelectorAll('.edit-btn').forEach(button => {
            button.addEventListener('click', async () => {
                const itemId = button.dataset.itemId;
                try {
                    const response = await fetch(`/api/menu-items/${itemId}/`);
                    if (!response.ok) throw new Error('Item not found');
                    
                    const item = await response.json();

                    // This form will POST to the HTML view, not the API
                    editFormContainer.action = `/menu/edit/${item.id}/`;
                    
                    // Populate form fields
                    editFormContainer.querySelector('input[name="name"]').value = item.name || '';
                    editFormContainer.querySelector('input[name="price"]').value = item.price || '';
                    
                    const imagePreview = editFormContainer.querySelector('#image-preview');
                    if (item.image_url) {
                        imagePreview.innerHTML = `<img src="${item.image_url}" alt="${item.name}" style="width: 100px; height: auto; border-radius: 8px;">`;
                    } else {
                        imagePreview.innerHTML = '<span>No image</span>';
                    }
                    
                    // Add other fields if they are in your form
                    // e.g., editFormContainer.querySelector('input[name="category"]').value = item.category || '';

                    editSidebar.classList.add('open');
                    document.getElementById('sidebar-overlay').classList.add('open');
                
                } catch (error) {
                    console.error('Failed to fetch menu item:', error);
                    alert('Error loading item data. Please check the console.');
                }
            });
        });

        // Close sidebar
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
                e.preventDefault(); // Prevent form submission
                editSidebar.classList.remove('open');
                document.getElementById('sidebar-overlay').classList.remove('open');
            }
        });
    }
});
