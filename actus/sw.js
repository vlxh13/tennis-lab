const CACHE_VERSION = 'v3.0';
const CACHE_NAME = 'actus-' + CACHE_VERSION;
const STATIC_ASSETS = [
    './manifest.json',
    './icon-192.png',
    './icon-512.png'
];

// Date du dernier accès (pour invalidation quotidienne)
let lastAccessDate = null;

function getTodayStr() {
    return new Date().toISOString().split('T')[0];
}

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    const today = getTodayStr();

    // Vérifier si on a changé de jour — invalider le cache des actus
    if (lastAccessDate && lastAccessDate !== today) {
        caches.open(CACHE_NAME).then(cache => {
            cache.keys().then(requests => {
                requests.forEach(req => {
                    if (req.url.includes('actu_') || req.url.includes('index.html')) {
                        cache.delete(req);
                    }
                });
            });
        });
    }
    lastAccessDate = today;

    // Pour index.html et les fichiers JSON d'actus, toujours réseau d'abord
    if (url.pathname.endsWith('index.html') || url.pathname.endsWith('/') ||
        (url.pathname.includes('actu_') && url.pathname.endsWith('.json'))) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
        return;
    }

    // Pour le reste (manifest, icônes), cache first
    event.respondWith(
        caches.match(event.request).then(cached => cached || fetch(event.request))
    );
});
