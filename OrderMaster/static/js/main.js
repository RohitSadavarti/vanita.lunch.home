document.addEventListener('DOMContentLoaded', function() {
    // Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Sidebar elements
    const editSidebar = document.getElementById('editSidebar');
    const closeEditBtn = document.getElementById('closeEditBtn');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const editForm = document.getElementById('editForm');
    const editButtons = document.querySelectorAll('.edit-btn');

    // Function to open the sidebar
    const openSidebar = () => {
        editSidebar.classList.add('open');
        sidebarOverlay.classList.add('open');
    };

    // Function to close the sidebar
    const closeSidebar = () => {
        editSidebar.classList.remove('open');
        sidebarOverlay.classList.remove('open');
    };

    // Populate select options
    const populateSelect = (selectElement, choices) => {
        selectElement.innerHTML = '';
        for (const [value, display] of Object.entries(choices)) {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = display;
            selectElement.appendChild(option);
        }
    };

    // Attach event listeners to all edit buttons
    editButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const itemId = button.dataset.itemId;
            
            // Fetch item data from the new API endpoint
            try {
                const response = await fetch(`/api/menu-item/${itemId}/`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const item = await response.json();

                // Populate the form fields in the sidebar
                document.getElementById('edit-item-id').value = item.id;
                document.getElementById('edit-item_name').value = item.item_name;
                document.getElementById('edit-description').value = item.description;
                document.getElementById('edit-price').value = item.price;
                document.getElementById('edit-availability_time').value = item.availability_time;

                // Populate and set selected options for dropdowns
                // Note: You might need to pass the choices from your Django view to the template
                const categorySelect = document.getElementById('edit-category');
                const vegSelect = document.getElementById('edit-veg_nonveg');
                const mealTypeSelect = document.getElementById('edit-meal_type');

                // Assuming you have access to choices (e.g., from a global JS variable set in the template)
                // For demonstration, I'll use placeholders. Replace these with actual choices.
                const categoryChoices = {'breakfast': 'Breakfast', 'lunch': 'Lunch', 'dinner': 'Dinner', 'snacks': 'Snacks', 'beverages': 'Beverages'};
                const vegChoices = {'veg': 'Vegetarian', 'non_veg': 'Non-Vegetarian'};
                const mealTypeChoices = {'main_course': 'Main Course', 'starter': 'Starter', 'dessert': 'Dessert', 'beverage': 'Beverage'};
                
                populateSelect(categorySelect, categoryChoices);
                populateSelect(vegSelect, vegChoices);
                populateSelect(mealTypeSelect, mealTypeChoices);
                
                categorySelect.value = item.category;
                vegSelect.value = item.veg_nonveg;
                mealTypeSelect.value = item.meal_type;

                // Display the current image
                const currentImage = document.getElementById('current-image');
                if (item.image_url) {
                    currentImage.src = item.image_url;
                    currentImage.style.display = 'block';
                } else {
                    currentImage.style.display = 'none';
                }

                // Set the form's action URL
                editForm.action = `/api/menu-item/${itemId}/`;

                // Open the sidebar
                openSidebar();

            } catch (error) {
                console.error('Failed to fetch menu item:', error);
                alert('Could not load item details. Please try again.');
            }
        });
    });

    // Event listener for the close button
    if (closeEditBtn) {
        closeEditBtn.addEventListener('click', closeSidebar);
    }

    // Event listener for the overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // Handle form submission
    if (editForm) {
        editForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(editForm);
            const actionUrl = editForm.action;

            try {
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        // CSRF token is already in the form data
                    },
                });

                if (response.ok) {
                    // Reload the page to see changes
                    window.location.reload();
                } else {
                    const errorData = await response.json();
                    alert(`Error: ${errorData.error || 'Could not update item.'}`);
                }
            } catch (error) {
                console.error('Failed to submit form:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }
});
