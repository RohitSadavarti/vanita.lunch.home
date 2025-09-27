// JavaScript for Vanita Lunch Order Master

document.addEventListener('DOMContentLoaded', function() {
    
    // Handle order status updates
    const moveToReadyButtons = document.querySelectorAll('.move-to-ready');
    const markCompletedButtons = document.querySelectorAll('.mark-completed');
    
    moveToReadyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            updateOrderStatus(orderId, 'ready', this);
        });
    });
    
    markCompletedButtons.forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            updateOrderStatus(orderId, 'completed', this);
        });
    });
    
    function updateOrderStatus(orderId, status, button) {
        // Show loading state
        const originalText = button.textContent;
        button.textContent = 'Updating...';
        button.disabled = true;
        
        // Get CSRF token
        const csrfToken = getCookie('csrftoken');
        
        fetch('/api/update-order-status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                order_id: orderId,
                status: status
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the order card or reload the page
                const orderCard = button.closest('.order-card');
                orderCard.style.transition = 'opacity 0.3s';
                orderCard.style.opacity = '0';
                setTimeout(() => {
                    location.reload(); // Reload to update both sections
                }, 300);
            } else {
                alert('Error updating order status: ' + (data.error || 'Unknown error'));
                button.textContent = originalText;
                button.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error updating order status');
            button.textContent = originalText;
            button.disabled = false;
        });
    }
    
    // Function to get CSRF token from cookies
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
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    });
    
    // Form validation for menu items
    const menuForm = document.querySelector('form[enctype="multipart/form-data"]');
    if (menuForm) {
        menuForm.addEventListener('submit', function(e) {
            const price = document.getElementById('price').value;
            if (price <= 0) {
                e.preventDefault();
                alert('Price must be greater than 0');
                return false;
            }
        });
    }
    
});