if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker');

        if (!('PushManager' in window)) {
            console.error("Push messaging not supported");
            return;
        }

        document.querySelector('#subscribe').addEventListener('click', async () => {
            console.log("Requesting notification permission")
            const permission = await Notification.requestPermission();
            console.log(permission);
            if (permission !== 'granted') return;
            console.log("Permission granted")
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: '{VAPID_PUBLIC_KEY}'
            });
            console.log(subscription);
            fetch("{BASE_URL}/notification/register",
                {
                    method: "POST",
                    body: JSON
                        .stringify
                        ({
                            subscription: subscription.toJSON(),
                        }),
                    headers: {
                        "Content-type": "application/json",
                    },
                })
                .then((response) => response.json())
                .then((json) => console.log(json));
        });
    });
}