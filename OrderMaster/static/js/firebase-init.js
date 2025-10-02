// OrderMaster/static/js/firebase-init.js

(function() {
    // IMPORTANT: Replace this with your actual Firebase config
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

    // Request permission to show notifications
    Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
            console.log('Notification permission granted.');
            return messaging.getToken();
        }
    }).then(token => {
        if (token) {
            // Send this token to your Django backend to subscribe it to the 'new_orders' topic
            subscribeTokenToTopic(token, 'new_orders');
        }
    }).catch(err => {
        console.error('Unable to get permission to notify.', err);
    });

    // This is the crucial part for the live popup
    messaging.onMessage((payload) => {
        console.log('Message received in foreground. ', payload);

        // The 'handleNewOrderNotification' function will be defined in persistent-popup.js
        if (window.handleNewOrderNotification) {
            window.handleNewOrderNotification(payload.data);
        }
    });

    function subscribeTokenToTopic(token, topic) {
        // This function sends the token to your backend
        fetch('/api/subscribe-topic/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Function to get CSRF token
            },
            body: JSON.stringify({ token: token, topic: topic })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Successfully subscribed to topic:', topic);
            } else {
                console.error('Failed to subscribe to topic.');
            }
        });
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
