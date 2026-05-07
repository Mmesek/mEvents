MANIFEST = """
{
    "name": "Mistyczne Wydarzenia",
    "short_name": "Wydarzenia",
    "start_url": "/events/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#000000",
    "icons": [
        {"src": "/icon", "sizes": "192x192", "type": "image/svg+xml"},
        {"src": "/icon", "sizes": "512x512", "type": "image/svg+xml"}
    ]
}
"""

SERVICE_WORKER = """
const OFFLINE_VERSION = 1;
const CACHE_NAME = "offline";
const OFFLINE_URL = "/events";

self.addEventListener("install", (event) => {
	event.waitUntil(
		(async () => {
			const cache = await caches.open(CACHE_NAME);
			await cache.add(new Request(OFFLINE_URL, { cache: "reload" }));
		})()
	);
	self.skipWaiting();
});

self.addEventListener("activate", (event) => {
	event.waitUntil(
		(async () => {
			if ("navigationPreload" in self.registration) {
				await self.registration.navigationPreload.enable();
			}
		})()
	);
	self.clients.claim();
});

self.addEventListener("fetch", (event) => {
	if (event.request.mode === "navigate") {
		event.respondWith(
			(async () => {
				try {
					const preloadResponse = await event.preloadResponse;
					if (preloadResponse) {
						return preloadResponse;
					}
					const networkResponse = await fetch(event.request);
					return networkResponse;
				} catch (error) {
					const cache = await caches.open(CACHE_NAME);
					const cachedResponse = await cache.match(OFFLINE_URL);
					return cachedResponse;
				}
			})()
		);
	}
});
"""

PWA_SCRIPT = """
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker')
      .then(registration => {
        console.log('ServiceWorker registration successful with scope: ', registration.scope);
      })
      .catch(error => {
        console.log('ServiceWorker registration failed: ', error);
      });
  });
}
"""

SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="18" fill="#f97316"/>
  <!-- Ciało kalendarza -->
  <rect x="14" y="28" width="72" height="58" rx="8" fill="white"/>
  <!-- Nagłówek -->
  <rect x="14" y="28" width="72" height="22" rx="8" fill="#ea580c"/>
  <rect x="14" y="42" width="72" height="8" fill="#ea580c"/>
  <!-- Uchwyty -->
  <rect x="30" y="18" width="10" height="16" rx="5" fill="white"/>
  <rect x="60" y="18" width="10" height="16" rx="5" fill="white"/>
  <!-- Siatka dni -->
  <rect x="22" y="58" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="37" y="58" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="52" y="58" width="10" height="10" rx="3" fill="#f97316"/>
  <rect x="67" y="58" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="22" y="73" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="37" y="73" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="52" y="73" width="10" height="10" rx="3" fill="#fed7aa"/>
</svg>
"""
