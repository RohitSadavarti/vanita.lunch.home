document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons if the library is present
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // --- MENU ITEM EDITING LOGIC ---
    const editSidebar = document.getElementById('editSidebar');
    const closeEditBtn = document.getElementById('closeEditBtn');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const editForm = document.getElementById('editForm');
    const editButtons = document.querySelectorAll('.edit-btn');

    const openEditSidebar = () => {
        if (editSidebar) editSidebar.classList.add('open');
        if (sidebarOverlay) sidebarOverlay.classList.add('open');
    };

    const closeEditSidebar = () => {
        if (editSidebar) editSidebar.classList.remove('open');
        if (sidebarOverlay) sidebarOverlay.classList.remove('open');
    };
    
    const populateSelect = (selectElement, choices, selectedValue) => {
        if (!selectElement) return;
        selectElement.innerHTML = '';
        for (const [value, display] of Object.entries(choices)) {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = display;
            if (value === selectedValue) {
                option.selected = true;
            }
            selectElement.appendChild(option);
        }
    };

    editButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const itemId = button.dataset.itemId;
            try {
                const response = await fetch(`/api/menu-item/${itemId}/`);
                if (!response.ok) throw new Error('Failed to fetch item details.');
                
                const item = await response.json();

                // Populate form
                document.getElementById('edit-item_name').value = item.item_name;
                document.getElementById('edit-description').value = item.description;
                document.getElementById('edit-price').value = item.price;
                document.getElementById('edit-availability_time').value = item.availability_time;

                const categoryChoices = {'breakfast': 'Breakfast', 'lunch': 'Lunch', 'thali': 'Thali', 'main_course': 'Main Course', 'bread': 'Bread', 'dessert_beverage': 'Dessert & Beverage'};
                const vegChoices = {'veg': 'Vegetarian', 'non_veg': 'Non-Vegetarian', 'beverage': 'Beverage'};
                const mealTypeChoices = {'regular': 'Regular', 'dessert': 'Dessert', 'thali': 'Thali', 'beverage': 'Beverage'};
                
                populateSelect(document.getElementById('edit-category'), categoryChoices, item.category);
                populateSelect(document.getElementById('edit-veg_nonveg'), vegChoices, item.veg_nonveg);
                populateSelect(document.getElementById('edit-meal_type'), mealTypeChoices, item.meal_type);

                const currentImage = document.getElementById('current-image');
                if (item.image_url) {
                    currentImage.src = item.image_url;
                    currentImage.style.display = 'block';
                } else {
                    currentImage.style.display = 'none';
                }

                editForm.action = `/api/menu-item/${itemId}/`;
                openEditSidebar();

            } catch (error) {
                console.error('Error fetching menu item:', error);
                alert('Could not load item details.');
            }
        });
    });

    if (closeEditBtn) closeEditBtn.addEventListener('click', closeEditSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeEditSidebar);

    if (editForm) {
        editForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(editForm);
            try {
                const response = await fetch(editForm.action, { method: 'POST', body: formData });
                if (response.ok) {
                    window.location.reload();
                } else {
                    const errorData = await response.json();
                    alert(`Error: ${errorData.error || 'Could not update item.'}`);
                }
            } catch (error) {
                console.error('Form submission error:', error);
                alert('An error occurred while saving.');
            }
        });
    }

    // --- ORDER MANAGEMENT LOGIC ---
    const handleStatusUpdate = async (orderCard, newStatus) => {
        const orderId = orderCard.dataset.orderId;
        
        // This function is needed for POST requests to Django
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
        }

        try {
            const response = await fetch('/api/update-order-status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') // Django requires a CSRF token
                },
                body: JSON.stringify({ id: orderId, status: newStatus })
            });

            if (response.ok) {
                orderCard.style.transition = 'opacity 0.5s ease';
                orderCard.style.opacity = '0';
                setTimeout(() => {
                    orderCard.remove();
                    // Optional: You could also reload the page here if you prefer
                    // window.location.reload(); 
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

    // Attach event listeners to new buttons
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
