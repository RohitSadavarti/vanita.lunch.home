// OrderMaster/static/js/firebase-init.js

(function() {
    // Your web app's Firebase configuration
    const firebaseConfig = {
      apiKey: "AIzaSyBnYYq_K3TL9MxyKaCNPkB8SRqAIucF0rI",
      authDomain: "vanita-lunch-home.firebaseapp.com",
      projectId: "vanita-lunch-home",
      storageBucket: "vanita-lunch-home.appspot.com",
      messagingSenderId: "86193565341",
      appId: "1:86193565341:web:b9c234bda59b37ee366e74"
    };

    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    // --- Helper function to get CSRF token ---
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

    // --- Helper function to send the token to your server ---
    function subscribeTokenToTopic(token) {
        console.log('📤 Attempting to subscribe token to topic...');
        
        fetch('/api/subscribe-topic/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ token: token })
        })
        .then(response => {
            console.log('📥 Response status:', response.status);
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('✅ Successfully subscribed to new_orders topic');
            } else {
                console.error('❌ Failed to subscribe to topic:', data.error);
            }
        })
        .catch(error => {
            console.error('❌ Network error subscribing to topic:', error);
        });
    }

    // --- Main function to initialize notifications ---
    async function initializeFirebaseMessaging() {
        try {
            // 1. Ask for permission first.
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                console.log('❌ Notification permission not granted.');
                return;
            }
            console.log('✅ Notification permission granted.');

            // 2. Wait for the Service Worker to be fully ready and active.
            const registration = await navigator.serviceWorker.ready;
            console.log('✅ Service Worker is active and ready:', registration);

            // 3. Now that the service worker is active, get the token.
            const currentToken = await messaging.getToken({ 
                vapidKey: 'BKjH1TPFhqWc4b0ClYHjgp7maojaR8TD1FnsI7eZCRGSPWul3aNtMs4Gd9wvER8Vlcs65I5jGDhFHzLN9DAxBqA',
                serviceWorkerRegistration: registration 
            });
            
            if (currentToken) {
                console.log('✅ FCM Token retrieved:', currentToken);
                subscribeTokenToTopic(currentToken);
            } else {
                console.warn('⚠️ Could not get FCM token. Is the VAPID key set?');
            }
        } catch (err) {
            console.error('❌ An error occurred during Firebase Messaging setup:', err);
        }
    }

    // --- Listen for foreground messages ---
    messaging.onMessage((payload) => {
        console.log('📬 Foreground message received:', payload);
        console.log('📦 Message data:', payload.data);

        // Make this function globally available
        if (window.handleNewOrderNotification) {
            window.handleNewOrderNotification(payload.data);
        } else {
            console.error('❌ ERROR: The popup handler function is not available.');
            // Fallback: show browser notification
            if (payload.notification) {
                new Notification(payload.notification.title, {
                    body: payload.notification.body,
                    icon: '/static/favicon.ico'
                });
            }
        }
    });
    
    // --- Start the initialization process ---
    initializeFirebaseMessaging();

})();
