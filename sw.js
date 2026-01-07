const CACHE_NAME = 'tennis-lab-v50';
const ASSETS_TO_CACHE = [
  './',
  './tennis_betting_lab_v15_ytd_monitor.html',
  './tennis_tracker.html',
  './manifest.json',
  './manifest_tracker.json'
];

// Installation - cache les fichiers de base
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS_TO_CACHE))
  );
  self.skipWaiting();
});

// Activation - nettoie les anciens caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch - network first pour les CSV (donnees fraiches), cache first pour le reste
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // CSV = toujours chercher en ligne d'abord (donnees fraiches)
  if (url.pathname.endsWith('.csv')) {
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

  // Autres fichiers = cache first
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
