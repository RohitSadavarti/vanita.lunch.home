// OrderMaster/static/js/firebase-init.js

// OrderMaster/static/js/firebase-init.js

(function() {
    const firebaseConfig = {
        apiKey: "AIzaSyBnYYq_K3TL9MxyKaCNPkB8SRqAIucF0rI",
        authDomain: "vanita-lunch-home.firebaseapp.com",
        projectId: "vanita-lunch-home",
        storageBucket: "vanita-lunch-home.appspot.com",
        messagingSenderId: "86193565341",
        appId: "1:86193565341:web:b9c234bda59b37ee366e74"
    };

    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    function requestNotificationPermission() {
        Notification.requestPermission().then((permission) => {
            if (permission === 'granted') {
                console.log('Notification permission granted.');
                getAndSendToken();
            } else {
                console.log('Unable to get permission to notify.');
            }
        });
    }

    function getAndSendToken() {
        messaging.getToken().then((currentToken) => {
            if (currentToken) {
                sendTokenToServer(currentToken);
            } else {
                console.log('No registration token available. Request permission to generate one.');
            }
        }).catch((err) => {
            console.log('An error occurred while retrieving token. ', err);
        });
    }

    function sendTokenToServer(token) {
        // This function would send the token to your server to subscribe to topics
        // For now, we'll just log it. You should have a view/API endpoint for this.
        console.log('FCM Token:', token);
        // Example of what you'd do:
        // fetch('/api/subscribe-to-topic/', {
        //     method: 'POST',
        //     body: JSON.stringify({ token: token, topic: 'new_orders' }),
        //     headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') }
        // });
    }
    
    // Listen for messages when the page is in the foreground
    messaging.onMessage((payload) => {
        console.log('Message received in foreground. ', payload);

        // Play the notification sound
        const sound = document.getElementById('notificationSound');
        if (sound) {
            sound.play().catch(e => console.error("Error playing sound:", e));
        }

        // Show the custom modal pop-up
        if (typeof showNewOrderPopup === "function") {
            showNewOrderPopup(payload.data);
        } else {
            console.error('showNewOrderPopup function not found!');
        }
    });

    requestNotificationPermission();

})();
   
    

 
    

    // Subscribe token to topic
    function subscribeTokenToTopic(token, topic) {
        fetch('/api/subscribe-topic/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ token: token, topic: topic })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Successfully subscribed to topic:', topic);
            } else {
                console.error('Failed to subscribe to topic:', data.error);
            }
        })
        .catch(error => {
            console.error('Error subscribing to topic:', error);
        });
    }

    // Request notification permission
    Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
            console.log('Notification permission granted.');
            messaging.getToken().then((currentToken) => {
                if (currentToken) {
                    console.log('FCM Token:', currentToken);
                    subscribeTokenToTopic(currentToken, 'new_orders');
                } else {
                    console.log('No registration token available.');
                }
            }).catch((err) => {
                console.log('Error retrieving token: ', err);
            });
        } else {
            console.log('Unable to get permission to notify.');
        }
    });

    // Handle incoming messages when page is in foreground
    messaging.onMessage((payload) => {
        console.log('Message received: ', payload);
        
        // Show the popup with order details
        showNewOrderPopup(payload.data);

        // Also show a browser notification
        if (Notification.permission === 'granted') {
            new Notification(payload.notification.title, {
                body: payload.notification.body,
                icon: '/static/favicon.ico',
                tag: 'new-order',
                requireInteraction: true
            });
        }

        // Play notification sound
        playNotificationSound();
    });

    // Function to show the new order popup
    window.showNewOrderPopup = function(orderData) {
        console.log('Showing popup for order:', orderData);
        
        const modalElement = document.getElementById('newOrderModal');
        if (!modalElement) {
            console.error('Modal element not found');
            return;
        }

        const modal = new bootstrap.Modal(modalElement);
        const detailsContainer = document.getElementById('newOrderDetails');
        
        // Parse the items if they are in string format
        let items;
        try {
            items = typeof orderData.items === 'string' ? JSON.parse(orderData.items) : orderData.items;
        } catch (e) {
            console.error('Error parsing items:', e);
            items = orderData.items || [];
        }

        let itemsHtml = '<ul class="list-unstyled">';
        if (Array.isArray(items)) {
            items.forEach(item => {
                itemsHtml += `<li class="mb-1"><i class="bi bi-dot"></i> ${item.quantity} x ${item.name}</li>`;
            });
        }
        itemsHtml += '</ul>';

        detailsContainer.innerHTML = `
            <div class="order-details">
                <div class="row mb-3">
                    <div class="col-6">
                        <p class="mb-1"><strong>Order ID:</strong></p>
                        <p class="text-primary">#${orderData.order_id}</p>
                    </div>
                    <div class="col-6 text-end">
                        <p class="mb-1"><strong>Total:</strong></p>
                        <p class="text-success fs-5">₹${orderData.total_price}</p>
                    </div>
                </div>
                <div class="mb-3">
                    <p class="mb-1"><strong>Customer:</strong></p>
                    <p>${orderData.customer_name}</p>
                </div>
                <div class="mb-3">
                    <p class="mb-1"><strong>Items:</strong></p>
                    ${itemsHtml}
                </div>
            </div>
        `;

        // Get buttons and add event listeners
        const acceptBtn = document.getElementById('acceptOrderBtn');
        const rejectBtn = document.getElementById('rejectOrderBtn');

        if (acceptBtn && rejectBtn) {
            // Clone and replace to remove old listeners
            const newAcceptBtn = acceptBtn.cloneNode(true);
            const newRejectBtn = rejectBtn.cloneNode(true);
            acceptBtn.parentNode.replaceChild(newAcceptBtn, acceptBtn);
            rejectBtn.parentNode.replaceChild(newRejectBtn, rejectBtn);

            // Add new event listeners
            newAcceptBtn.onclick = () => handleOrderAction(orderData.id, 'accept', modal);
            newRejectBtn.onclick = () => handleOrderAction(orderData.id, 'reject', modal);
        }

        // Show the modal
        modal.show();
    };

    // Function to handle order accept/reject actions
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

            const result = await response.json();

            if (response.ok && result.success) {
                modalInstance.hide();
                showToastNotification(`Order has been ${action}ed successfully!`, 'success');
                
                // Refresh the page after a short delay
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                throw new Error(result.error || `Failed to ${action} the order.`);
            }
        } catch (error) {
            console.error(`Error ${action}ing order:`, error);
            showToastNotification(`Failed to ${action} order: ${error.message}`, 'error');
        }
    }

    // Function to show toast notifications
    function showToastNotification(message, type = 'success') {
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '11';
            document.body.appendChild(toastContainer);
        }

        const toastId = 'toast-' + Date.now();
        const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // Function to play notification sound
    function playNotificationSound() {
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIGGS57OihUxILTqvj7btvIgU2k9r0yH0vBSF1xe3akEIJE1yx6OyrWBIJRp7h8r9xJAQogM3y2Ik2Bxdhue3poVISC06s4+27biMFNpPa9Mh+MAUgdcXt2pBCCRNcsenrq1gSCUae4fK/cSQFKIDN8tiJNggXYbnt6aFSEgtOrOPtu24jBTaT2vTIfjAFIHXF7dqQQgkTXLHp66tYEglGnuHyv3ElBSiAzfLYiTYIF2G57emhUhILTqzj7btuIwU2k9r0yH4wBSB1xe3akEIJE1yx6eurWBIJRp7h8r9xJAUogM3y2Ik2CBdhue3poVISC06s4+27biMFNpPa9Mh+MAUgdcXt2pBCCRNcsenrq1gSCUae4fK/cSQFKIDN8tiJNggXYbnt6aFSEgtOrOPtu24jBTaT2vTIfjAFIHXF7dqQQgkTXLHp66tYEglGnuHyv3ElBSiAzfLYiTYIF2G57emhUhILTqzj7btuIwU2k9r0yH4wBSB1xe3akEIJE1yx6eurWBIJRp7h8r9xJAUogM3y2Ik2CBdhue3poVISC06s4+27biMFNpPa9Mh+MAUgdcXt2pBCCRNcsenrq1gSCUae4fK/cSQFKIDN8tiJNggXYbnt6aFSEgtOrOPtu24jBTaT2vTIfjAFIHXF7dqQQgkTXLHp66tYEglGnuHyv3ElBSiAzfLYiTYIF2G57emhUhILTqzj7btuIwU2k9r0yH4wBSB1xe3akEIJE1yx6eurWBIJRp7h8r9xJAUogM3y2Ik2CBdhue3poVISC06s4+27biMFNpPa9Mh+MAUgdcXt2pBCCRNcsenrq1gSCUae4fK/cSQFKIDN8tiJNggXYbnt6aFSEgtOrOPtu24jBTaT2vTIfjAFIHXF7dqQQgkTXLHp66tYEglGnuHyv3ElBSiAzfLYiTYIF2G57emhUhILTqzj7btuIwU2k9r0yH4wBSB1xe3akEIJE1yx6eurWBIJRp7h8r9xJAUogM3y2Ik2CBdhue3poVISC06s4+27biMFNpPa9Mh+MAUgdcXt2pBCCRNcsenrq1gSCUae4fK/cSQFKIDN8tiJNggXYbnt6aFSEgtOrOPtu24jBTaT2vTIfjAFIHXF7dqQQgkTXLHp66tYEglGnuHyv3ElBSiAzfLYiTYIF2G57emhUhILTqzj7btuIwU2k9r0yH4wBSB1xe3akEIJE1yx6eurWBIJRp7h8r9xJAUogM3y2Ik2CBdhue3poVISC06s4+27biMFNpPa9Mh+MAUgdcXt2pBCCRNcsenrq1gSCUae4fK/cSQFKIDN8tiJNggXYbnt6aFSEgtOrOPtu24jBTaT2vTIfjAFIHXF7dqQQgkTXLHp66tYEglGnuHyv3ElBSiAzfLYiTYIF2G57emhUhILTqzj7btuIwU2k9r0yH4wBSB1xe3akEIJE1yx6eurWBIJRp7h8r9xJAUogM3y2Ik2CBdhue3poVISC06s4+27biMFNpPa9Mh+MAUgdcXt2pBCCRNcsenrq1gSCUae4fK/cSQFKIDN8tiJNggXYbnt6aFSEgtOrOPtu24jBTaT2vTIfjAFIHXF7dqQ==');
            audio.volume = 0.3;
            audio.play().catch(e => console.log('Could not play notification sound:', e));
        } catch (e) {
            console.log('Error playing notification sound:', e);
        }
    }
})();
