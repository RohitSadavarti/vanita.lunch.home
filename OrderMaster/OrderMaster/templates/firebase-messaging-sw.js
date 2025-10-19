// OrderMaster/OrderMaster/templates/OrderMaster/firebase-messaging-sw.js

importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-messaging.js');

// IMPORTANT: Replace this with your actual Firebase config from the console
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

// This handler is for notifications received when the app is in the background
messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message: ', payload);

  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/static/favicon.ico' // Ensure you have a favicon at this path
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
