const CACHE_NAME = '-v1';

// Fichiers à mettre en cache pour le mode hors ligne
const STATIC_ASSETS = [
  '/',
  '/static/img/logo.png',
  '/static/img/favi.ico',
  '/static/js/home.js',
  '/static/js/login.js',
  '/static/js/register.js',
];

// Installation : mise en cache des assets statiques
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activation : suppression des anciens caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Fetch : réseau d'abord, cache en fallback
self.addEventListener('fetch', event => {
  // Ignorer les requêtes POST et non-GET
  if (event.request.method !== 'GET') return;

  // Ignorer les requêtes vers des APIs externes (SumUp, Nominatim)
  const url = new URL(event.request.url);
  if (url.hostname !== location.hostname) return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Mettre en cache les réponses réussies pour les assets statiques
        if (response.ok && url.pathname.startsWith('/static/')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        // Hors ligne : retourner depuis le cache
        return caches.match(event.request).then(cached => {
          if (cached) return cached;
          // Page offline par défaut si rien en cache
          if (event.request.destination === 'document') {
            return caches.match('/');
          }
        });
      })
  );
});
