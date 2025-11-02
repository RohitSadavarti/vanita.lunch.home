// OrderMaster/static/js/persistent-popup.js

(function() {
    'use strict';

    // This function is called by firebase-init.js when a message is received
    window.handleNewOrderNotification = function(orderData) {
        console.log('📱 New order notification received:', orderData);
        
        // Check for 'order_source' which is sent from views.py
        // 'customer' orders with 'pending' status will trigger page reload to show modal
        if (orderData.order_source && 
            orderData.order_source.toLowerCase() === 'customer' && 
            orderData.status === 'pending') {
            
            console.log('🔔 New customer order requires action - reloading page');
            
            // Show a brief notification before reload
            showBriefNotification(`New order #${orderData.order_id} from ${orderData.customer_name}`);
            
            // Reload the page after a brief delay to show the blocking modal
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            console.log('ℹ️ Order notification ignored (not a pending customer order)');
        }
    };

    function showBriefNotification(message) {
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            z-index: 10000;
            font-weight: 600;
            animation: slideIn 0.3s ease-out;
        `;
        toast.innerHTML = `
            <i class="fas fa-bell me-2"></i>
            ${message}
        `;
        
        // Add animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(toast);
        
        // Remove after 1 second
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(400px)';
            setTimeout(() => toast.remove(), 300);
        }, 700);
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
