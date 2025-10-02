// OrderMaster/static/js/firebase-init.js

// Updated OrderMaster/static/js/firebase-init.js

(function() {
    // Your web app's Firebase configuration
    const firebaseConfig = {
      apiKey: "AIzaSyBnYYq_K3TL9MxyKaCNPkB8SRqAIucF0rI",
      authDomain: "vanita-lunch-home.firebaseapp.com",
      projectId: "vanita-lunch-home",
      storageBucket: "vanita-lunch-home.firebasestorage.app",
      messagingSenderId: "86193565341",
      appId: "1:86193565341:web:b9c234bda59b37ee366e74"
    };

    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    // Request notification permission
    Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
            console.log('Notification permission granted.');
            // Get token
            messaging.getToken().then((currentToken) => {
                if (currentToken) {
                    // Send the token to your server and subscribe to the topic
                    subscribeTokenToTopic(currentToken, 'new_orders');
                } else {
                    console.log('No registration token available. Request permission to generate one.');
                }
            }).catch((err) => {
                console.log('An error occurred while retrieving token. ', err);
            });
        } else {
            console.log('Unable to get permission to notify.');
        }
    });

    // Handle incoming messages when app is in foreground
    messaging.onMessage((payload) => {
        console.log('Message received. ', payload);
        
        // Extract order data from payload
        const orderData = {
            id: parseInt(payload.data.id),
            order_id: payload.data.order_id,
            customer_name: payload.data.customer_name,
            customer_mobile: payload.data.customer_mobile || 'N/A',
            total_price: parseFloat(payload.data.total_price),
            items: JSON.parse(payload.data.items),
            created_at: new Date().toLocaleString()
        };

        // Show browser notification
        if (Notification.permission === 'granted') {
            const notification = new Notification(payload.notification.title, {
                body: payload.notification.body,
                icon: '/static/favicon.ico',
                tag: 'order-' + orderData.order_id,
                requireInteraction: true
            });

            notification.onclick = function() {
                window.focus();
                notification.close();
            };
        }

        // Add to popup queue
        if (typeof window.handleNewOrderNotification === 'function') {
            window.handleNewOrderNotification(orderData);
        } else {
            console.error('handleNewOrderNotification function not found');
        }
    });

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
})();
